"""Project *type-level* MaleCNS partner evidence onto 616 FAFB-v783 IDs.

No MaleCNS body ID is interpreted as a FAFB root ID, and no predicted edge is
inserted into the released FAFB graph. The output is a ranked comparative
hypothesis table, not a synapse reconstruction.
"""

from __future__ import annotations

import collections
import csv
import datetime as dt
import hashlib
import json
import pathlib

import numpy as np
import pandas as pd
import pyarrow.feather as feather


ROOT = pathlib.Path(__file__).resolve().parent.parent
MALE = ROOT / "data" / "malecns_v1_reference"
DERIVED = ROOT / "data" / "research_sources" / "derived"
OUT_GROUPS = DERIVED / "malecns_observed_partner_type_groups.csv"
OUT_IDS = DERIVED / "malecns_type_partner_hypotheses_for_616.csv"
OUT_COVERAGE = DERIVED / "malecns_type_mapping_coverage_for_616.csv"
OUT_R7_CROSSCHECK = DERIVED / "malecns_r7_raw_type_crosscheck.csv"
OUT_AUDIT = ROOT / "analysis" / "malecns_type_partner_hypotheses_audit.json"
TOP_PER_DIRECTION = 10


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def verified_male_inputs() -> dict[str, dict]:
    manifest = json.loads((MALE / "provenance.json").read_text(encoding="utf-8"))
    items = {pathlib.Path(item["path"]).name: item for item in manifest["files"]}
    for name in (
        "body-annotations-male-cns-v1.0-minconf-0.5.feather",
        "connectome-weights-male-cns-v1.0-minconf-0.5-traced-only.feather",
        "mcns_fw_edge_comp_mappings.json",
    ):
        item = items[name]
        file = ROOT / item["path"]
        if file.stat().st_size != item["bytes"] or sha256(file) != item["sha256"]:
            raise ValueError(f"MaleCNS source checksum mismatch: {file}")
    return items


def normalize_fafb_side(side: str) -> str | None:
    return {"left": "L", "right": "R"}.get(str(side).lower())


def male_side(row: pd.Series) -> tuple[str, str]:
    # Root-side describes the entering nerve for sensory axons; otherwise use
    # the soma side where it is known. Preserve midline/unknown separately.
    sensory = "sensory" in str(row["superclass"])
    order = ("rootSide", "somaSide") if sensory else ("somaSide", "rootSide")
    for col in order:
        value = row[col]
        if value in ("L", "R", "M"):
            return value, col
    return "unknown", "unknown"


def joined_partner_type(row: pd.Series) -> tuple[str, str, bool]:
    value = row["flywireType"]
    if isinstance(value, str) and value:
        return value, "male_annotation_flywireType", "," in value
    value = row["author_cross_label"]
    if isinstance(value, str) and value:
        return value, "author_cross_type_label", "," in value
    value = row["type"]
    if isinstance(value, str) and value:
        return value, "malecns_type_only", "," in value
    return "untyped", "untyped", True


