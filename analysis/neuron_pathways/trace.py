"""Shortest directed anatomical paths for source-labelled sensory/output candidates.

This is graph reachability, independent of the dynamical assays and body adapter.
Run: analysis/.venv/Scripts/python.exe analysis/neuron_pathways/trace.py
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import json

import numpy as np
import openpyxl

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
GRAPH = ROOT / "brain/graph-original-v783"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def main():
    manifest = json.loads((GRAPH / "manifest.json").read_text())
    arrays = {}
    for name, dtype in [("nodes.u64", "<u8"), ("offsets.u32", "<u4"), ("targets.u32", "<u4"), ("synapses.u32", "<u4"), ("nt_probs.u8", "u1")]:
        assert sha(GRAPH / name) == manifest["files"][name]["sha256"]
        arrays[name] = np.fromfile(GRAPH / name, dtype=dtype)
    ids, offsets, targets, counts = [arrays[k] for k in ["nodes.u64", "offsets.u32", "targets.u32", "synapses.u32"]]
    nt = arrays["nt_probs.u8"].reshape(-1, 6)
    source_index = np.repeat(np.arange(len(ids), dtype=np.uint32), np.diff(offsets))
    id_index = {str(v): i for i, v in enumerate(ids)}
    annotations = {x["id"]: x for x in json.loads((GRAPH / "annotations.json").read_text())}
    supplement_path = ROOT / "data/research_sources/shiu/derived/shiu_supplement_index.json"
    supplement = json.loads(supplement_path.read_text())
    groups = {name: [] for name in ["JO_CE", "JO_F", "sugar", "water", "bitter"]}
    excluded = []
    for c in supplement["candidates"]:
        category = c["category"]
        group = "JO_CE" if category in ("jon_c", "jon_e") else "JO_F" if category == "jon_f" else {"sugar_grn": "sugar", "water_grn": "water", "bitter_grn": "bitter"}.get(category)
        if group is None:
            continue
        root = c["source_root_id"]
        if root not in id_index:
            excluded.append({"group": group, "root_id": root})
        else:
            groups[group].append(root)
    groups = {k: sorted(set(v)) for k, v in groups.items()}
    readouts = {"aBN1": "720575940630907434", "aDN1_source_l_side_conflict": "720575940616185531", "aDN2_source_l_side_conflict": "720575940629806974", "MN9_right": "720575940660219265", "MN9_left_Tastekin_v783": "720575940618238523"}
    tastekin_path = ROOT / "data/research_sources/other/tastekin/tastekin_2026_cell_table_s1.xlsx"
    tastekin = openpyxl.load_workbook(tastekin_path, read_only=True, data_only=True)
    assert str(tastekin["MNs"]["B69"].value) == readouts["MN9_left_Tastekin_v783"]
    assert tastekin["MNs"]["C69"].value == "L" and tastekin["MNs"]["E69"].value == "MN9"
    assert str(tastekin["MNs"]["B68"].value) == readouts["MN9_right"]
    tastekin.close()
    assert all(root in id_index for root in readouts.values())
    records = []
    summaries = []
    for threshold in (1, 5):
        strong = counts >= threshold
        for output_name, output_root in readouts.items():
            output_index = id_index[output_root]
            distance = np.full(len(ids), -1, dtype=np.int8)
            distance[output_index] = 0
            next_edge = np.full(len(ids), -1, dtype=np.int64)
            frontier = np.zeros(len(ids), dtype=bool)
            frontier[output_index] = True
            for depth in range(1, 5):
                candidates = np.flatnonzero(strong & frontier[targets] & (distance[source_index] < 0))
                if not len(candidates):
                    break
                found, first = np.unique(source_index[candidates], return_index=True)
                distance[found] = depth
                next_edge[found] = candidates[first]
                frontier[:] = False
                frontier[found] = True
            for group, roots in groups.items():
                hops = Counter()
                for input_root in roots:
                    start = id_index[input_root]
                    d = int(distance[start])
                    hops[str(d)] += 1
                    nodes = [input_root] if d >= 0 else []
                    edges = []
                    current = start
                    for _ in range(max(0, d)):
                        edge = int(next_edge[current])
                        dest = int(targets[edge])
                        assert source_index[edge] == current and counts[edge] >= threshold
                        source_root, target_root = str(ids[current]), str(ids[dest])
                        edges.append({"pre": source_root, "post": target_root, "synapse_count": int(counts[edge]), "predicted_transmitter_scores": {name: float(score) / 255 for name, score in zip(manifest["neurotransmitter_order"], nt[edge])}})
                        nodes.append(target_root)
                        current = dest
                    if d >= 0:
                        assert current == output_index and len(nodes) == d + 1
                    labels = [{"root_id": root, "cell_type": annotations[root].get("cell_type", ""), "cell_class": annotations[root].get("cell_class", ""), "side": annotations[root].get("side", "")} for root in nodes]
                    records.append({"input_group": group, "input_root_id": input_root, "readout_name": output_name, "readout_root_id": output_root, "min_synapses_per_edge": threshold, "shortest_hops_within_4": d if d >= 0 else None, "path_nodes": nodes, "path_labels": labels, "path_edges": edges, "path_bottleneck_count": min((x["synapse_count"] for x in edges), default=None)})
                summaries.append({"input_group": group, "readout_name": output_name, "readout_root_id": output_root, "min_synapses_per_edge": threshold, "inputs": len(roots), "reachable_within_4": sum(v for k, v in hops.items() if k != "-1"), "direct": hops["1"], "two_hops": hops["2"], "three_hops": hops["3"], "four_hops": hops["4"], "not_reached_within_4": hops["-1"]})
    with (OUT / "reachability.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summaries[0])); w.writeheader(); w.writerows(summaries)
    (OUT / "example_shortest_paths.json").write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    audit = {"created_utc": datetime.now(timezone.utc).isoformat(), "dataset": manifest["dataset"], "node_count": len(ids), "directed_pairs": len(targets), "source_manifest_sha256": sha(GRAPH / "manifest.json"), "supplement_index_sha256": sha(supplement_path), "all_loaded_graph_arrays_sha256_verified": True, "max_hops": 4, "synapse_thresholds": [1, 5], "input_groups": {k: len(v) for k, v in groups.items()}, "excluded_missing_source_ids": excluded, "readouts": readouts, "summary_rows": len(summaries), "path_records": len(records), "reached_records": sum(r["shortest_hops_within_4"] is not None for r in records), "method": "Backward breadth-first search on the full directed original CSR. One shortest path per source/output is retained; ties choose the first CSR edge, not an optimized or uniquely biological route.", "limitations": ["Anatomical reachability does not imply excitatory drive or a behavioral function.", "No path within four hops does not mean globally disconnected.", "Transmitter scores are source predictions quantized to uint8; receptor effects are unknown.", "Both aDN source names conflict with current side annotation; no lateralized actuation follows.", "MN9 left uses the independently published current v783 Tastekin ID, not a guessed remapping of old Shiu ID."]}
    audit["tastekin_workbook_sha256"] = sha(tastekin_path)
    audit["mn9_source_cells"] = {"right": "MNs!B68:G68", "left": "MNs!B69:G69"}
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
