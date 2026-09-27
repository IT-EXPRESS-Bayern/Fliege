"""Streaming audit of 616 edge-less FAFB v783 roots in the FlyWire LOD1 skeletons.

Run from the project root with: analysis/.venv/Scripts/python.exe analysis/morphology_616/scan.py
The Parquet file is scanned in bounded batches. Only three example neurons are
retained as complete node arrays for the point-to-skeleton coordinate check.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SKELETON = ROOT / "data/flywire_morphology_v783/sk_lod1_783_healed_ds2.parquet"
MISSING = ROOT / "data/research_sources/derived/model_missing_fafb_ids.csv"
STRATA = ROOT / "analysis/reconstruction_candidates_v783/princeton_strata.json"
PRINCETON_POINTS = ROOT / "analysis/reconstruction_candidates_v783/princeton_individual_points_for_616.csv"
BUHMANN_POINTS = ROOT / "data/research_sources/derived/points_for_616_ids_without_proofread_edges.csv"
ZENODO_RECORD = ROOT / "data/flywire_morphology_v783/zenodo_record.json"
R7 = 720575940623940963
EXPECTED_SIZE = 5_355_543_468
EXPECTED_MD5 = "a4c104776f33ec539ef859064c4de3df"
FIELDS = ("node_id", "parent_id", "radius", "x", "y", "z", "neuron")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def md5(path: Path) -> str:
    digest = hashlib.md5()  # Published Zenodo file checksum, not a security use.
    with path.open("rb") as handle:
        while chunk := handle.read(16 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def percentile_summary(values: list[float]) -> dict:
    if not values:
        return {"n": 0, "min": None, "p25": None, "median": None, "p75": None, "p95": None, "max": None}
    a = np.asarray(values, dtype=np.float64)
    return {
        "n": len(values), "min": float(np.min(a)), "p25": float(np.percentile(a, 25)),
        "median": float(np.median(a)), "p75": float(np.percentile(a, 75)),
        "p95": float(np.percentile(a, 95)), "max": float(np.max(a)),
    }


def fresh_stats() -> dict:
    return {
        "nodes": 0, "root_nodes": 0, "radius_negative": 0, "radius_zero": 0,
        "nonfinite_coordinates": 0, "radius_min": math.inf, "radius_max": -math.inf,
        "radius_sum": 0, "x_min": math.inf, "x_max": -math.inf,
        "y_min": math.inf, "y_max": -math.inf, "z_min": math.inf, "z_max": -math.inf,
    }


def update_stats(s: dict, arrays: dict[str, np.ndarray]) -> None:
    n = len(arrays["neuron"])
    if not n:
        return
    s["nodes"] += n
    s["root_nodes"] += int(np.count_nonzero(arrays["parent_id"] == -1))
    radius = arrays["radius"]
    s["radius_negative"] += int(np.count_nonzero(radius < 0))
    s["radius_zero"] += int(np.count_nonzero(radius == 0))
    s["radius_min"] = min(s["radius_min"], int(np.min(radius)))
    s["radius_max"] = max(s["radius_max"], int(np.max(radius)))
    s["radius_sum"] += int(np.sum(radius, dtype=np.int64))
    for axis in ("x", "y", "z"):
        values = arrays[axis]
        finite = np.isfinite(values)
        s["nonfinite_coordinates"] += int(np.count_nonzero(~finite))
        if np.any(finite):
            s[f"{axis}_min"] = min(s[f"{axis}_min"], float(np.min(values[finite])))
            s[f"{axis}_max"] = max(s[f"{axis}_max"], float(np.max(values[finite])))


def point_rows_for_examples(examples: set[int]) -> tuple[list[dict], Counter]:
    points: list[dict] = []
    princeton_count: Counter = Counter()
    for row in read_csv(PRINCETON_POINTS):
        ids = [int(x) for x in row["selected_root_ids"].replace(";", ",").split(",") if x]
        for root in ids:
            princeton_count[root] += 1
            if root not in examples:
                continue
            for role in ("pre", "post"):
                if int(row[f"{role}_root_id"]) == root:
                    points.append({
                        "root_id": root, "source": "Princeton_2025_unfiltered_point",
                        "source_row": row["source_row_number"], "role": role,
                        "x_nm": float(row[f"{role}_x"]), "y_nm": float(row[f"{role}_y"]),
                        "z_nm": float(row[f"{role}_z"]),
                        "partner_proofreading_class": row["partner_proofreading_class"],
                    })
    for row in read_csv(BUHMANN_POINTS):
        for role in ("pre", "post"):
            root = int(row[f"{role}_root_id"])
            if root in examples:
                points.append({
                    "root_id": root, "source": "Buhmann_v783_raw_point",
                    "source_row": row["synapse_id"], "role": role,
                    "x_nm": float(row[f"{role}_x_nm"]), "y_nm": float(row[f"{role}_y_nm"]),
                    "z_nm": float(row[f"{role}_z_nm"]),
                    "partner_proofreading_class": "both_proofread" if row["pre_root_proofread"] == "True" and row["post_root_proofread"] == "True" else "at_least_one_unproofread",
                })
    return points, princeton_count


def example_topology(arrays: dict[str, np.ndarray]) -> tuple[dict, np.ndarray, np.ndarray]:
    ids = arrays["node_id"].astype(np.int64)
    parents = arrays["parent_id"].astype(np.int64)
    xyz = np.column_stack((arrays["x"], arrays["y"], arrays["z"])).astype(np.float64)
    order = np.argsort(ids)
    sorted_ids = ids[order]
    root_mask = parents == -1
    child_idx = np.flatnonzero(~root_mask)
    positions = np.searchsorted(sorted_ids, parents[child_idx])
    valid = positions < len(sorted_ids)
    matching = np.zeros(len(child_idx), dtype=bool)
    matching[valid] = sorted_ids[positions[valid]] == parents[child_idx[valid]]
    children = child_idx[matching]
    ancestor = order[positions[matching]]
    length = np.linalg.norm(xyz[children] - xyz[ancestor], axis=1)
    return {
        "unique_node_ids": int(len(np.unique(ids))),
        "duplicate_node_id_rows": int(len(ids) - len(np.unique(ids))),
        "root_nodes": int(np.count_nonzero(root_mask)),
        "parent_reference_missing": int(np.count_nonzero(~matching)),
        "valid_segments": int(len(children)),
        "total_cable_length_um": float(np.sum(length) / 1000),
        "segment_length_nm": percentile_summary(length.tolist()),
    }, xyz, np.stack((xyz[children], xyz[ancestor]), axis=1)


def point_distance(point: np.ndarray, nodes: np.ndarray, segments: np.ndarray) -> tuple[float, float]:
    # Exemplar-sized arrays only; no whole-dataset nearest-neighbour index.
    node_d2 = np.sum((nodes - point) ** 2, axis=1)
    nearest_node = float(np.sqrt(np.min(node_d2)))
    if len(segments) == 0:
        return nearest_node, nearest_node
    start = segments[:, 0, :]
    vector = segments[:, 1, :] - start
    denominator = np.einsum("ij,ij->i", vector, vector)
    fraction = np.divide(np.einsum("ij,ij->i", point - start, vector), denominator,
                         out=np.zeros(len(segments)), where=denominator > 0)
    fraction = np.clip(fraction, 0, 1)
    projection = start + fraction[:, None] * vector
    nearest_segment = float(np.sqrt(np.min(np.sum((projection - point) ** 2, axis=1))))
    return nearest_node, nearest_segment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-md5", action="store_true", help="Rehash 5.36 GB source before scanning")
    parser.add_argument("--batch-size", type=int, default=262_144)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if SKELETON.stat().st_size != EXPECTED_SIZE:
        raise RuntimeError("Skeleton file size differs from official Zenodo record")
    if args.verify_md5 and md5(SKELETON) != EXPECTED_MD5:
        raise RuntimeError("Skeleton MD5 differs from official Zenodo record")
    official = json.loads(ZENODO_RECORD.read_text(encoding="utf-8"))
    official_entry = next(f for f in official["files"] if f["key"] == SKELETON.name)
    if official_entry["checksum"] != f"md5:{EXPECTED_MD5}":
        raise RuntimeError("Pinned MD5 differs from local official Zenodo metadata")

    roots = read_csv(MISSING)
    root_ids = [int(r["root_id"]) for r in roots]
    if len(root_ids) != 616 or len(set(root_ids)) != 616:
        raise RuntimeError("Expected exactly 616 distinct missing roots")
    strata = json.loads(STRATA.read_text(encoding="utf-8"))
    princeton_only = set(map(int, strata["new_detector_only_root_ids"]))
    if len(princeton_only) != 195 or not princeton_only.issubset(root_ids):
        raise RuntimeError("Expected 195 Princeton-only roots within the 616")
    all_points = read_csv(PRINCETON_POINTS)
    all_point_counts = Counter()
    for row in all_points:
        all_point_counts.update(int(x) for x in row["selected_root_ids"].replace(";", ",").split(",") if x)
    example_ids = {R7} | {root for root, _ in sorted(
        ((root, all_point_counts[root]) for root in princeton_only),
        key=lambda pair: (-pair[1], pair[0]))[:2]}
    point_rows, princeton_counts = point_rows_for_examples(example_ids)
    parquet = pq.ParquetFile(SKELETON)
    if parquet.schema_arrow.remove_metadata().names != list(FIELDS):
        raise RuntimeError("Unexpected skeleton schema")
    metadata = parquet.schema_arrow.metadata or {}
    meta_coverage = {root: (f"{root}:id".encode() in metadata) for root in root_ids}
    units = Counter((metadata.get(f"{root}:units".encode()) or b"MISSING").decode("utf-8") for root in root_ids)
    stats = {root: fresh_stats() for root in root_ids}
    example_parts: dict[int, dict[str, list[np.ndarray]]] = {
        root: {field: [] for field in FIELDS if field != "neuron"} for root in example_ids}
    target_arrow = pa.array(root_ids, type=pa.int64())
    scanned = 0
    matched = 0
    for group in range(parquet.num_row_groups):
        for batch in parquet.iter_batches(row_groups=[group], batch_size=args.batch_size, columns=list(FIELDS)):
            scanned += batch.num_rows
            mask = pc.is_in(batch.column("neuron"), value_set=target_arrow)
            indices = np.flatnonzero(mask.to_numpy(zero_copy_only=False))
            if not len(indices):
                continue
            matched += len(indices)
            subset = {field: batch.column(field).to_numpy(zero_copy_only=False)[indices] for field in FIELDS}
            ids = subset["neuron"]
            for root in np.unique(ids):
                root = int(root)
                sel = ids == root
                selected = {field: values[sel] for field, values in subset.items()}
                update_stats(stats[root], selected)
                if root in example_parts:
                    for field in example_parts[root]:
                        example_parts[root][field].append(selected[field].copy())
        print(f"row_group={group + 1}/{parquet.num_row_groups} rows_scanned={scanned:,} target_rows={matched:,}", flush=True)

    coverage_rows = []
    for row in roots:
        root = int(row["root_id"])
        s = stats[root]
        available = s["nodes"] > 0
        result = dict(row)
        result.update({
            "in_schema_metadata": meta_coverage[root],
            "is_R7_priority": root == R7,
            "is_Princeton_only_195": root in princeton_only,
            "Princeton_individual_points": princeton_counts[root],
            "skeleton_nodes": s["nodes"], "skeleton_root_nodes": s["root_nodes"],
            "radius_min_nm": s["radius_min"] if available else "",
            "radius_mean_nm": round(s["radius_sum"] / s["nodes"], 3) if available else "",
            "radius_max_nm": s["radius_max"] if available else "",
            "radius_zero_rows": s["radius_zero"], "radius_negative_rows": s["radius_negative"],
            "nonfinite_coordinate_cells": s["nonfinite_coordinates"],
        })
        for axis in ("x", "y", "z"):
            result[f"{axis}_min_nm"] = round(s[f"{axis}_min"], 3) if available else ""
            result[f"{axis}_max_nm"] = round(s[f"{axis}_max"], 3) if available else ""
            result[f"{axis}_span_um"] = round((s[f"{axis}_max"] - s[f"{axis}_min"]) / 1000, 3) if available else ""
        result["bounding_box_diagonal_um"] = round(math.sqrt(sum(
            (s[f"{axis}_max"] - s[f"{axis}_min"]) ** 2 for axis in ("x", "y", "z"))) / 1000, 3) if available else ""
        coverage_rows.append(result)
    write_csv(OUT / "coverage_616.csv", coverage_rows, list(coverage_rows[0]))
    node_limits = np.percentile([int(r["skeleton_nodes"]) for r in coverage_rows], [1, 99])
    diagonal_limits = np.percentile([float(r["bounding_box_diagonal_um"]) for r in coverage_rows], [1, 99])
    extremes = []
    for row in coverage_rows:
        flags = []
        if int(row["skeleton_nodes"]) <= node_limits[0]:
            flags.append("bottom_1pct_node_count")
        if int(row["skeleton_nodes"]) >= node_limits[1]:
            flags.append("top_1pct_node_count")
        if float(row["bounding_box_diagonal_um"]) <= diagonal_limits[0]:
            flags.append("bottom_1pct_bbox_diagonal")
        if float(row["bounding_box_diagonal_um"]) >= diagonal_limits[1]:
            flags.append("top_1pct_bbox_diagonal")
        if flags:
            extremes.append(dict(row, distribution_tail_flags=";".join(flags)))
    write_csv(OUT / "geometry_extremes.csv", extremes,
              ["distribution_tail_flags"] + list(coverage_rows[0]))
    ordered = sorted(coverage_rows, key=lambda row: (
        0 if row["is_R7_priority"] else 1 if row["is_Princeton_only_195"] else 2,
        -int(row["Princeton_individual_points"]), int(row["skeleton_nodes"]), int(row["root_id"])))
    for rank, row in enumerate(ordered, 1):
        row["review_rank"] = rank
        row["priority_reason"] = "R7 focal case" if row["is_R7_priority"] else "Princeton-only point coverage" if row["is_Princeton_only_195"] else "remaining missing-root morphology"
    write_csv(OUT / "review_priority_616.csv", ordered, ["review_rank", "priority_reason"] + list(coverage_rows[0]))

    topology = {}
    distance_rows = []
    for root in sorted(example_ids):
        arrays = {field: np.concatenate(parts) for field, parts in example_parts[root].items()}
        topology[str(root)], nodes, segments = example_topology(arrays)
        for point in point_rows:
            if point["root_id"] != root:
                continue
            dnode, dseg = point_distance(np.array((point["x_nm"], point["y_nm"], point["z_nm"])), nodes, segments)
            distance_rows.append(dict(point, nearest_node_nm=round(dnode, 3), nearest_segment_nm=round(dseg, 3)))
    write_csv(OUT / "point_distance_exemplars.csv", distance_rows, list(distance_rows[0]) if distance_rows else [])
    distance_summary = {}
    for root in sorted(example_ids):
        distance_summary[str(root)] = {}
        for source in ("Buhmann_v783_raw_point", "Princeton_2025_unfiltered_point"):
            vals = [r["nearest_segment_nm"] for r in distance_rows if r["root_id"] == root and r["source"] == source]
            distance_summary[str(root)][source] = dict(
                percentile_summary(vals),
                within_0_5_um=sum(v <= 500 for v in vals),
                within_1_um=sum(v <= 1000 for v in vals),
                within_2_um=sum(v <= 2000 for v in vals),
            )
    audit = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(SKELETON.relative_to(ROOT)).replace("\\", "/"),
        "official_record_url": "https://zenodo.org/records/10877326",
        "official_md5": EXPECTED_MD5,
        "md5_rechecked_this_run": bool(args.verify_md5),
        "file_size_bytes": SKELETON.stat().st_size,
        "parquet_rows": parquet.metadata.num_rows,
        "parquet_row_groups": parquet.num_row_groups,
        "rows_scanned": scanned,
        "target_rows_found": matched,
        "target_id_count": len(root_ids),
        "ids_present_in_metadata": sum(meta_coverage.values()),
        "ids_with_nodes": sum(s["nodes"] > 0 for s in stats.values()),
        "princeton_only_id_count": len(princeton_only),
        "princeton_only_ids_with_nodes": sum(stats[root]["nodes"] > 0 for root in princeton_only),
        "units_metadata": dict(units),
        "nodes_per_id": percentile_summary([s["nodes"] for s in stats.values()]),
        "bounding_box_diagonal_um": percentile_summary([float(r["bounding_box_diagonal_um"]) for r in coverage_rows if r["bounding_box_diagonal_um"] != ""]),
        "radius_negative_rows": sum(s["radius_negative"] for s in stats.values()),
        "radius_zero_rows": sum(s["radius_zero"] for s in stats.values()),
        "nonfinite_coordinate_cells": sum(s["nonfinite_coordinates"] for s in stats.values()),
        "root_nodes_count_distribution": dict(sorted(Counter(s["root_nodes"] for s in stats.values()).items())),
        "geometry_tail_thresholds": {
            "node_count_p1": float(node_limits[0]), "node_count_p99": float(node_limits[1]),
            "bbox_diagonal_um_p1": float(diagonal_limits[0]),
            "bbox_diagonal_um_p99": float(diagonal_limits[1]),
            "flagged_ids": len(extremes),
        },
        "example_ids": sorted(example_ids),
        "example_topology": topology,
        "point_to_skeleton_example_summary": distance_summary,
        "interpretation": "Morphology and coordinate compatibility only; proximity cannot establish synapses, direction, or physiological activity.",
    }
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: audit[k] for k in ("ids_with_nodes", "target_rows_found", "princeton_only_ids_with_nodes", "example_ids")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