def summarise_direction(
    direction: str,
    pre: np.ndarray,
    post: np.ndarray,
    weights: np.ndarray,
    focus_ids: np.ndarray,
    neurons: pd.DataFrame,
    focus: pd.DataFrame,
) -> pd.DataFrame:
    # Restrict to observed MaleCNS pairs with both partners annotated as neurons.
    neuron_ids = neurons["bodyId"].to_numpy()
    if direction == "outgoing":
        mask = np.isin(pre, focus_ids) & np.isin(post, neuron_ids)
        source = pre[mask]
        partner = post[mask]
    else:
        mask = np.isin(post, focus_ids) & np.isin(pre, neuron_ids)
        source = post[mask]
        partner = pre[mask]
    links = pd.DataFrame({
        "male_source_id": source,
        "male_partner_id": partner,
        "male_contact_count": weights[mask],
    })
    source_cols = focus[["bodyId", "author_cross_label", "male_side"]].rename(columns={
        "bodyId": "male_source_id",
        "author_cross_label": "source_cross_type",
        "male_side": "source_side",
    })
    partner_cols = neurons[[
        "bodyId", "partner_type", "partner_type_basis", "partner_type_ambiguous",
        "male_side", "type", "flywireType",
    ]].rename(columns={
        "bodyId": "male_partner_id",
        "male_side": "partner_side",
        "type": "male_partner_type",
        "flywireType": "male_partner_flywireType",
    })
    links = links.merge(source_cols, on="male_source_id", how="inner", validate="many_to_one")
    links = links.merge(partner_cols, on="male_partner_id", how="inner", validate="many_to_one")
    links["direction"] = direction
    key = [
        "source_cross_type", "source_side", "direction", "partner_type",
        "partner_side", "partner_type_basis", "partner_type_ambiguous",
    ]
    grouped = links.groupby(key, dropna=False).agg(
        male_synaptic_contacts=("male_contact_count", "sum"),
        male_directed_body_pairs=("male_contact_count", "size"),
        male_sources_with_partner_type=("male_source_id", "nunique"),
        male_partner_neurons=("male_partner_id", "nunique"),
        male_partner_type_count=("male_partner_type", "nunique"),
    ).reset_index()
    examples = links.groupby(key, dropna=False)["male_partner_type"].agg(
        lambda x: ";".join(sorted({str(v) for v in x.dropna()})[:5])
    ).rename("male_partner_type_examples").reset_index()
    grouped = grouped.merge(examples, on=key, how="left", validate="one_to_one")
    denom_sources = focus.groupby(["author_cross_label", "male_side"]).size()
    denom_contacts = links.groupby(["source_cross_type", "source_side"])["male_contact_count"].sum()
    grouped["same_side_male_source_neurons"] = [
        int(denom_sources.loc[(label, side)])
        for label, side in zip(grouped.source_cross_type, grouped.source_side)
    ]
    grouped["male_source_prevalence"] = (
        grouped.male_sources_with_partner_type / grouped.same_side_male_source_neurons
    )
    grouped["male_synapse_share_of_direction"] = [
        float(value / denom_contacts.loc[(label, side)])
        for label, side, value in zip(
            grouped.source_cross_type, grouped.source_side, grouped.male_synaptic_contacts
        )
    ]
    return grouped


