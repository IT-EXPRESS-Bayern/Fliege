"""Check Shiu/Eon v783 model tables against the original FlyWire IDs."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.feather as feather
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "data" / "research_sources"


def read_model_ids(path: Path) -> tuple[np.ndarray, pd.DataFrame]:
    table = pd.read_csv(path, dtype=str, index_col=0)
    ids = np.fromiter((int(value) for value in table.index), dtype=np.uint64, count=len(table))
    if len(np.unique(ids)) != len(ids):
        raise ValueError(f"Duplicate model IDs in {path}")
    return ids, table


def check_connection_indices(path: Path, model_ids: np.ndarray) -> dict:
    parquet = pq.ParquetFile(path)
    rows = 0
    mismatched_pre = mismatched_post = mismatched_sign = 0
    synapse_sum = 0
    signs: Counter[int] = Counter()
    columns = ["Presynaptic_ID", "Postsynaptic_ID", "Presynaptic_Index",
               "Postsynaptic_Index", "Connectivity", "Excitatory", "Excitatory x Connectivity"]
    for batch in parquet.iter_batches(batch_size=250_000, columns=columns):
        values = {name: batch.column(i).to_numpy(zero_copy_only=False) for i, name in enumerate(columns)}
        pre_idx, post_idx = values["Presynaptic_Index"], values["Postsynaptic_Index"]
        if np.any(pre_idx < 0) or np.any(post_idx < 0) or np.any(pre_idx >= len(model_ids)) or np.any(post_idx >= len(model_ids)):
            raise ValueError("Connectivity index outside the Shiu/Eon completeness list")
        mismatched_pre += int(np.count_nonzero(model_ids[pre_idx] != values["Presynaptic_ID"].astype(np.uint64)))
        mismatched_post += int(np.count_nonzero(model_ids[post_idx] != values["Postsynaptic_ID"].astype(np.uint64)))
        weight = values["Connectivity"].astype(np.int64)
        sign = values["Excitatory"].astype(np.int64)
        signed = values["Excitatory x Connectivity"].astype(np.int64)
        mismatched_sign += int(np.count_nonzero(sign * weight != signed))
        synapse_sum += int(weight.sum(dtype=np.int64))
        for value, count in zip(*np.unique(sign, return_counts=True)):
            signs[int(value)] += int(count)
        rows += batch.num_rows
    return {
        "rows": rows,
        "synapse_count_sum": synapse_sum,
        "pre_index_root_id_mismatches": mismatched_pre,
        "post_index_root_id_mismatches": mismatched_post,
        "signed_weight_mismatches": mismatched_sign,
        "sign_rows": dict(signs),
    }


def main() -> None:
    shiu_ids, shiu_table = read_model_ids(RESEARCH / "shiu" / "Completeness_783.csv")
    eon_ids, eon_table = read_model_ids(RESEARCH / "eon" / "data" / "2025_Completeness_783.csv")
    official_ids = np.unique(np.load(ROOT / "data" / "flywire_fafb_v783" / "proofread_root_ids_783.npy"))
    original_edges = feather.read_table(
        ROOT / "data" / "flywire_fafb_v783" / "proofread_connections_783.feather",
        columns=["pre_pt_root_id", "post_pt_root_id"],
    )
    connected_ids = np.union1d(
        original_edges[0].to_numpy().astype(np.uint64),
        original_edges[1].to_numpy().astype(np.uint64),
    )
    missing_ids = np.setdiff1d(official_ids, shiu_ids, assume_unique=True)
    model_only_ids = np.setdiff1d(shiu_ids, official_ids, assume_unique=True)
    annotations = pd.read_csv(
        ROOT / "data" / "flywire_annotations_v2.1.0" / "Supplemental_file1_neuron_annotations.tsv",
        sep="\t", dtype=str, low_memory=False,
    ).set_index("root_id", drop=False)
    selected_columns = ["root_id", "flow", "super_class", "cell_class", "cell_type", "side"]
    missing_rows = annotations.loc[[str(int(value)) for value in missing_ids], selected_columns].fillna("")
    out_dir = RESEARCH / "derived"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "model_missing_fafb_ids.csv"
    missing_rows.to_csv(out_file, index=False, quoting=csv.QUOTE_ALL)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_files": [
            "data/flywire_fafb_v783/proofread_root_ids_783.npy",
            "data/flywire_fafb_v783/proofread_connections_783.feather",
            "data/flywire_annotations_v2.1.0/Supplemental_file1_neuron_annotations.tsv",
            "data/research_sources/shiu/Completeness_783.csv",
            "data/research_sources/shiu/Connectivity_783.parquet",
            "data/research_sources/eon/data/2025_Completeness_783.csv",
        ],
        "official_root_ids": len(official_ids),
        "shiu_model_ids": len(shiu_ids),
        "eon_model_ids": len(eon_ids),
        "eon_and_shiu_same_order": bool(np.array_equal(eon_ids, shiu_ids)),
        "eon_and_shiu_same_completed_values": bool(eon_table["Completed"].equals(shiu_table["Completed"])),
        "model_only_ids": len(model_only_ids),
        "official_ids_missing_from_model": len(missing_ids),
        "official_ids_in_proofread_connection_table": len(connected_ids),
        "model_ids_equal_connected_original_ids": bool(np.array_equal(np.sort(shiu_ids), connected_ids)),
        "missing_model_ids_have_no_proofread_connection_rows": bool(
            np.intersect1d(missing_ids, connected_ids).size == 0
        ),
        "missing_by_flow": missing_rows["flow"].value_counts().to_dict(),
        "missing_by_super_class": missing_rows["super_class"].value_counts().to_dict(),
        "missing_by_cell_class_top_12": missing_rows["cell_class"].value_counts().head(12).to_dict(),
        "connectivity": check_connection_indices(RESEARCH / "shiu" / "Connectivity_783.parquet", shiu_ids),
        "missing_ids_output": str(out_file.relative_to(ROOT)).replace("\\", "/"),
        "note": "The 616 omitted official IDs do not occur in either partner column of the original proofread connection table. This explains the model node set; the biological reason for each absence is not inferred.",
    }
    (ROOT / "analysis" / "research_data_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
