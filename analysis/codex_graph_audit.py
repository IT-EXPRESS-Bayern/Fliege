"""Independent checks on the derived Codex FAFB v783 CSR graph and its source."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np


ARRAYS = {
    "nodes.u64": "<u8",
    "offsets.u32": "<u4",
    "targets.u32": "<u4",
    "synapses.u32": "<u4",
    "nt_probs.u8": "u1",
}


def hash_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def source_csv(path: Path) -> dict[str, Any]:
    rows = 0
    synapses = 0
    minimum = None
    regions = Counter()
    nt_rows = Counter()
    nt_synapses = Counter()
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        required = {"pre_root_id", "post_root_id", "neuropil", "syn_count", "nt_type"}
        if not required.issubset(columns):
            raise ValueError(f"Unexpected Codex source schema: {columns}")
        for row in reader:
            rows += 1
            weight = int(row["syn_count"])
            synapses += weight
            minimum = weight if minimum is None else min(minimum, weight)
            regions[row["neuropil"]] += 1
            nt_rows[row["nt_type"] or "(missing)"] += 1
            nt_synapses[row["nt_type"] or "(missing)"] += weight
    return {
        "columns": columns, "rows": rows, "synapse_count_sum": synapses,
        "minimum_row_synapses": minimum,
        "region_rows": dict(regions.most_common()),
        "nt_type_rows": dict(nt_rows.most_common()),
        "nt_type_synapses": dict(nt_synapses.most_common()),
    }


def audit_graph(graph_dir: Path, source_dir: Path, sorted_roots: np.ndarray | None, skip_hashes: bool) -> dict[str, Any]:
    manifest_path = graph_dir / "manifest.json"
    if not manifest_path.is_file():
        return {"status": "missing", "incomplete": True}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    result: dict[str, Any] = {
        "status": "present", "incomplete": skip_hashes,
        "dataset": manifest.get("dataset"),
        "manifest": manifest,
        "files": {},
        "source_warning": "Codex Princeton export is already filtered to neuron pairs with at least five synapses across neuropils; graph min_synapses_per_edge=1 cannot restore omitted pairs.",
        "nt_warning": "Six CSR channels encode synapse-weighted averages of categorical nt_type one-hot labels, not the Zenodo per-synapse/edge transmitter probabilities.",
    }
    for name, expected in manifest.get("files", {}).items():
        path = graph_dir / name
        if not path.is_file():
            result["files"][name] = {"status": "missing", "expected_bytes": expected.get("bytes")}
            result["incomplete"] = True
            continue
        size = path.stat().st_size
        actual = hash_file(path, "sha256") if not skip_hashes else None
        result["files"][name] = {
            "status": "present", "bytes": size, "expected_bytes": expected.get("bytes"),
            "size_matches_manifest": size == expected.get("bytes"),
            "sha256": actual, "sha256_matches_manifest": actual == expected.get("sha256") if actual else None,
        }
        if size != expected.get("bytes") or (actual and actual != expected.get("sha256")):
            result["incomplete"] = True
    if any(result["files"].get(name, {}).get("status") != "present" for name in ARRAYS):
        return result
    arrays = {name: np.fromfile(graph_dir / name, dtype=dtype) for name, dtype in ARRAYS.items()}
    nodes = arrays["nodes.u64"]
    offsets = arrays["offsets.u32"]
    targets = arrays["targets.u32"]
    counts = arrays["synapses.u32"]
    nt = arrays["nt_probs.u8"]
    n, e = len(nodes), len(targets)
    checks = {
        "node_count_matches_manifest": n == manifest.get("node_count"),
        "edge_count_matches_manifest": e == manifest.get("edge_count"),
        "offset_count_is_nodes_plus_one": len(offsets) == n + 1,
        "target_count_equals_synapse_count": e == len(counts),
        "nt_channels_six_per_edge": len(nt) == 6 * e,
        "nodes_strictly_sorted": bool(np.all(nodes[1:] > nodes[:-1])),
        "targets_in_node_range": bool(np.all(targets < n)),
        "minimum_synapses_at_least_one": bool(np.all(counts >= 1)),
        "synapse_sum_matches_manifest": int(counts.sum(dtype=np.uint64)) == manifest.get("synapse_count"),
    }
    if len(offsets) == n + 1:
        checks.update({
            "offset_starts_at_zero": int(offsets[0]) == 0,
            "offset_ends_at_edge_count": int(offsets[-1]) == e,
            "offsets_non_decreasing": bool(np.all(offsets[1:] >= offsets[:-1])),
        })
    if sorted_roots is not None:
        checks["nodes_equal_zenodo_proofread_root_ids"] = bool(np.array_equal(nodes, sorted_roots))
    result["checks"] = checks
    result["graph_stats"] = {
        "nodes": n, "directed_pair_edges": e,
        "synapses_in_graph": int(counts.sum(dtype=np.uint64)),
        "minimum_pair_synapses": int(counts.min()) if e else None,
        "maximum_pair_synapses": int(counts.max()) if e else None,
        "nodes_with_outgoing_edges": int(np.count_nonzero(np.diff(offsets))) if len(offsets) == n + 1 else None,
        "maximum_outgoing_degree": int(np.diff(offsets).max()) if len(offsets) == n + 1 else None,
        "precombined_neuropil_rows": manifest.get("input_rows"),
    }
    if len(nt) == 6 * e:
        channels = nt.reshape(e, 6)
        result["graph_stats"]["nt_channel_min"] = channels.min(axis=0).astype(int).tolist()
        result["graph_stats"]["nt_channel_max"] = channels.max(axis=0).astype(int).tolist()
        result["graph_stats"]["edges_with_no_nt_category"] = int(np.count_nonzero(channels.sum(axis=1) == 0))
    source_path = source_dir / manifest.get("sources", {}).get("connections", {}).get("file", "connections_princeton.csv.gz")
    if source_path.is_file():
        source_info = manifest["sources"]["connections"]
        result["codex_source"] = {
            "file": str(source_path.resolve()), "bytes": source_path.stat().st_size,
            "md5": hash_file(source_path, "md5") if not skip_hashes else None,
            "expected_md5": source_info.get("published_md5"),
            "sha256": hash_file(source_path, "sha256") if not skip_hashes else None,
            "expected_sha256": source_info.get("sha256"),
            **source_csv(source_path),
        }
        result["codex_source"]["md5_matches_published"] = (
            result["codex_source"]["md5"] == source_info.get("published_md5")
            if result["codex_source"]["md5"] else None
        )
        result["codex_source"]["rows_match_graph_manifest"] = (
            result["codex_source"]["rows"] == manifest.get("input_rows")
        )
        result["codex_source"]["synapses_match_graph"] = (
            result["codex_source"]["synapse_count_sum"] == result["graph_stats"]["synapses_in_graph"]
        )
        if result["codex_source"]["md5_matches_published"] is False:
            result["incomplete"] = True
    else:
        result["codex_source"] = {"status": "missing"}
        result["incomplete"] = True
    annotations_path = graph_dir / "annotations.json"
    if annotations_path.is_file():
        records = json.loads(annotations_path.read_text(encoding="utf-8"))
        record_ids = np.array([int(item["id"]) for item in records], dtype=np.uint64)
        result["checks"]["annotation_rows_equal_node_count"] = len(records) == n
        result["checks"]["annotation_ids_equal_node_order"] = bool(np.array_equal(record_ids, nodes))
        result["graph_stats"]["annotation_rows"] = len(records)
    result["checks_all_true"] = all(checks.values())
    if not result["checks_all_true"]:
        result["incomplete"] = True
    return result
