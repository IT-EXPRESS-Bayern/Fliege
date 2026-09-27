"""Rank cell-type links for v783 IDs absent from the proofread pair graph.

These are hypotheses at cell-type level. The script never fabricates an exact
root-ID-to-root-ID edge or mutates the measured graph.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parents[1]
graph = root / "brain/graph-original-v783"
node_ids = np.fromfile(graph / "nodes.u64", dtype="<u8")
offsets = np.fromfile(graph / "offsets.u32", dtype="<u4")
targets = np.memmap(graph / "targets.u32", dtype="<u4", mode="r")
synapses = np.memmap(graph / "synapses.u32", dtype="<u4", mode="r")

annotations = {}
with (root / "data/flywire_annotations_v2.1.0/Supplemental_file1_neuron_annotations.tsv").open(
    "r", encoding="utf-8-sig", newline=""
) as file:
    for row in csv.DictReader(file, delimiter="\t"):
        annotations[int(row["root_id"])] = row
types = np.array([annotations[int(r)].get("cell_type", "") for r in node_ids], dtype=object)
sides = np.array([annotations[int(r)].get("side", "") for r in node_ids], dtype=object)

coverage = {}
with (root / "data/research_sources/derived/proofread_synapse_coverage_by_neuron.csv").open(
    "r", encoding="utf-8", newline=""
) as file:
    for row in csv.DictReader(file):
        coverage[int(row["root_id"])] = row
missing = []
with (root / "data/research_sources/derived/model_missing_fafb_ids.csv").open(
    "r", encoding="utf-8", newline=""
) as file:
    missing = list(csv.DictReader(file))
assert len(missing) == 616

visual = {}
with (root / "data/research_sources/other/visual_system/data/type_to_type_connection_and_synapse_counts.csv").open(
    "r", encoding="utf-8", newline=""
) as file:
    for row in csv.DictReader(file):
        visual[(row["from type"], row["to type"])] = row
visual_sources = {key[0] for key in visual}

missing_groups = {(row["cell_type"], row["side"]) for row in missing if row["cell_type"] and row["side"]}
peer_indexes = defaultdict(list)
for i in range(len(node_ids)):
    key = (types[i], sides[i])
    if key in missing_groups and offsets[i + 1] > offsets[i]:
        peer_indexes[key].append(i)

group_results = {}
for group, peers in peer_indexes.items():
    incidence = Counter()
    synapse_sum = Counter()
    for peer in peers:
        start, end = int(offsets[peer]), int(offsets[peer + 1])
        local = Counter()
        for target_idx, weight in zip(targets[start:end], synapses[start:end]):
            target_type = types[int(target_idx)]
            if target_type:
                local[target_type] += int(weight)
        for target_type, count in local.items():
            incidence[target_type] += 1
            synapse_sum[target_type] += count
    ranked = sorted(incidence, key=lambda target_type: (
        incidence[target_type] / len(peers), synapse_sum[target_type]
    ), reverse=True)
    group_results[group] = (len(peers), incidence, synapse_sum, ranked)

output = root / "data/research_sources/derived/missing_neuron_type_link_hypotheses.csv"
rows = []
for row in missing:
    root_id = int(row["root_id"])
    group = (row["cell_type"], row["side"])
    all_pre = int(coverage[root_id]["all_pre_points"])
    all_post = int(coverage[root_id]["all_post_points"])
    peer_count, incidence, synapse_sum, ranked = group_results.get(group, (0, {}, {}, []))
    if peer_count < 10:
        rows.append({
            "root_id": str(root_id), "cell_type": row["cell_type"], "side": row["side"],
            "released_pre_points": all_pre, "released_post_points": all_post,
            "connected_homologs_same_type_side": peer_count, "candidate_target_type": "",
            "homologs_with_target_type": "", "homolog_support_fraction": "",
            "synapses_in_homologs": "", "published_visual_type_connections": "",
            "published_visual_type_synapses": "",
            "status": "insufficient_same_type_side_homologs",
        })
        continue
    kept = 0
    for target_type in ranked:
        if incidence[target_type] < 3 or incidence[target_type] / peer_count < 0.05:
            continue
        if row["cell_class"] == "visual" and row["cell_type"] in visual_sources \
                and (row["cell_type"], target_type) not in visual:
            continue
        published = visual.get((row["cell_type"], target_type), {})
        rows.append({
            "root_id": str(root_id), "cell_type": row["cell_type"], "side": row["side"],
            "released_pre_points": all_pre, "released_post_points": all_post,
            "connected_homologs_same_type_side": peer_count,
            "candidate_target_type": target_type,
            "homologs_with_target_type": incidence[target_type],
            "homolog_support_fraction": round(incidence[target_type] / peer_count, 4),
            "synapses_in_homologs": synapse_sum[target_type],
            "published_visual_type_connections": published.get("connections total", ""),
            "published_visual_type_synapses": published.get("synapses total", ""),
            "status": "type_level_hypothesis_only",
        })
        kept += 1
        if kept == 5:
            break
    if kept == 0:
        rows.append({
            "root_id": str(root_id), "cell_type": row["cell_type"], "side": row["side"],
            "released_pre_points": all_pre, "released_post_points": all_post,
            "connected_homologs_same_type_side": peer_count, "candidate_target_type": "",
            "homologs_with_target_type": "", "homolog_support_fraction": "",
            "synapses_in_homologs": "", "published_visual_type_connections": "",
            "published_visual_type_synapses": "", "status": "no_supported_target_type",
        })

with output.open("w", encoding="utf-8", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
summary = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "source_missing_ids": "data/research_sources/derived/model_missing_fafb_ids.csv",
    "source_local_graph": "brain/graph-original-v783/manifest.json",
    "source_visual_type_matrix": "data/research_sources/other/visual_system/data/type_to_type_connection_and_synapse_counts.csv",
    "method": "Same cell_type and side among graph-connected homologs; outgoing target-type incidence, requiring >=10 peers and >=3 peers with target and >=5% prevalence; visual target types also require support in the published visual type matrix; top 5 per missing ID.",
    "missing_ids": len(missing),
    "candidate_rows": len(rows),
    "ids_with_type_hypotheses": len({row["root_id"] for row in rows if row["status"] == "type_level_hypothesis_only"}),
    "ids_without_sufficient_homologs": len({row["root_id"] for row in rows if row["status"] == "insufficient_same_type_side_homologs"}),
    "ids_with_observed_released_points": sum(
        int(coverage[int(row["root_id"])]["all_pre_points"]) + int(coverage[int(row["root_id"])]["all_post_points"]) > 0
        for row in missing
    ),
    "output_csv": str(output.relative_to(root)).replace("\\", "/"),
    "caution": "A target cell type is not an exact synaptic partner. Support fraction is homolog prevalence, not calibrated confidence or a biological probability. No edge is added to the measured graph.",
}
(root / "analysis/missing_neuron_type_link_audit.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(summary, ensure_ascii=False, indent=2))
