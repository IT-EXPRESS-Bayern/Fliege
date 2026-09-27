"""Quantify released synapses excluded from the published proofread pair table.

Uses the two small official all-partner count tables, so it can run while the
9.49 GB point table is still downloading. Counts are anatomical detections,
not inferred or biologically validated missing synapses.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.ipc as ipc

root = Path(__file__).resolve().parents[1]
data = root / "data/flywire_fafb_v783"
out = root / "data/research_sources/derived"
out.mkdir(parents=True, exist_ok=True)
ids = np.sort(np.load(data / "proofread_root_ids_783.npy").astype(np.int64))
assert np.all(ids[1:] > ids[:-1])
n = ids.size


def matched_indexes(batch, name):
    values = batch.column(batch.schema.get_field_index(name)).to_numpy()
    indexes = np.searchsorted(ids, values)
    matches = (indexes < n) & (ids[np.minimum(indexes, n - 1)] == values)
    return indexes, matches


def count_table(path, id_column):
    known = np.zeros(n, dtype=np.uint64)
    all_count = 0
    known_count = 0
    row_count = 0
    with pa.memory_map(str(path), "r") as file:
        reader = ipc.open_file(file)
        for i in range(reader.num_record_batches):
            batch = reader.get_batch(i)
            indexes, matches = matched_indexes(batch, id_column)
            counts = batch.column(batch.schema.get_field_index("count")).to_numpy().astype(np.int64)
            assert np.all(counts >= 0)
            all_count += int(counts.sum())
            known_count += int(counts[matches].sum())
            known += np.bincount(
                indexes[matches], weights=counts[matches], minlength=n
            ).astype(np.uint64)
            row_count += batch.num_rows
    return known, {"rows": row_count, "all_synapse_counts": all_count,
                   "proofread_neuron_synapse_counts": known_count,
                   "unproofread_neuron_synapse_counts": all_count - known_count}


pre_all, pre_info = count_table(data / "per_neuron_neuropil_count_pre_783.feather", "pre_pt_root_id")
post_all, post_info = count_table(data / "per_neuron_neuropil_count_post_783.feather", "post_pt_root_id")
pre_proofread = np.zeros(n, dtype=np.uint64)
post_proofread = np.zeros(n, dtype=np.uint64)
edge_rows = 0
with pa.memory_map(str(data / "proofread_connections_783.feather"), "r") as file:
    reader = ipc.open_file(file)
    for i in range(reader.num_record_batches):
        batch = reader.get_batch(i)
        pre_idx, pre_match = matched_indexes(batch, "pre_pt_root_id")
        post_idx, post_match = matched_indexes(batch, "post_pt_root_id")
        assert bool(np.all(pre_match)) and bool(np.all(post_match))
        counts = batch.column(batch.schema.get_field_index("syn_count")).to_numpy().astype(np.int64)
        pre_proofread += np.bincount(pre_idx, weights=counts, minlength=n).astype(np.uint64)
        post_proofread += np.bincount(post_idx, weights=counts, minlength=n).astype(np.uint64)
        edge_rows += batch.num_rows

assert np.all(pre_all >= pre_proofread), "Pre counts smaller than proofread graph"
assert np.all(post_all >= post_proofread), "Post counts smaller than proofread graph"
pre_other = pre_all - pre_proofread
post_other = post_all - post_proofread
assert int(pre_proofread.sum()) == int(post_proofread.sum()) == 54_492_922
assert pre_info["all_synapse_counts"] == post_info["all_synapse_counts"], "Pre/post global totals disagree"

annotations = {}
with (root / "data/flywire_annotations_v2.1.0/Supplemental_file1_neuron_annotations.tsv").open(
    "r", encoding="utf-8-sig", newline=""
) as file:
    for row in csv.DictReader(file, delimiter="\t"):
        annotations[row["root_id"]] = (row.get("super_class", ""), row.get("cell_class", ""), row.get("cell_type", ""))

csv_path = out / "proofread_synapse_coverage_by_neuron.csv"
with csv_path.open("w", encoding="utf-8", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["root_id", "super_class", "cell_class", "cell_type",
                     "all_pre_points", "aggregated_table_pre_points", "outside_aggregated_pre_points",
                     "all_post_points", "aggregated_table_post_points", "outside_aggregated_post_points"])
    for i, root_id in enumerate(ids):
        rid = str(int(root_id))
        writer.writerow([rid, *annotations.get(rid, ("", "", "")),
                         int(pre_all[i]), int(pre_proofread[i]), int(pre_other[i]),
                         int(post_all[i]), int(post_proofread[i]), int(post_other[i])])

disconnected = (pre_proofread + post_proofread) == 0
top_output = np.argsort(pre_other)[-20:][::-1]
top_input = np.argsort(post_other)[-20:][::-1]
summary = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "source": "https://zenodo.org/records/10676866",
    "method": "Official per-neuron, per-neuropil all-partner counts minus official proofread-connection counts, summed per exact v783 root ID. A difference is not necessarily an unproofread partner: 48 released raw contacts have two proofread IDs but are absent from the published pair table.",
    "pre_table": pre_info,
    "post_table": post_info,
    "proofread_connection_rows": edge_rows,
    "proofread_connection_synapses": int(pre_proofread.sum()),
    "released_synapses_outside_aggregated_pair_table": pre_info["all_synapse_counts"] - int(pre_proofread.sum()),
    "proofread_pre_neuron_points_outside_aggregated_pair_table": int(pre_other.sum()),
    "proofread_post_neuron_points_outside_aggregated_pair_table": int(post_other.sum()),
    "official_ids_without_proofread_edges": int(disconnected.sum()),
    "of_these_with_any_released_point": int(np.count_nonzero(disconnected & ((pre_all + post_all) > 0))),
    "of_these_with_no_released_point": int(np.count_nonzero(disconnected & ((pre_all + post_all) == 0))),
    "output_csv": str(csv_path.relative_to(root)).replace("\\", "/"),
    "top_20_proofread_neurons_by_output_points_outside_aggregated_pair_table": [
        {"root_id": str(int(ids[i])), "count": int(pre_other[i]),
         "cell_class": annotations.get(str(int(ids[i])), ("", "", ""))[1]} for i in top_output
    ],
    "top_20_proofread_neurons_by_input_points_outside_aggregated_pair_table": [
        {"root_id": str(int(ids[i])), "count": int(post_other[i]),
         "cell_class": annotations.get(str(int(ids[i])), ("", "", ""))[1]} for i in top_input
    ],
    "limits": [
        "A difference from the published pair table is not automatically a contact with an unproofread partner; inspect the verified raw point table to classify it.",
        "A counted point with an unproofread partner is an existing released synapse, not a newly predicted biological synapse.",
        "The all-partner summaries alone cannot identify the exact omitted partner or spatial point; use flywire_synapses_783.feather.",
        "Synapses below the published cleft-score threshold and missed by detection do not appear in any of these files.",
    ],
}
summary_path = root / "analysis/synapse_coverage_audit.json"
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: value for key, value in summary.items() if key not in (
    "top_20_proofread_neurons_by_output_points_outside_aggregated_pair_table",
    "top_20_proofread_neurons_by_input_points_outside_aggregated_pair_table",
)}, ensure_ascii=False, indent=2))
