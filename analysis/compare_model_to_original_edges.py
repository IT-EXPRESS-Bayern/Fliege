"""Compare every Shiu v783 pair and synapse count with our full original CSR export."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

root = Path(__file__).resolve().parents[1]
graph = root / "brain/graph-original-v783"
nodes = np.fromfile(graph / "nodes.u64", dtype="<u8")
offsets = np.fromfile(graph / "offsets.u32", dtype="<u4")
targets = np.memmap(graph / "targets.u32", dtype="<u4", mode="r")
synapses = np.memmap(graph / "synapses.u32", dtype="<u4", mode="r")
model_ids = pd.read_csv(
    root / "data/research_sources/shiu/Completeness_783.csv",
    usecols=["Unnamed: 0"], dtype={"Unnamed: 0": "uint64"},
)["Unnamed: 0"].to_numpy(dtype=np.uint64)
model_to_graph = np.searchsorted(nodes, model_ids)
assert np.all(model_to_graph < nodes.size)
assert np.array_equal(nodes[model_to_graph], model_ids)

src = np.repeat(np.arange(nodes.size, dtype=np.uint32), np.diff(offsets).astype(np.int64))
graph_keys = src.astype(np.uint64) * np.uint64(nodes.size) + targets.astype(np.uint64)
assert bool(np.all(graph_keys[1:] > graph_keys[:-1]))
del src

parquet = pq.ParquetFile(root / "data/research_sources/shiu/Connectivity_783.parquet")
all_model_keys = np.empty(parquet.metadata.num_rows, dtype=np.uint64)
edge_not_found = 0
synapse_mismatch = 0
checked = 0
for group in range(parquet.num_row_groups):
    table = parquet.read_row_group(group, columns=[
        "Presynaptic_Index", "Postsynaptic_Index", "Connectivity",
    ])
    pre = table["Presynaptic_Index"].to_numpy().astype(np.int64)
    post = table["Postsynaptic_Index"].to_numpy().astype(np.int64)
    weight = table["Connectivity"].to_numpy().astype(np.uint32)
    keys = model_to_graph[pre].astype(np.uint64) * np.uint64(nodes.size) + model_to_graph[post].astype(np.uint64)
    all_model_keys[checked:checked + len(keys)] = keys
    pos = np.searchsorted(graph_keys, keys)
    found = (pos < len(graph_keys)) & (graph_keys[np.minimum(pos, len(graph_keys) - 1)] == keys)
    edge_not_found += int((~found).sum())
    synapse_mismatch += int((synapses[pos[found]] != weight[found]).sum())
    checked += len(keys)
    print(f"row group {group + 1}/{parquet.num_row_groups}: {checked:,} rows")

all_model_keys.sort()
same_pair_set = bool(np.array_equal(all_model_keys, graph_keys))
result = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "shiu_model_rows_checked": checked,
    "original_graph_edges": int(len(graph_keys)),
    "model_pair_keys_unique": bool(np.all(all_model_keys[1:] > all_model_keys[:-1])),
    "same_exact_directed_pair_set": same_pair_set,
    "model_edges_missing_from_original": edge_not_found,
    "synapse_count_mismatches": synapse_mismatch,
    "source_model": "data/research_sources/shiu/Connectivity_783.parquet",
    "source_original_export": "brain/graph-original-v783/manifest.json",
}
(root / "analysis/model_original_edge_comparison.json").write_text(
    json.dumps(result, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(result, indent=2))
