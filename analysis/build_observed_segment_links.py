"""Aggregate released v783 synapse points touching 616 disconnected proofread IDs.

Run after ``audit_synapse_points.py`` has exported and audited the point CSV.
Two separate outputs preserve the evidence classes: released contacts to
unproofread segments (tier B) and verified raw proofread-to-proofread points
missing from the published aggregate edge table (tier A_raw_exception).
Neither output modifies the measured CSR graph. An unproofread segment is not
reidentified as a neuron.

Usage::

    python analysis/build_observed_segment_links.py

The CSV preserves exact integer IDs as decimal strings. Its ``synapse_ids``
column lists every released point supporting each directed pair and neuropil.
The detector scores describe the published point calls; they are not calibrated
probabilities of an edge or physiological synaptic weights.
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
import pyarrow.ipc as ipc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POINTS = ROOT / "data/research_sources/derived/points_for_616_ids_without_proofread_edges.csv"
DEFAULT_COVERAGE = ROOT / "data/research_sources/derived/proofread_synapse_coverage_by_neuron.csv"
DEFAULT_ROOT_IDS = ROOT / "data/flywire_fafb_v783/proofread_root_ids_783.npy"
DEFAULT_PUBLISHED_EDGES = ROOT / "data/flywire_fafb_v783/proofread_connections_783.feather"
DEFAULT_POINT_AUDIT = ROOT / "analysis/synapse_point_audit.json"
DEFAULT_ZENODO_RECORD = ROOT / "data/flywire_fafb_v783/zenodo_record.json"
DEFAULT_OUTPUT = ROOT / "data/research_sources/derived/observed_segment_links_for_616.csv"
DEFAULT_AUDIT = ROOT / "analysis/observed_segment_links_audit.json"
DEFAULT_RAW_OUTPUT = ROOT / "data/research_sources/derived/observed_raw_proofread_edge_exceptions_for_616.csv"
DEFAULT_RAW_AUDIT = ROOT / "analysis/observed_raw_proofread_edge_exceptions_audit.json"
SOURCE_RECORD = "https://zenodo.org/records/10676866"
POINT_FIELDS = (
    "synapse_id", "pre_root_id", "post_root_id", "pre_root_proofread",
    "post_root_proofread", "pre_x_nm", "pre_y_nm", "pre_z_nm", "post_x_nm",
    "post_y_nm", "post_z_nm", "cleft_score", "connection_score", "neuropil",
)
COORD_FIELDS = ("pre_x_nm", "pre_y_nm", "pre_z_nm", "post_x_nm", "post_y_nm", "post_z_nm")
OUTPUT_FIELDS = (
    "evidence_tier", "pre_root_id", "post_root_id", "proofread_root_id",
    "unproofread_segment_id", "direction", "neuropil", "synapse_count",
    "synapse_ids", "cleft_score_min", "cleft_score_mean", "cleft_score_max",
    "connection_score_min", "connection_score_mean", "connection_score_max",
    "pre_centroid_x_nm", "pre_centroid_y_nm", "pre_centroid_z_nm",
    "post_centroid_x_nm", "post_centroid_y_nm", "post_centroid_z_nm",
)
RAW_OUTPUT_FIELDS = (
    "evidence_tier", "pre_root_id", "post_root_id", "neuropil", "synapse_count",
    "synapse_ids", "published_pair_region_status", "cleft_score_min",
    "cleft_score_mean", "cleft_score_max", "connection_score_min",
    "connection_score_mean", "connection_score_max", "pre_centroid_x_nm",
    "pre_centroid_y_nm", "pre_centroid_z_nm", "post_centroid_x_nm",
    "post_centroid_y_nm", "post_centroid_z_nm",
)


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def integer(row: dict[str, str], field: str, line_no: int) -> int:
    try:
        value = int(row[field])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Line {line_no}: invalid integer in {field!r}") from error
    return value


def finite_score(row: dict[str, str], field: str, line_no: int) -> float:
    try:
        value = float(row[field])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Line {line_no}: invalid numeric score in {field!r}") from error
    if not math.isfinite(value):
        raise ValueError(f"Line {line_no}: non-finite score in {field!r}")
    return value


def positive_id(row: dict[str, str], field: str, line_no: int) -> int:
    value = integer(row, field, line_no)
    if value <= 0:
        raise ValueError(f"Line {line_no}: {field} must be a positive ID")
    return value


def boolean(row: dict[str, str], field: str, line_no: int) -> bool:
    value = row.get(field)
    if value not in ("True", "False"):
        raise ValueError(f"Line {line_no}: {field} must be 'True' or 'False'")
    return value == "True"


def load_disconnected_ids(path: Path) -> tuple[dict[int, tuple[int, int]], int]:
    disconnected: dict[int, tuple[int, int]] = {}
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        required = {
            "root_id", "all_pre_points", "all_post_points",
            "aggregated_table_pre_points", "aggregated_table_post_points",
        }
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Coverage CSV missing {sorted(required - set(reader.fieldnames or []))}")
        for line_no, row in enumerate(reader, 2):
            rid = positive_id(row, "root_id", line_no)
            if integer(row, "aggregated_table_pre_points", line_no) + integer(
                row, "aggregated_table_post_points", line_no
            ):
                continue
            if rid in disconnected:
                raise ValueError(f"Duplicate disconnected root ID {rid} in coverage CSV")
            pre = integer(row, "all_pre_points", line_no)
            post = integer(row, "all_post_points", line_no)
            if pre < 0 or post < 0:
                raise ValueError(f"Negative point count for {rid} in coverage CSV")
            disconnected[rid] = (pre, post)
    if len(disconnected) != 616:
        raise ValueError(f"Expected 616 disconnected proofread IDs, found {len(disconnected)}")
    return disconnected, sum(pre + post for pre, post in disconnected.values())


def source_file_record(path: Path) -> dict[str, object]:
    record = json.loads(path.read_text(encoding="utf-8"))
    for item in record.get("files", []):
        if item.get("key") == "flywire_synapses_783.feather":
            return {
                "file": "data/flywire_fafb_v783/flywire_synapses_783.feather",
                "zenodo_md5": item.get("checksum"),
                "zenodo_bytes": item.get("size"),
            }
    raise ValueError("Zenodo record has no flywire_synapses_783.feather entry")


def common_group_fields(group: dict[str, object]) -> dict[str, object]:
    count = len(group["synapse_ids"])
    return {
        "synapse_count": count,
        "synapse_ids": ";".join(map(str, sorted(group["synapse_ids"]))),
        "cleft_score_min": group["cleft_min"],
        "cleft_score_mean": f"{group['cleft_sum'] / count:.6f}",
        "cleft_score_max": group["cleft_max"],
        "connection_score_min": group["connection_min"],
        "connection_score_mean": f"{group['connection_sum'] / count:.6f}",
        "connection_score_max": group["connection_max"],
        **{
            field.replace("_x_nm", "_centroid_x_nm")
            .replace("_y_nm", "_centroid_y_nm")
            .replace("_z_nm", "_centroid_z_nm"):
            f"{group['coordinate_sums'][field] / count:.3f}"
            for field in COORD_FIELDS
        },
    }


def verify_raw_keys_absent_from_published_table(
    path: Path, raw_keys: set[tuple[int, int, str]]
) -> dict[str, int]:
    """Stream the official pair-by-neuropil table and require zero exact matches."""
    if not path.is_file():
        raise SystemExit(f"Published edge table is missing: {path}")
    found: dict[tuple[int, int, str], int] = {}
    rows_scanned = 0
    common_roots = set.intersection(*(set((pre, post)) for pre, post, _ in raw_keys))
    pre_candidates = np.array(sorted({key[0] for key in raw_keys}), dtype=np.int64)
    post_candidates = np.array(sorted({key[1] for key in raw_keys}), dtype=np.int64)
    with pa.memory_map(str(path), "r") as source:
        reader = ipc.open_file(source)
        required = {"pre_pt_root_id", "post_pt_root_id", "neuropil", "syn_count"}
        if not required.issubset(reader.schema.names):
            raise ValueError(f"Published edge schema missing {sorted(required - set(reader.schema.names))}")
        for batch_index in range(reader.num_record_batches):
            batch = reader.get_batch(batch_index)
            rows_scanned += batch.num_rows
            pre = batch.column(batch.schema.get_field_index("pre_pt_root_id")).to_numpy(zero_copy_only=False)
            post = batch.column(batch.schema.get_field_index("post_pt_root_id")).to_numpy(zero_copy_only=False)
            if common_roots:
                root = next(iter(common_roots))
                candidate_mask = (pre == root) | (post == root)
            else:
                candidate_mask = np.isin(pre, pre_candidates) & np.isin(post, post_candidates)
            positions = np.flatnonzero(candidate_mask)
            if not len(positions):
                continue
            names = batch.column(batch.schema.get_field_index("neuropil")).take(pa.array(positions)).to_pylist()
            counts = batch.column(batch.schema.get_field_index("syn_count")).take(pa.array(positions)).to_pylist()
            for index, neuropil, count in zip(positions, names, counts):
                key = (int(pre[index]), int(post[index]), neuropil or "")
                if key in raw_keys:
                    found[key] = found.get(key, 0) + int(count)
    if found:
        sample = [(str(pre), str(post), region, count) for (pre, post, region), count in list(found.items())[:10]]
        raise ValueError(f"Raw proofread keys already occur in the published pair table: {sample}")
    return {"published_pair_region_rows_scanned": rows_scanned,
            "raw_pair_region_keys_checked": len(raw_keys),
            "raw_pair_region_keys_found": len(found)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--points", type=Path, default=DEFAULT_POINTS)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--root-ids", type=Path, default=DEFAULT_ROOT_IDS)
    parser.add_argument("--published-edges", type=Path, default=DEFAULT_PUBLISHED_EDGES)
    parser.add_argument("--point-audit", type=Path, default=DEFAULT_POINT_AUDIT)
    parser.add_argument("--zenodo-record", type=Path, default=DEFAULT_ZENODO_RECORD)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--raw-out", type=Path, default=DEFAULT_RAW_OUTPUT)
    parser.add_argument("--raw-audit", type=Path, default=DEFAULT_RAW_AUDIT)
    args = parser.parse_args()

    for path in (args.points, args.coverage, args.root_ids, args.point_audit,
                 args.zenodo_record, args.published_edges):
        if not path.is_file():
            raise SystemExit(f"Required verified input is missing: {path}")
    point_audit = json.loads(args.point_audit.read_text(encoding="utf-8"))
    if point_audit.get("point_export") != relative(args.points):
        raise ValueError("Point-audit export path does not match input CSV")
    if point_audit.get("source_record") != SOURCE_RECORD:
        raise ValueError("Point-audit source is not the pinned FlyWire Zenodo record")
    expected_from_audit = point_audit.get("counts", {}).get("selected_points")
    if not isinstance(expected_from_audit, int):
        raise ValueError("Point audit has no integer selected_points count")

    disconnected, expected_from_coverage = load_disconnected_ids(args.coverage)
    official_ids = np.load(args.root_ids).astype(np.int64)
    if len(official_ids) != len(set(map(int, official_ids))):
        raise ValueError("Official proofread root array contains duplicate IDs")
    official = set(map(int, official_ids))
    if not set(disconnected).issubset(official):
        raise ValueError("Disconnected ID not present in official proofread root array")
    if expected_from_audit != expected_from_coverage:
        raise ValueError(
            f"Point audit expects {expected_from_audit} points, coverage expects {expected_from_coverage}"
        )

    groups: dict[tuple[int, int, str, str], dict[str, object]] = {}
    raw_groups: dict[tuple[int, int, str], dict[str, object]] = {}
    observed_pre = Counter()
    observed_post = Counter()
    direction_counts = Counter()
    raw_direction_counts = Counter()
    neuropil_counts = Counter()
    unique_synapse_ids: set[int] = set()
    unique_segment_ids: set[int] = set()
    coordinate_min: dict[str, int | None] = {field: None for field in COORD_FIELDS}
    coordinate_max: dict[str, int | None] = {field: None for field in COORD_FIELDS}
    coordinate_zero = Counter()
    coordinate_negative = Counter()
    score_min: dict[str, float | None] = {key: None for key in ("cleft_score", "connection_score")}
    score_max: dict[str, float | None] = {key: None for key in score_min}
    connection_score_negative = 0
    separation_min: float | None = None
    separation_max: float | None = None
    separation_sum = 0.0
    separation_over_10000_nm = 0
    rows = 0

    with args.points.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if not set(POINT_FIELDS).issubset(reader.fieldnames or []):
            raise ValueError(f"Point CSV missing {sorted(set(POINT_FIELDS) - set(reader.fieldnames or []))}")
        for line_no, row in enumerate(reader, 2):
            rows += 1
            synapse_id = positive_id(row, "synapse_id", line_no)
            if synapse_id in unique_synapse_ids:
                raise ValueError(f"Duplicate synapse ID {synapse_id} in point export")
            unique_synapse_ids.add(synapse_id)
            pre = positive_id(row, "pre_root_id", line_no)
            post = positive_id(row, "post_root_id", line_no)
            pre_proofread = boolean(row, "pre_root_proofread", line_no)
            post_proofread = boolean(row, "post_root_proofread", line_no)
            if pre_proofread != (pre in official) or post_proofread != (post in official):
                raise ValueError(f"Line {line_no}: proofread flags disagree with official root array")
            selected_pre = pre in disconnected
            selected_post = post in disconnected
            if selected_pre == selected_post:
                raise ValueError(
                    f"Line {line_no}: expected exactly one of the 616 IDs in each point"
                )
            if selected_pre:
                observed_pre[pre] += 1
            else:
                observed_post[post] += 1
            raw_proofread_pair = pre_proofread and post_proofread
            if raw_proofread_pair:
                raw_direction_counts["selected_id_is_pre" if selected_pre else "selected_id_is_post"] += 1
            else:
                if selected_pre:
                    proofread_id, segment_id, direction = pre, post, "proofread_to_segment"
                else:
                    proofread_id, segment_id, direction = post, pre, "segment_to_proofread"
                unique_segment_ids.add(segment_id)
                direction_counts[direction] += 1
            neuropil = row["neuropil"] or ""
            neuropil_counts[neuropil] += 1

            cleft = finite_score(row, "cleft_score", line_no)
            connection = finite_score(row, "connection_score", line_no)
            if cleft < 50:
                raise ValueError(f"Line {line_no}: cleft score {cleft} below the release threshold 50")
            if connection < 0:
                connection_score_negative += 1
            for name, value in (("cleft_score", cleft), ("connection_score", connection)):
                score_min[name] = value if score_min[name] is None else min(score_min[name], value)
                score_max[name] = value if score_max[name] is None else max(score_max[name], value)

            coords = {field: integer(row, field, line_no) for field in COORD_FIELDS}
            for name, value in coords.items():
                coordinate_min[name] = value if coordinate_min[name] is None else min(coordinate_min[name], value)
                coordinate_max[name] = value if coordinate_max[name] is None else max(coordinate_max[name], value)
                coordinate_zero[name] += value == 0
                coordinate_negative[name] += value < 0
            separation = math.dist(
                (coords[f"pre_{axis}_nm"] for axis in "xyz"),
                (coords[f"post_{axis}_nm"] for axis in "xyz"),
            )
            separation_min = separation if separation_min is None else min(separation_min, separation)
            separation_max = separation if separation_max is None else max(separation_max, separation)
            separation_sum += separation
            separation_over_10000_nm += separation > 10_000

            key = (pre, post, neuropil) if raw_proofread_pair else (
                proofread_id, segment_id, direction, neuropil
            )
            selected_groups = raw_groups if raw_proofread_pair else groups
            if key not in selected_groups:
                selected_groups[key] = {
                    "synapse_ids": [], "cleft_sum": 0, "cleft_min": cleft,
                    "cleft_max": cleft, "connection_sum": 0,
                    "connection_min": connection, "connection_max": connection,
                    "coordinate_sums": {field: 0 for field in COORD_FIELDS},
                }
            group = selected_groups[key]
            group["synapse_ids"].append(synapse_id)
            group["cleft_sum"] += cleft
            group["cleft_min"] = min(group["cleft_min"], cleft)
            group["cleft_max"] = max(group["cleft_max"], cleft)
            group["connection_sum"] += connection
            group["connection_min"] = min(group["connection_min"], connection)
            group["connection_max"] = max(group["connection_max"], connection)
            for name, value in coords.items():
                group["coordinate_sums"][name] += value

    if rows != expected_from_coverage:
        raise ValueError(f"Point export has {rows} rows, expected {expected_from_coverage}")
    for rid, (pre, post) in disconnected.items():
        if observed_pre[rid] != pre or observed_post[rid] != post:
            raise ValueError(
                f"Per-ID mismatch for {rid}: observed pre/post "
                f"{observed_pre[rid]}/{observed_post[rid]}, expected {pre}/{post}"
            )
    raw_points = sum(raw_direction_counts.values())
    segment_points = sum(direction_counts.values())
    if segment_points + raw_points != rows or len(unique_synapse_ids) != rows:
        raise ValueError("Point count or synapse ID uniqueness check failed")
    expected_raw_global_difference = point_audit.get("raw_both_proofread_minus_published_pair_table")
    if not isinstance(expected_raw_global_difference, int) or raw_points != expected_raw_global_difference:
        raise ValueError(
            f"Observed {raw_points} selected raw proofread points, but upstream global "
            f"raw-minus-published count is {expected_raw_global_difference}"
        )
    published_key_check = verify_raw_keys_absent_from_published_table(
        args.published_edges, set(raw_groups)
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp_output = args.out.with_name(args.out.name + ".partial")
    with tmp_output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for (proofread_id, segment_id, direction, neuropil), group in sorted(
            groups.items(), key=lambda item: (item[0][0], item[0][2], item[0][1], item[0][3])
        ):
            pre, post = (
                (proofread_id, segment_id)
                if direction == "proofread_to_segment" else (segment_id, proofread_id)
            )
            writer.writerow({
                "evidence_tier": "B_observed_point_unproofread_partner",
                "pre_root_id": str(pre),
                "post_root_id": str(post),
                "proofread_root_id": str(proofread_id),
                "unproofread_segment_id": str(segment_id),
                "direction": direction,
                "neuropil": neuropil,
                **common_group_fields(group),
            })
    tmp_output.replace(args.out)

    args.raw_out.parent.mkdir(parents=True, exist_ok=True)
    tmp_raw_output = args.raw_out.with_name(args.raw_out.name + ".partial")
    with tmp_raw_output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=RAW_OUTPUT_FIELDS)
        writer.writeheader()
        for (pre, post, neuropil), group in sorted(raw_groups.items()):
            writer.writerow({
                "evidence_tier": "A_raw_exception",
                "pre_root_id": str(pre),
                "post_root_id": str(post),
                "neuropil": neuropil,
                "published_pair_region_status": "absent_verified",
                **common_group_fields(group),
            })
    tmp_raw_output.replace(args.raw_out)

    generated_at = datetime.now(timezone.utc).isoformat()
    inputs = {
        "points_csv": relative(args.points),
        "points_csv_sha256": sha256(args.points),
        "point_audit_json": relative(args.point_audit),
        "point_audit_sha256": sha256(args.point_audit),
        "coverage_csv": relative(args.coverage),
        "coverage_csv_sha256": sha256(args.coverage),
        "proofread_root_ids_npy": relative(args.root_ids),
        "proofread_root_ids_sha256": sha256(args.root_ids),
        "published_pair_table": relative(args.published_edges),
        "published_pair_table_sha256": sha256(args.published_edges),
    }
    segment_neuropils = Counter()
    for (_, _, _, neuropil), group in groups.items():
        segment_neuropils[neuropil] += len(group["synapse_ids"])
    raw_neuropils = Counter()
    for (_, _, neuropil), group in raw_groups.items():
        raw_neuropils[neuropil] += len(group["synapse_ids"])
    result = {
        "generated_at_utc": generated_at,
        "source_record": SOURCE_RECORD,
        "source_file": source_file_record(args.zenodo_record),
        "inputs": inputs,
        "output_csv": relative(args.out),
        "output_csv_sha256": sha256(args.out),
        "method": "From exact released points touching the 616 IDs, group only contacts to opposing unproofread segments by proofread ID, segment ID, direction, and neuropil. Keep raw proofread exceptions in a separate file.",
        "counts": {
            "disconnected_proofread_root_ids": len(disconnected),
            "input_points_touching_616_ids": rows,
            "observed_segment_contact_points": segment_points,
            "proofread_raw_exception_points_separated": raw_points,
            "observed_link_rows_by_pair_direction_neuropil": len(groups),
            "opposing_unproofread_segment_ids": len(unique_segment_ids),
            "proofread_root_ids_with_segment_contacts": len({key[0] for key in groups}),
            "point_counts_by_direction": dict(direction_counts),
            "point_counts_by_neuropil": dict(sorted(segment_neuropils.items())),
        },
        "checks": {
            "every_point_has_exactly_one_of_616_proofread_ids": True,
            "segment_output_opposing_partners_absent_from_official_proofread_ids": True,
            "proofread_flags_match_official_root_array": True,
            "per_root_pre_post_counts_match_official_all_partner_tables": True,
            "point_count_matches_upstream_audit": True,
            "synapse_ids_unique": True,
            "cleft_scores_at_least_release_threshold_50": True,
            "coordinates_are_parseable_integers_nm": True,
            "input_coordinate_min_nm": coordinate_min,
            "input_coordinate_max_nm": coordinate_max,
            "input_coordinate_zero_counts": dict(coordinate_zero),
            "input_coordinate_negative_counts": dict(coordinate_negative),
            "input_pre_post_separation_nm_min": separation_min,
            "input_pre_post_separation_nm_mean": separation_sum / rows if rows else None,
            "input_pre_post_separation_nm_max": separation_max,
            "input_pre_post_separation_over_10000_nm_count": separation_over_10000_nm,
            "input_score_min": score_min,
            "input_score_max": score_max,
            "input_connection_score_negative_count": connection_score_negative,
        },
        "interpretation": (
            "Each row is an observed directed v783 contact to an unproofread segment, "
            "not a neuron-neuron edge, inferred segment identity, biological gap repair, "
            "or a calibrated synaptic weight. Keep this CSV separate from the proofread CSR graph."
        ),
    }
    raw_result = {
        "generated_at_utc": generated_at,
        "source_record": SOURCE_RECORD,
        "source_file": source_file_record(args.zenodo_record),
        "inputs": inputs,
        "output_csv": relative(args.raw_out),
        "output_csv_sha256": sha256(args.raw_out),
        "method": "Group released points with both partners in the official proofread root array by exact directed pre ID, post ID, and neuropil; verify every key is absent from the published proofread_connections_783.feather table.",
        "counts": {
            "input_points_touching_616_ids": rows,
            "raw_proofread_exception_points": raw_points,
            "raw_proofread_exception_pair_region_keys": len(raw_groups),
            "raw_proofread_exception_directed_pairs": len({(pre, post) for pre, post, _ in raw_groups}),
            "proofread_root_ids_among_616_with_raw_exceptions": len({
                rid for pre, post, _ in raw_groups for rid in (pre, post) if rid in disconnected
            }),
            "point_counts_by_selected_id_role": dict(raw_direction_counts),
            "point_counts_by_neuropil": dict(sorted(raw_neuropils.items())),
            "upstream_global_raw_minus_published_synapse_count": expected_raw_global_difference,
            "segment_contact_points_separated": segment_points,
        },
        "checks": {
            **published_key_check,
            "all_raw_exception_pair_region_keys_absent_from_published_table": True,
            "raw_exception_points_equal_upstream_global_count_difference": True,
            "exact_synapse_ids_preserved": True,
            "source_and_per_id_counts_verified_in_segment_audit": relative(args.audit),
        },
        "interpretation": (
            "These are released v783 synapse points between two official proofread roots "
            "whose exact directed pair-plus-neuropil keys are absent from the official "
            "aggregated connection table. They are observed raw exceptions, not a "
            "biological inference. Their 48-point total accounts numerically for the "
            "global raw-versus-aggregated count gap, but does not establish full "
            "pairwise equality for every other connection. Keep the published CSR unchanged."
        ),
    }
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    tmp_audit = args.audit.with_name(args.audit.name + ".partial")
    tmp_audit.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_audit.replace(args.audit)
    args.raw_audit.parent.mkdir(parents=True, exist_ok=True)
    tmp_raw_audit = args.raw_audit.with_name(args.raw_audit.name + ".partial")
    tmp_raw_audit.write_text(json.dumps(raw_result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_raw_audit.replace(args.raw_audit)
    print(json.dumps({
        "segment_output_csv": result["output_csv"],
        "segment_contact_points": segment_points,
        "raw_proofread_output_csv": raw_result["output_csv"],
        "raw_proofread_points": raw_points,
        "raw_proofread_pair_region_keys": len(raw_groups),
        "raw_pair_keys_absent_from_published_table": True,
        "segment_audit_json": relative(args.audit),
        "raw_audit_json": relative(args.raw_audit),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
