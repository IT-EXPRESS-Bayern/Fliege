"""Stream the completed 9.49 GB FlyWire point table and classify its contacts.

Run only after the download pipeline has verified and renamed the final file.
For 616 proofread IDs absent from the proofread edge graph, export each observed
synapse point with coordinates and its actual released partner segment ID.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.ipc as ipc

root = Path(__file__).resolve().parents[1]
source = root / "data/flywire_fafb_v783/flywire_synapses_783.feather"
if not source.is_file():
    raise SystemExit("Verified flywire_synapses_783.feather is not ready; the .partial file must not be analyzed.")

coverage = json.loads((root / "analysis/synapse_coverage_audit.json").read_text(encoding="utf-8"))
official_ids = np.sort(np.load(root / "data/flywire_fafb_v783/proofread_root_ids_783.npy").astype(np.int64))
known = set()
with (root / coverage["output_csv"]).open("r", encoding="utf-8", newline="") as file:
    for row in csv.DictReader(file):
        if int(row["aggregated_table_pre_points"]) + int(row["aggregated_table_post_points"]) == 0:
            known.add(int(row["root_id"]))
missing_ids = np.array(sorted(known), dtype=np.int64)
assert len(missing_ids) == 616
expected_selected_counts = {}
with (root / coverage["output_csv"]).open("r", encoding="utf-8", newline="") as file:
    for row in csv.DictReader(file):
        if int(row["root_id"]) in known:
            expected_selected_counts[row["root_id"]] = int(row["all_pre_points"]) + int(row["all_post_points"])


def numpy_int(column):
    """Fill nullable Arrow integers before NumPy conversion to preserve 18-digit IDs."""
    return pc.fill_null(column, 0).to_numpy(zero_copy_only=False).astype(np.int64)


def in_sorted(sorted_ids, values):
    index = np.searchsorted(sorted_ids, values)
    return (index < len(sorted_ids)) & (sorted_ids[np.minimum(index, len(sorted_ids) - 1)] == values)


names = (
    "id", "pre_pt_root_id", "post_pt_root_id", "cleft_score", "connection_score",
    "pre_pt_position_x", "pre_pt_position_y", "pre_pt_position_z",
    "post_pt_position_x", "post_pt_position_y", "post_pt_position_z", "neuropil",
)
counts = Counter()
selected_id_counts = Counter()
coord_min = {key: None for key in names if key.endswith(("_x", "_y", "_z"))}
coord_max = {key: None for key in coord_min}
output = root / "data/research_sources/derived/points_for_616_ids_without_proofread_edges.csv"
temporary = output.with_suffix(".csv.partial")
output.parent.mkdir(parents=True, exist_ok=True)

with pa.memory_map(str(source), "r") as file, temporary.open("w", encoding="utf-8", newline="") as csv_file:
    reader = ipc.open_file(file)
    required = set(names)
    if not required.issubset(reader.schema.names):
        raise ValueError(f"Unexpected point schema; missing {sorted(required - set(reader.schema.names))}")
    writer = csv.writer(csv_file)
    writer.writerow(["synapse_id", "pre_root_id", "post_root_id", "pre_root_proofread",
                     "post_root_proofread", "pre_x_nm", "pre_y_nm", "pre_z_nm",
                     "post_x_nm", "post_y_nm", "post_z_nm", "cleft_score",
                     "connection_score", "neuropil"])
    for batch_no in range(reader.num_record_batches):
        batch = reader.get_batch(batch_no)
        score_names = {"cleft_score", "connection_score"}
        arr = {name: numpy_int(batch.column(batch.schema.get_field_index(name)))
               for name in names if name not in score_names and name != "neuropil"}
        for name in score_names:
            col = batch.column(batch.schema.get_field_index(name))
            counts[f"{name}_null"] += col.null_count
            arr[name] = pc.fill_null(col, 0).to_numpy(zero_copy_only=False).astype(np.float64)
        pre = arr["pre_pt_root_id"]
        post = arr["post_pt_root_id"]
        pre_ok = in_sorted(official_ids, pre)
        post_ok = in_sorted(official_ids, post)
        selected = in_sorted(missing_ids, pre) | in_sorted(missing_ids, post)
        counts["rows"] += batch.num_rows
        counts["both_proofread"] += int(np.count_nonzero(pre_ok & post_ok))
        counts["both_proofread_self"] += int(np.count_nonzero(pre_ok & post_ok & (pre == post)))
        counts["all_self"] += int(np.count_nonzero(pre == post))
        counts["only_pre_proofread"] += int(np.count_nonzero(pre_ok & ~post_ok))
        counts["only_post_proofread"] += int(np.count_nonzero(~pre_ok & post_ok))
        counts["neither_proofread"] += int(np.count_nonzero(~pre_ok & ~post_ok))
        counts["cleft_below_50"] += int(np.count_nonzero(arr["cleft_score"] < 50))
        counts["selected_points"] += int(np.count_nonzero(selected))
        neuropil_col = batch.column(batch.schema.get_field_index("neuropil"))
        counts["both_proofread_neuropil_null"] += int(np.count_nonzero(
            pre_ok & post_ok & ~pc.is_valid(neuropil_col).to_numpy(zero_copy_only=False)
        ))
        for key in coord_min:
            col = batch.column(batch.schema.get_field_index(key))
            counts[f"{key}_null"] += col.null_count
            valid = arr[key][pc.is_valid(col).to_numpy(zero_copy_only=False)]
            if len(valid):
                lo, hi = int(valid.min()), int(valid.max())
                coord_min[key] = lo if coord_min[key] is None else min(lo, coord_min[key])
                coord_max[key] = hi if coord_max[key] is None else max(hi, coord_max[key])
        idx = np.flatnonzero(selected)
        if len(idx):
            neuropils = batch.column(batch.schema.get_field_index("neuropil")).take(pa.array(idx)).to_pylist()
            for local, p in enumerate(idx):
                if pre[p] in known:
                    selected_id_counts[str(int(pre[p]))] += 1
                if post[p] in known and post[p] != pre[p]:
                    selected_id_counts[str(int(post[p]))] += 1
                writer.writerow([int(arr["id"][p]), int(pre[p]), int(post[p]),
                                 bool(pre_ok[p]), bool(post_ok[p]),
                                 *[int(arr[f"pre_pt_position_{axis}"][p]) for axis in "xyz"],
                                 *[int(arr[f"post_pt_position_{axis}"][p]) for axis in "xyz"],
                                 float(arr["cleft_score"][p]), float(arr["connection_score"][p]),
                                 neuropils[local]])
        if (batch_no + 1) % 100 == 0:
            print(f"batches {batch_no + 1}/{reader.num_record_batches}; rows {counts['rows']:,}")

assert counts["rows"] == coverage["pre_table"]["all_synapse_counts"]
assert sum(counts[key] for key in (
    "both_proofread", "only_pre_proofread", "only_post_proofread", "neither_proofread"
)) == counts["rows"]
assert counts["both_proofread"] + counts["only_pre_proofread"] == coverage["pre_table"]["proofread_neuron_synapse_counts"]
assert counts["both_proofread"] + counts["only_post_proofread"] == coverage["post_table"]["proofread_neuron_synapse_counts"]
assert counts["cleft_below_50"] == 0
assert len(selected_id_counts) == coverage["of_these_with_any_released_point"]
assert all(selected_id_counts[key] == expected for key, expected in expected_selected_counts.items())
temporary.replace(output)
result = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "source": str(source.relative_to(root)).replace("\\", "/"),
    "source_record": "https://zenodo.org/records/10676866",
    "counts": dict(counts),
    "raw_both_proofread_minus_published_pair_table": counts["both_proofread"] - coverage["proofread_connection_synapses"],
    "coordinate_min_nm": coord_min,
    "coordinate_max_nm": coord_max,
    "ids_without_proofread_edges_with_points": len(selected_id_counts),
    "top_20_selected_ids_by_points": selected_id_counts.most_common(20),
    "point_export": str(output.relative_to(root)).replace("\\", "/"),
    "meaning": "Observed published synapse points and segment IDs. An unproofread segment ID is not automatically a missing proofread neurite.",
}
(root / "analysis/synapse_point_audit.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(result, ensure_ascii=False, indent=2))