def raw_observations(selected_ids: set[str]) -> tuple[dict, dict]:
    raw_points = collections.Counter()
    with (DERIVED / "points_for_616_ids_without_proofread_edges.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        for row in csv.DictReader(stream):
            if row["pre_root_id"] in selected_ids:
                raw_points[(row["pre_root_id"], "outgoing")] += 1
            if row["post_root_id"] in selected_ids:
                raw_points[(row["post_root_id"], "incoming")] += 1

    # Existing published raw exceptions refer to this *FAFB* animal. They are
    # evidence only for the exact 21 observed FAFB pairs, never for MaleCNS IDs.
    ann_fafb = {
        row["id"]: row for row in json.loads(
            (ROOT / "brain" / "graph-original-v783" / "annotations.json").read_text()
        )
    }
    exceptions = collections.Counter()
    with (DERIVED / "observed_raw_proofread_edge_exceptions_for_616.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        for row in csv.DictReader(stream):
            pre, post = row["pre_root_id"], row["post_root_id"]
            weight = int(row["synapse_count"])
            if pre in selected_ids:
                ptype = ann_fafb.get(post, {}).get("cell_type") or "untyped"
                exceptions[(pre, "outgoing", ptype)] += weight
            if post in selected_ids:
                ptype = ann_fafb.get(pre, {}).get("cell_type") or "untyped"
                exceptions[(post, "incoming", ptype)] += weight
    return dict(raw_points), dict(exceptions)


def r7_raw_type_crosscheck(group_rows: pd.DataFrame) -> pd.DataFrame:
    """Compare distinct type names; keep FAFB exact pairs in their own source CSV."""
    selected = "720575940623940963"
    ann = {
        row["id"]: row for row in json.loads(
            (ROOT / "brain" / "graph-original-v783" / "annotations.json").read_text()
        )
    }
    raw = collections.defaultdict(lambda: [0, 0])
    with (DERIVED / "observed_raw_proofread_edge_exceptions_for_616.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        for row in csv.DictReader(stream):
            if row["pre_root_id"] == selected:
                direction = "outgoing"
                partner_id = row["post_root_id"]
            elif row["post_root_id"] == selected:
                direction = "incoming"
                partner_id = row["pre_root_id"]
            else:
                continue
            partner = ann.get(partner_id, {})
            key = (
                direction,
                partner.get("cell_type") or "untyped",
                normalize_fafb_side(partner.get("side")) or "unknown",
            )
            raw[key][0] += int(row["synapse_count"])
            raw[key][1] += 1

    male = group_rows.loc[
        group_rows.source_cross_type.eq("R7") & group_rows.source_side.eq("R")
    ]
    output = []
    for (direction, raw_type, raw_side), (raw_contacts, raw_pairs) in sorted(raw.items()):
        block = male.loc[male.direction.eq(direction)]
        if raw_side != "unknown":
            block = block.loc[block.partner_side.eq(raw_side)]
        exact = block.loc[block.partner_type.eq(raw_type)]
        if not exact.empty:
            matches = exact
            relation = "exact_type_label_only"
        elif raw_type == "Dm8":
            matches = block.loc[block.partner_type.isin(("pDm8", "yDm8"))]
            relation = "Dm8_family_only_not_exact_subtype" if not matches.empty else "no_type_label_match"
        else:
            matches = block.iloc[0:0]
            relation = "no_type_label_match"
        if matches.empty:
            output.append({
                "fafb_v783_root_id": selected,
                "direction": direction,
                "fafb_raw_partner_type": raw_type,
                "fafb_raw_partner_side": raw_side,
                "fafb_raw_calls": raw_contacts,
                "fafb_raw_directed_pair_region_rows": raw_pairs,
                "male_observed_partner_type": "",
                "male_partner_type_basis": "",
                "male_partner_type_rank": "",
                "male_synaptic_contacts": "",
                "male_source_prevalence": "",
                "type_relation": relation,
                "interpretation": "FAFB exact raw pair list remains separate; no inferred FAFB graph edge",
            })
            continue
        for hit in matches.itertuples(index=False):
            output.append({
                "fafb_v783_root_id": selected,
                "direction": direction,
                "fafb_raw_partner_type": raw_type,
                "fafb_raw_partner_side": raw_side,
                "fafb_raw_calls": raw_contacts,
                "fafb_raw_directed_pair_region_rows": raw_pairs,
                "male_observed_partner_type": hit.partner_type,
                "male_partner_type_basis": hit.partner_type_basis,
                "male_partner_type_rank": hit.rank_within_source_type_side_direction,
                "male_synaptic_contacts": hit.male_synaptic_contacts,
                "male_source_prevalence": round(hit.male_source_prevalence, 6),
                "type_relation": relation,
                "interpretation": "FAFB exact raw pair list remains separate; no inferred FAFB graph edge",
            })
    return pd.DataFrame(output)


def main() -> None:
    official = verified_male_inputs()
    missing_path = DERIVED / "model_missing_fafb_ids.csv"
    prior_path = DERIVED / "missing_neuron_type_link_hypotheses.csv"
    fa = pd.read_csv(missing_path, dtype={"root_id": str})
    assert len(fa) == 616 and fa.root_id.is_unique
    fa["side_code"] = fa.side.map(normalize_fafb_side)
    author_map = json.loads((MALE / "mcns_fw_edge_comp_mappings.json").read_text())
    fa["author_cross_label"] = fa.root_id.map(author_map)

    ann = feather.read_table(MALE / "body-annotations-male-cns-v1.0-minconf-0.5.feather")
    neurons = ann.to_pandas()
    neurons = neurons.loc[neurons.superclass.notna()].copy()
    assert len(neurons) == 166700 and neurons.bodyId.is_unique
    sides = neurons.apply(male_side, axis=1)
    neurons["male_side"] = [x[0] for x in sides]
    neurons["male_side_basis"] = [x[1] for x in sides]
    neurons["author_cross_label"] = neurons.bodyId.astype(str).map(author_map)
    partner_values = neurons.apply(joined_partner_type, axis=1)
    neurons["partner_type"] = [x[0] for x in partner_values]
    neurons["partner_type_basis"] = [x[1] for x in partner_values]
    neurons["partner_type_ambiguous"] = [x[2] for x in partner_values]

    needed_labels = set(fa.author_cross_label.dropna())
    focus = neurons.loc[
        neurons.author_cross_label.isin(needed_labels)
        & neurons.male_side.isin(("L", "R"))
    ].copy()
    # Preserve only cohorts requested by a FAFB cell on that same anatomical side.
    requested = set(zip(fa.author_cross_label, fa.side_code))
    focus = focus.loc[
        [(label, side) in requested for label, side in zip(focus.author_cross_label, focus.male_side)]
    ].copy()
    focus_ids = focus.bodyId.to_numpy()
    weights = feather.read_table(
        MALE / "connectome-weights-male-cns-v1.0-minconf-0.5-traced-only.feather",
        columns=["body_pre", "body_post", "weight"],
    )
    pre = weights["body_pre"].to_numpy()
    post = weights["body_post"].to_numpy()
    strength = weights["weight"].to_numpy()
    group_rows = pd.concat([
        summarise_direction("outgoing", pre, post, strength, focus_ids, neurons, focus),
        summarise_direction("incoming", pre, post, strength, focus_ids, neurons, focus),
    ], ignore_index=True)
    group_rows = group_rows.sort_values(
        ["source_cross_type", "source_side", "direction", "male_source_prevalence",
         "male_synaptic_contacts", "partner_type", "partner_side"],
        ascending=[True, True, True, False, False, True, True],
    )
    group_rows["rank_within_source_type_side_direction"] = (
        group_rows.groupby(["source_cross_type", "source_side", "direction"]).cumcount() + 1
    )
    group_rows["evidence_tier"] = "cross_animal_observed_malecns_type_only"
    group_rows.to_csv(OUT_GROUPS, index=False)

    # Group coverage and ambiguity are copied to every individual FAFB ID.
    source_stats = focus.groupby(["author_cross_label", "male_side"]).agg(
        same_side_male_sources=("bodyId", "size"),
        distinct_male_source_types=("type", "nunique"),
        distinct_source_side_bases=("male_side_basis", "nunique"),
    )
    all_label_side = neurons.loc[neurons.author_cross_label.isin(needed_labels)].groupby(
        ["author_cross_label", "male_side"]
    ).size()
    fafb_group_size = fa.groupby(["author_cross_label", "side_code"]).size()
    selected_ids = set(fa.root_id)
    point_counts, raw_exception_counts = raw_observations(selected_ids)
    prior = pd.read_csv(prior_path, dtype={"root_id": str})
    prior = prior.loc[
        prior.candidate_target_type.notna()
        & prior.status.eq("type_level_hypothesis_only")
    ].copy()
    prior_rows = {(row.root_id, row.candidate_target_type): row for row in prior.itertuples()}
    prior_by_id = prior.groupby("root_id").size().to_dict()

    top = group_rows.loc[
        group_rows.rank_within_source_type_side_direction <= TOP_PER_DIRECTION
    ]
    top_lookup = {
        key: block for key, block in top.groupby(["source_cross_type", "source_side"])
    }
    all_lookup = {
        key: block for key, block in group_rows.groupby(["source_cross_type", "source_side"])
    }
    per_id_rows = []
    coverage_rows = []
    for row in fa.itertuples():
        key = (row.author_cross_label, row.side_code)
        mapped = isinstance(row.author_cross_label, str)
        same_count = int(source_stats.loc[key, "same_side_male_sources"]) if key in source_stats.index else 0
        other_side = "R" if row.side_code == "L" else "L"
        opposite = int(all_label_side.get((row.author_cross_label, other_side), 0)) if mapped else 0
        unknown = int(all_label_side.get((row.author_cross_label, "unknown"), 0)) if mapped else 0
        candidate_block = top_lookup.get(key)
        all_block = all_lookup.get(key)
        raw_out = point_counts.get((row.root_id, "outgoing"), 0)
        raw_in = point_counts.get((row.root_id, "incoming"), 0)
        raw_exception_out = sum(
            count for (root, direction, _), count in raw_exception_counts.items()
            if root == row.root_id and direction == "outgoing"
        )
        raw_exception_in = sum(
            count for (root, direction, _), count in raw_exception_counts.items()
            if root == row.root_id and direction == "incoming"
        )
        cover = {
            "fafb_root_id": row.root_id,
            "fafb_v783_cell_type": row.cell_type,
            "fafb_v783_side": row.side,
            "author_cross_type_label": row.author_cross_label if mapped else "",
            "status": "mapped_same_side" if same_count else ("mapped_no_same_side" if mapped else "unmapped"),
            "same_side_malecns_neurons": same_count,
            "opposite_side_malecns_neurons": opposite,
            "unknown_side_malecns_neurons": unknown,
            "male_source_type_count": int(source_stats.loc[key, "distinct_male_source_types"]) if same_count else 0,
            "male_source_type_examples": (
                ";".join(sorted(set(focus.loc[
                    focus.author_cross_label.eq(row.author_cross_label)
                    & focus.male_side.eq(row.side_code), "type"
                ].dropna().astype(str)))[:8]) if same_count else ""
            ),
            "fafb_ids_sharing_type_and_side": int(fafb_group_size.loc[key]) if mapped and key in fafb_group_size.index else 0,
            "observed_fafb_raw_outgoing_calls": raw_out,
            "observed_fafb_raw_incoming_calls": raw_in,
            "observed_fafb_raw_proofread_exception_outgoing_calls": raw_exception_out,
            "observed_fafb_raw_proofread_exception_incoming_calls": raw_exception_in,
            "prior_v783_homolog_outgoing_type_candidates": int(prior_by_id.get(row.root_id, 0)),
            "all_malecns_partner_type_side_rows": len(all_block) if all_block is not None else 0,
            "prioritized_malecns_rows": len(candidate_block) if candidate_block is not None else 0,
        }
        coverage_rows.append(cover)
        if candidate_block is None:
            continue
        for candidate in candidate_block.itertuples(index=False):
            partner_type = candidate.partner_type
            prior_hit = (
                prior_rows.get((row.root_id, partner_type))
                if candidate.direction == "outgoing"
                and candidate.partner_type_basis != "malecns_type_only"
                and candidate.partner_type_basis != "untyped"
                and not candidate.partner_type_ambiguous
                else None
            )
            raw_support = raw_exception_counts.get((row.root_id, candidate.direction, partner_type), 0)
            per_id_rows.append({
                "evidence_tier": "D_cross_animal_type_hypothesis_only",
                "fafb_root_id": row.root_id,
                "fafb_v783_cell_type": row.cell_type,
                "fafb_v783_side": row.side,
                "male_source_cross_type": candidate.source_cross_type,
                "male_source_side": candidate.source_side,
                "direction_relative_to_fafb_type": candidate.direction,
                "rank_within_source_type_side_direction": candidate.rank_within_source_type_side_direction,
                "male_partner_type_label": partner_type,
                "male_partner_type_basis": candidate.partner_type_basis,
                "male_partner_type_ambiguous": candidate.partner_type_ambiguous,
                "male_partner_side": candidate.partner_side,
                "male_partner_type_examples": candidate.male_partner_type_examples,
                "same_side_male_source_neurons": candidate.same_side_male_source_neurons,
                "male_sources_with_partner_type": candidate.male_sources_with_partner_type,
                "male_source_prevalence": round(candidate.male_source_prevalence, 6),
                "male_directed_body_pairs": candidate.male_directed_body_pairs,
                "male_partner_neurons": candidate.male_partner_neurons,
                "male_synaptic_contacts": candidate.male_synaptic_contacts,
                "male_synapse_share_of_direction": round(candidate.male_synapse_share_of_direction, 6),
                "fafb_ids_sharing_same_male_cohort": int(fafb_group_size.loc[key]),
                "prior_fafb_homolog_outgoing_type_match": prior_hit is not None,
                "prior_fafb_homolog_support_fraction": (
                    prior_hit.homolog_support_fraction if prior_hit is not None else ""
                ),
                "observed_fafb_raw_exception_contacts_same_type": raw_support,
                "observed_fafb_raw_calls_touching_id": raw_out + raw_in,
                "interpretation": "Other male animal, type-level only; not an individual FAFB root-to-root edge",
            })

    pd.DataFrame(per_id_rows).to_csv(OUT_IDS, index=False)
    pd.DataFrame(coverage_rows).to_csv(OUT_COVERAGE, index=False)
    r7_crosscheck = r7_raw_type_crosscheck(group_rows)
    r7_crosscheck.to_csv(OUT_R7_CROSSCHECK, index=False)
    mapped = sum(x["status"] == "mapped_same_side" for x in coverage_rows)
    id_rows = pd.DataFrame(per_id_rows)
    coverage_df = pd.DataFrame(coverage_rows)
    agreement_ids = set(id_rows.loc[
        id_rows.prior_fafb_homolog_outgoing_type_match, "fafb_root_id"
    ])
    strata = {}
    for name, block in (
        ("R1-6", coverage_df.loc[coverage_df.fafb_v783_cell_type.eq("R1-6")]),
        ("other_96", coverage_df.loc[~coverage_df.fafb_v783_cell_type.eq("R1-6")]),
    ):
        strata[name] = {
            "fafb_ids": len(block),
            "author_cross_mapped_same_side": int(block.status.eq("mapped_same_side").sum()),
            "unmapped": int(block.status.eq("unmapped").sum()),
            "with_prior_v783_homolog_type_hypothesis": int(
                block.prior_v783_homolog_outgoing_type_candidates.gt(0).sum()
            ),
            "with_prioritized_type_string_agreement": int(
                block.fafb_root_id.isin(agreement_ids).sum()
            ),
            "with_any_released_v783_raw_point": int(
                (block.observed_fafb_raw_outgoing_calls + block.observed_fafb_raw_incoming_calls).gt(0).sum()
            ),
            "released_v783_raw_point_calls": int(
                (block.observed_fafb_raw_outgoing_calls + block.observed_fafb_raw_incoming_calls).sum()
            ),
        }
    audit = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_release": "MaleCNS v1.0, separate male animal",
        "fafb_release": "FlyWire FAFB v783, separate female animal",
        "source_male_files": {
            name: {"bytes": official[name]["bytes"], "sha256": official[name]["sha256"]}
            for name in (
                "body-annotations-male-cns-v1.0-minconf-0.5.feather",
                "connectome-weights-male-cns-v1.0-minconf-0.5-traced-only.feather",
                "mcns_fw_edge_comp_mappings.json",
            )
        },
        "source_fafb_files_sha256": {
            str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
            for path in (
                missing_path, prior_path,
                DERIVED / "points_for_616_ids_without_proofread_edges.csv",
                DERIVED / "observed_raw_proofread_edge_exceptions_for_616.csv",
                ROOT / "brain" / "graph-original-v783" / "annotations.json",
            )
        },
        "method": {
            "source_cell_mapping": "Author MaleCNS↔FlyWire cross-type JSON, exact FAFB root ID to label; male body IDs sharing label and anatomical side.",
            "side": "Male sensory axons use rootSide where valid; other neurons use somaSide where valid; opposite/unknown sides excluded.",
            "male_edges": "Observed directed MaleCNS v1.0 traced-only body-pair weights, both endpoints annotated as neurons.",
            "partner_label": "Prefer MaleCNS flywireType annotation, else author cross-type label, else MaleCNS type; retain ambiguous comma lists.",
            "ranking": "Within source type+side+direction, descending prevalence of male source neurons with that partner type+side, then descending total synapse contacts; top ten per direction expanded to each FAFB ID.",
            "comparison": "Exact target-type string comparison with existing v783 homolog hypotheses (outgoing only); released v783 raw points and proofread raw exceptions remain separate evidence columns.",
        },
        "counts": {
            "fafb_ids_total": len(fa),
            "fafb_ids_in_author_cross_mapping": int(fa.author_cross_label.notna().sum()),
            "fafb_ids_with_same_side_male_sources": mapped,
            "fafb_ids_unmapped": sum(x["status"] == "unmapped" for x in coverage_rows),
            "fafb_ids_mapped_but_no_same_side_source": sum(x["status"] == "mapped_no_same_side" for x in coverage_rows),
            "male_source_neurons_in_requested_cohorts": len(focus),
            "male_source_type_side_cohorts": len(source_stats),
            "all_observed_male_partner_type_side_rows": len(group_rows),
            "prioritized_rows_expanded_to_fafb_ids": len(id_rows),
            "fafb_ids_with_prior_v783_homolog_hypotheses": len(prior_by_id),
            "prioritized_outgoing_rows_matching_prior_homolog_type": int(
                id_rows["prior_fafb_homolog_outgoing_type_match"].sum()
            ),
            "fafb_ids_with_any_prioritized_outgoing_type_agreement": int(
                id_rows.loc[id_rows.prior_fafb_homolog_outgoing_type_match, "fafb_root_id"].nunique()
            ),
            "fafb_ids_with_released_raw_points": sum(
                x["observed_fafb_raw_outgoing_calls"] + x["observed_fafb_raw_incoming_calls"] > 0
                for x in coverage_rows
            ),
            "fafb_ids_with_raw_proofread_exceptions": sum(
                x["observed_fafb_raw_proofread_exception_outgoing_calls"]
                + x["observed_fafb_raw_proofread_exception_incoming_calls"] > 0
                for x in coverage_rows
            ),
            "fafb_raw_point_calls_touched": int(
                coverage_df.observed_fafb_raw_outgoing_calls.sum()
                + coverage_df.observed_fafb_raw_incoming_calls.sum()
            ),
            "fafb_raw_proofread_exception_calls": int(
                coverage_df.observed_fafb_raw_proofread_exception_outgoing_calls.sum()
                + coverage_df.observed_fafb_raw_proofread_exception_incoming_calls.sum()
            ),
            "ids_with_multiple_malecns_source_type_names": int(
                coverage_df.male_source_type_count.gt(1).sum()
            ),
            "r7_raw_type_crosscheck_rows": len(r7_crosscheck),
        },
        "strata": strata,
        "outputs": {
            str(path.relative_to(ROOT)).replace("\\", "/"): {
                "bytes": path.stat().st_size, "sha256": sha256(path)
            } for path in (OUT_GROUPS, OUT_IDS, OUT_COVERAGE, OUT_R7_CROSSCHECK)
        },
        "hard_boundary": "No exact FAFB synapses or root-to-root partner IDs are inferred or added; this is cross-animal type evidence only.",
    }
    OUT_AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit["counts"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
