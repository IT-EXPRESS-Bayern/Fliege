"""Audit the downloaded MaleCNS v1.0 traced graph and prepare model roles."""

from __future__ import annotations

import csv
import hashlib
import json
import pathlib

import numpy as np
import pandas as pd
import pyarrow.feather as feather


ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "malecns_v1_reference"
ANNOTATIONS = DATA / "body-annotations-male-cns-v1.0-minconf-0.5.feather"
NT = DATA / "body-neurotransmitters-male-cns-v1.0.feather"
WEIGHTS = DATA / "connectome-weights-male-cns-v1.0-minconf-0.5-traced-only.feather"
ROLES = DATA / "model_neuron_roles_v1.csv"
AUDIT = ROOT / "analysis" / "malecns_v1_reference_audit.json"


def digest(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def edge_counts(pre: np.ndarray, post: np.ndarray, weight: np.ndarray, mask: np.ndarray) -> dict:
    p = pre[mask]
    q = post[mask]
    w = weight[mask]
    return {
        "directed_pair_rows": int(mask.sum()),
        "unique_bodies": int(np.unique(np.concatenate((p, q))).size),
        "summed_synaptic_contacts": int(w.sum(dtype=np.int64)),
    }


def main() -> None:
    manifest = json.loads((DATA / "provenance.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        target = ROOT / entry["path"]
        if target.stat().st_size != entry["bytes"] or digest(target) != entry["sha256"]:
            raise ValueError(f"source provenance mismatch: {target}")

    annotations = feather.read_table(ANNOTATIONS).to_pandas()
    neurons = annotations.loc[annotations["superclass"].notna()].copy()
    assert neurons["bodyId"].is_unique
    nt = feather.read_table(NT, columns=["body", "consensus_nt", "predicted_nt_confidence"])
    nt = nt.to_pandas()
    assert nt["body"].is_unique

    roles_cols = [
        "bodyId", "superclass", "type", "group", "class", "subclass",
        "somaSide", "rootSide", "somaNeuromere", "entryNerve", "exitNerve",
        "receptorType", "flywireType", "mancType", "hemibrainType",
        "dimorphism", "fruDsx", "statusLabel",
    ]
    roles = neurons[roles_cols].merge(
        nt, left_on="bodyId", right_on="body", how="left", validate="one_to_one"
    ).drop(columns="body")
    roles.to_csv(ROLES, index=False)

    weights = feather.read_table(WEIGHTS, columns=["body_pre", "body_post", "weight"])
    pre = weights["body_pre"].to_numpy()
    post = weights["body_post"].to_numpy()
    weight = weights["weight"].to_numpy()
    neuron_ids = neurons["bodyId"].to_numpy()
    neuron_pair = np.isin(pre, neuron_ids) & np.isin(post, neuron_ids)
    thresholded = weight >= 5

    function = pd.read_csv(DATA / "dnan_cluster_function_20260509.csv")
    with (ROOT / "data" / "research_sources" / "derived" / "model_missing_fafb_ids.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        missing_fafb = list(csv.DictReader(stream))
    mapping = json.loads((DATA / "mcns_fw_edge_comp_mappings.json").read_text())
    mapped_missing = [row for row in missing_fafb if row["root_id"] in mapping]

    capture = pd.read_csv(DATA / "male-cns-v1.0-traced-synapse-capture-by-roi.csv")
    major_capture = capture.loc[capture["compartment"].eq("CNS Major Compartments")]

    result = {
        "version": "MaleCNS v1.0",
        "source_provenance": str((DATA / "provenance.json").relative_to(ROOT)).replace("\\", "/"),
        "annotations": {
            "all_annotated_body_rows_including_non_neurons": len(annotations),
            "neuron_rows_with_superclass": len(neurons),
            "distinct_nonempty_type_labels_unfiltered": int(neurons["type"].nunique()),
            "superclass_counts": {
                str(k): int(v) for k, v in neurons["superclass"].value_counts().items()
            },
            "neuron_rows_with_consensus_nt": int(roles["consensus_nt"].notna().sum()),
            "consensus_nt_counts": {
                str(k): int(v)
                for k, v in roles["consensus_nt"].fillna("missing").value_counts().items()
            },
        },
        "traced_only_weight_table": {
            "definition": "Official minconf-0.5 traced-only body-pair table; includes some bodies without neuron superclass.",
            "all_rows": edge_counts(pre, post, weight, np.ones(weight.size, dtype=bool)),
            "both_ends_annotated_neurons": edge_counts(pre, post, weight, neuron_pair),
            "all_rows_weight_at_least_5": edge_counts(pre, post, weight, thresholded),
            "both_neurons_weight_at_least_5": edge_counts(pre, post, weight, neuron_pair & thresholded),
            "traced_table_bodies_without_neuron_superclass": int(
                np.unique(np.concatenate((pre, post))).size
                - np.intersect1d(np.unique(np.concatenate((pre, post))), neuron_ids).size
            ),
        },
        "supplemental": {
            "dnan_rows": len(function),
            "dnan_distinct_bodies": int(function["bodyId"].nunique()),
            "dnan_rows_with_function": int(function["function"].notna().sum()),
            "dnan_rows_with_reference": int(function["reference"].notna().sum()),
            "dnan_duplicate_body_rows": int(function.duplicated("bodyId").sum()),
            "missing_fafb_ids": len(missing_fafb),
            "missing_fafb_ids_in_author_cross_match": len(mapped_missing),
            "missing_fafb_cross_match_type_labels": len(
                {mapping[row["root_id"]] for row in mapped_missing}
            ),
            "capture_major_compartments": major_capture.to_dict(orient="records"),
        },
        "derived": {
            "roles_csv": str(ROLES.relative_to(ROOT)).replace("\\", "/"),
            "roles_rows": len(roles),
            "roles_sha256": digest(ROLES),
        },
    }
    AUDIT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "neuron_rows": len(neurons),
        "traced_only_all": result["traced_only_weight_table"]["all_rows"],
        "traced_only_neuron_pairs": result["traced_only_weight_table"]["both_ends_annotated_neurons"],
        "roles": str(ROLES), "audit": str(AUDIT),
    }, indent=2))


if __name__ == "__main__":
    main()
