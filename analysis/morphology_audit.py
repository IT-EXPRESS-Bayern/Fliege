"""Bounded-memory inspection of FlyWire FAFB v783 morphology supplements."""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from itertools import islice
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.ipc as ipc
import pyarrow.parquet as pq
from pyarrow._feather import FeatherReader


MORPHOLOGY_FILES = {
    "nblast_flywire_all_right_aba_comp.feather": (809_046_036, "a8b3d2589b382bdb1ca19a060249a2dc"),
    "nblast_flywire_hemibrain_min_comp.feather": (212_095_362, "3ca6d79615e1cd30b37f32a8ae845f32"),
    "nblast_flywire_mirrored_hemibrain_min_comp.feather": (223_176_394, "a0e2089764911fc5fd2d2d14c6aaa6a0"),
    "sk_lod1_783_healed_ds2.parquet": (5_355_543_468, "a4c104776f33ec539ef859064c4de3df"),
}
FLYWIRE_ID = re.compile(r"^(\d{15,20})(?:,\d{15,20})?$")
NB_MAX_SCORE_COLUMNS_PER_BATCH = 256
NB_TARGET_DECOMPRESSED_BYTES = 64 * 1024 * 1024
SKELETON_NESTED_BATCH = 64
SKELETON_SCALAR_BATCH = 65_536


def md5_file(path: Path) -> str:
    digest = hashlib.md5()  # noqa: S324 - published dataset checksum
    with path.open("rb") as handle:
        while block := handle.read(8 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def schema_overview(schema: pa.Schema) -> dict[str, Any]:
    names = schema.names
    sample = names[:25]
    if len(names) > 50:
        sample += ["…"] + names[-25:]
    elif len(names) > 25:
        sample += names[25:]
    return {
        "column_count": len(names),
        "columns_sample": sample,
        "types": dict(Counter(str(field.type) for field in schema)),
        "schema_text_sample": "\n".join(str(field) for field in islice(schema, 40)),
    }


def parse_id(label: Any) -> int | None:
    match = FLYWIRE_ID.fullmatch(str(label)) if label is not None else None
    return int(match.group(1)) if match else None


def coverage(ids: set[int], sorted_roots: np.ndarray | None) -> dict[str, Any]:
    result: dict[str, Any] = {"parsed_flywire_ids": len(ids)}
    if sorted_roots is not None:
        values = np.fromiter(ids, dtype=np.uint64, count=len(ids))
        positions = np.searchsorted(sorted_roots, values)
        valid = positions < len(sorted_roots)
        matched = int(np.count_nonzero(sorted_roots[positions[valid]] == values[valid]))
        result["matched_proofread_roots"] = matched
        result["proofread_root_coverage_fraction"] = matched / len(sorted_roots) if len(sorted_roots) else None
    return result


def is_numeric(field_type: pa.DataType) -> bool:
    return pa.types.is_integer(field_type) or pa.types.is_floating(field_type)


def is_numeric_or_list(field_type: pa.DataType) -> bool:
    if is_numeric(field_type):
        return True
    if pa.types.is_list(field_type) or pa.types.is_large_list(field_type) or pa.types.is_fixed_size_list(field_type):
        return is_numeric(field_type.value_type)
    return False


def empty_quality() -> dict[str, Any]:
    return {"values_scanned": 0, "nulls": 0, "nonfinite": 0, "negative": 0, "min": None, "max": None}


def update_quality(stats: dict[str, Any], array: pa.ChunkedArray | pa.Array) -> None:
    chunks = array.chunks if isinstance(array, pa.ChunkedArray) else [array]
    for values in chunks:
        if pa.types.is_list(values.type) or pa.types.is_large_list(values.type) or pa.types.is_fixed_size_list(values.type):
            values = pc.list_flatten(values)
        stats["values_scanned"] += len(values)
        stats["nulls"] += values.null_count
        if pa.types.is_floating(values.type):
            finite = pc.is_finite(values)
            nonfinite = int(pc.sum(pc.invert(finite)).as_py() or 0)
            stats["nonfinite"] += nonfinite
            if nonfinite:
                values = pc.filter(values, finite)
        if len(values) == values.null_count:
            continue
        bounds = pc.min_max(values).as_py()
        low, high = bounds["min"], bounds["max"]
        if low is not None and low < 0:
            stats["negative"] += int(pc.sum(pc.less(values, 0)).as_py() or 0)
        if low is not None:
            stats["min"] = low if stats["min"] is None else min(stats["min"], low)
        if high is not None:
            stats["max"] = high if stats["max"] is None else max(stats["max"], high)


def numeric_quality(array: pa.ChunkedArray | pa.Array) -> dict[str, Any]:
    stats = empty_quality()
    update_quality(stats, array)
    # Keep the previous key so existing small-file consumers remain compatible.
    stats["sampled_values"] = stats["values_scanned"]
    return stats


def _id_values(array: pa.ChunkedArray | pa.Array, ids: set[int]) -> int:
    unparsed = 0
    chunks = array.chunks if isinstance(array, pa.ChunkedArray) else [array]
    for chunk in chunks:
        # Skeleton files have hundreds of millions of node rows but far fewer
        # distinct neurons. Count repeated IDs in Arrow before Python parsing.
        for item in pc.value_counts(chunk).to_pylist():
            value = item["values"]
            number = parse_id(value)
            if number is None:
                unparsed += int(item["counts"])
            else:
                ids.add(number)
    return unparsed


def nblast(path: Path, sorted_roots: np.ndarray | None, deep_scan: bool = True) -> dict[str, Any]:
    source = pa.memory_map(str(path), "r")
    try:
        reader = ipc.open_file(source)
        schema = reader.schema
        result: dict[str, Any] = {**schema_overview(schema), "record_batches": reader.num_record_batches}
    finally:
        source.close()
    name_ids = {number for name in schema.names if (number := parse_id(name)) is not None}
    result["column_id_coverage"] = coverage(name_ids, sorted_roots)
    result["column_id_scan_scope"] = "all_schema_columns"
    index_candidates = [name for name in ("root_id", "id", "index", "__index_level_0__") if name in schema.names]
    score_columns = [field.name for field in schema if is_numeric(field.type) and field.name not in index_candidates]
    score_names = set(score_columns)
    other_columns = [field.name for field in schema if field.name not in index_candidates and field.name not in score_names]
    result["numeric_score_columns_total"] = len(score_columns)
    result["other_columns_count"] = len(other_columns)
    result["other_columns_sample"] = other_columns[:20]
    row_field = index_candidates[0] if index_candidates else (schema.names[0] if schema.names else None)
    if row_field is None:
        raise ValueError(f"NBLAST Feather file has no columns: {path}")
    # Keep one reader alive: these very wide Feather schemas can be >10 MiB,
    # so reopening the file once per projected score block is expensive.
    projected_reader = FeatherReader(str(path), use_memory_map=True, use_threads=True)
    row_table = projected_reader.read_names([row_field])
    result["rows"] = row_table.num_rows
    result["row_id_column"] = index_candidates[0] if index_candidates else None
    if index_candidates:
        row_ids: set[int] = set()
        unparsed = _id_values(row_table[row_field], row_ids)
        result["row_id_coverage"] = coverage(row_ids, sorted_roots)
        result["row_id_values_unparsed"] = unparsed
        result["row_id_scan_scope"] = "all_rows"
    else:
        result["row_id_scan_scope"] = "unavailable_no_recognized_index_column"
    if deep_scan:
        quality = empty_quality()
        scanned = 0
        # Eight bytes per cell is a conservative bound for the scalar scores.
        # Wider projections amortize Arrow's large schema parsing cost while
        # keeping each decompressed table near 64 MiB.
        column_batch_size = max(
            1, min(NB_MAX_SCORE_COLUMNS_PER_BATCH,
                   NB_TARGET_DECOMPRESSED_BYTES // max(1, result["rows"] * 8))
        )
        for offset in range(0, len(score_columns), column_batch_size):
            names = score_columns[offset:offset + column_batch_size]
            table = projected_reader.read_names(names)
            if table.num_rows != result["rows"]:
                raise ValueError(f"NBLAST row-count changed during projected read: {path}")
            for name in names:
                update_quality(quality, table[name])
            scanned += len(names)
            if scanned and scanned % 1024 == 0:
                print(f"{path.name}: {scanned:,}/{len(score_columns):,} numerische Score-Spalten", flush=True)
        result["score_quality"] = quality
        result["score_scan"] = {
            "mode": "full_numeric_columns",
            "columns_scanned": scanned,
            "numeric_columns_total": len(score_columns),
            "rows_per_column_scanned": result["rows"],
            "all_numeric_values_scanned": scanned == len(score_columns) and bool(score_columns),
            "column_projection_batch_size": column_batch_size,
            "other_non_numeric_columns_not_checked": len(other_columns),
        }
    else:
        sample_columns = score_columns[:5]
        table = projected_reader.read_names(sample_columns) if sample_columns else None
        result["sampled_score_quality"] = {
            name: numeric_quality(table[name]) for name in sample_columns
        } if table is not None else {}
        result["score_scan"] = {
            "mode": "sampled_columns",
            "columns_scanned": len(sample_columns),
            "numeric_columns_total": len(score_columns),
            "rows_per_column_scanned": result["rows"],
            "all_numeric_values_scanned": False,
            "other_non_numeric_columns_not_checked": len(other_columns),
        }
    return result


def skeletons(path: Path, sorted_roots: np.ndarray | None, deep_scan: bool = True) -> dict[str, Any]:
    reader = pq.ParquetFile(path)
    schema = reader.schema_arrow
    result: dict[str, Any] = {
        **schema_overview(schema),
        "rows": reader.metadata.num_rows,
        "row_groups": reader.metadata.num_row_groups,
        "coordinate_units": "nanometers, per Zenodo 10877326",
        "source_representation": "SWC skeletons packed in Parquet",
        "row_grain": "skeleton_node" if {"neuron", "node_id", "parent_id"}.issubset(schema.names) else "schema_dependent",
    }
    # The v783 SWC Parquet uses `neuron` for the FlyWire root ID. Each row is
    # one skeleton node, rather than one neuron or one whole SWC object.
    id_candidates = [name for name in ("root_id", "neuron", "neuron_id", "body_id", "id") if name in schema.names]
    id_name = id_candidates[0] if id_candidates and (
        pa.types.is_integer(schema.field(id_candidates[0]).type)
        or pa.types.is_string(schema.field(id_candidates[0]).type)
        or pa.types.is_large_string(schema.field(id_candidates[0]).type)
    ) else None
    result["id_column"] = id_name
    result["id_scan_scope"] = "all_rows" if id_name else "unavailable_no_scalar_id_column"
    numeric_columns = [field.name for field in schema if is_numeric_or_list(field.type) and field.name != id_name]
    coordinate_columns = [name for name in ("x", "y", "z", "radius") if name in numeric_columns]
    unparsed_columns = [field.name for field in schema if field.name not in numeric_columns and field.name != id_name]
    result["numeric_columns_total"] = len(numeric_columns)
    result["numeric_columns_sample"] = numeric_columns[:30]
    result["unparsed_columns_count"] = len(unparsed_columns)
    result["unparsed_columns_sample"] = unparsed_columns[:30]
    result["recognized_coordinate_columns"] = coordinate_columns
    nested = any(
        pa.types.is_list(schema.field(name).type)
        or pa.types.is_large_list(schema.field(name).type)
        or pa.types.is_fixed_size_list(schema.field(name).type)
        for name in numeric_columns
    )
    if deep_scan:
        select = ([id_name] if id_name else []) + numeric_columns
        batch_size = SKELETON_NESTED_BATCH if nested else SKELETON_SCALAR_BATCH
        ids: set[int] = set()
        id_unparsed = 0
        numeric_stats = {name: empty_quality() for name in numeric_columns}
        rows_scanned = 0
        if select:
            for batch in reader.iter_batches(batch_size=batch_size, columns=select):
                rows_scanned += batch.num_rows
                if id_name:
                    id_unparsed += _id_values(batch.column(batch.schema.get_field_index(id_name)), ids)
                for name in numeric_columns:
                    update_quality(numeric_stats[name], batch.column(batch.schema.get_field_index(name)))
        result["id_coverage"] = coverage(ids, sorted_roots) if id_name else None
        result["id_rows_unparsed"] = id_unparsed if id_name else None
        result["numeric_quality"] = numeric_stats
        result["coordinate_quality"] = {name: numeric_stats[name] for name in coordinate_columns}
        result["numeric_scan"] = {
            "mode": "full_recognized_numeric_columns" if select else "unavailable",
            "columns_scanned": len(numeric_columns),
            "numeric_columns_total": len(numeric_columns),
            "rows_scanned": rows_scanned,
            "rows_total": result["rows"],
            "all_recognized_numeric_values_scanned": rows_scanned == result["rows"] and bool(select),
            "xyz_coordinates_recognized": all(name in coordinate_columns for name in ("x", "y", "z")),
            "unparsed_columns_not_content_checked": len(unparsed_columns),
            "batch_size": batch_size,
        }
    else:
        ids = set()
        id_unparsed = 0
        if id_name:
            for batch in reader.iter_batches(batch_size=SKELETON_SCALAR_BATCH, columns=[id_name]):
                id_unparsed += _id_values(batch.column(0), ids)
        result["id_coverage"] = coverage(ids, sorted_roots) if id_name else None
        result["id_rows_unparsed"] = id_unparsed if id_name else None
        result["coordinate_quality_sample"] = {name: [] for name in coordinate_columns}
        batch_size = 4 if nested else SKELETON_SCALAR_BATCH
        rows_scanned = 0
        if coordinate_columns:
            for batch_no, batch in enumerate(reader.iter_batches(batch_size=batch_size, columns=coordinate_columns)):
                if batch_no >= 2:
                    break
                rows_scanned += batch.num_rows
                for name in coordinate_columns:
                    result["coordinate_quality_sample"][name].append(
                        numeric_quality(batch.column(batch.schema.get_field_index(name)))
                    )
        result["coordinate_sample_batch_size"] = batch_size
        result["numeric_scan"] = {
            "mode": "sampled_coordinate_batches" if coordinate_columns else "unavailable",
            "columns_scanned": len(coordinate_columns),
            "numeric_columns_total": len(numeric_columns),
            "rows_scanned": rows_scanned,
            "rows_total": result["rows"],
            "all_recognized_numeric_values_scanned": False,
            "xyz_coordinates_recognized": all(name in coordinate_columns for name in ("x", "y", "z")),
            "unparsed_columns_not_content_checked": len(unparsed_columns),
            "batch_size": batch_size,
        }
    return result


def analyze_morphology(
    directory: Path, sorted_roots: np.ndarray | None, skip_md5: bool, deep_scan: bool = True
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "source_url": "https://zenodo.org/records/10877326",
        "release": "v2 / FlyWire FAFB v783",
        "files": {},
        "integrity_complete": not skip_md5,
        "structure_complete": True,
        "numeric_content_full_scan": deep_scan,
        "incomplete": False,
        "nblast_note": "Scores are rounded to four decimal places and negative scores clipped to zero by the publishers.",
    }
    for name, (expected_size, expected_md5) in MORPHOLOGY_FILES.items():
        path = directory / name
        if not path.is_file():
            report["files"][name] = {"status": "missing", "expected_bytes": expected_size, "expected_md5": expected_md5}
            report["integrity_complete"] = False
            report["structure_complete"] = False
            report["numeric_content_full_scan"] = False
            report["incomplete"] = True
            continue
        size = path.stat().st_size
        if size != expected_size:
            report["files"][name] = {"status": "size_mismatch", "bytes": size, "expected_bytes": expected_size, "expected_md5": expected_md5}
            report["integrity_complete"] = False
            report["structure_complete"] = False
            report["numeric_content_full_scan"] = False
            report["incomplete"] = True
            continue
        info: dict[str, Any] = {
            "status": "present", "bytes": size, "expected_bytes": expected_size,
            "expected_md5": expected_md5,
            "md5": md5_file(path) if not skip_md5 else None,
        }
        info["md5_matches_published"] = info["md5"] == expected_md5 if info["md5"] else None
        if info["md5_matches_published"] is False:
            report["integrity_complete"] = False
            report["structure_complete"] = False
            report["numeric_content_full_scan"] = False
            report["incomplete"] = True
            info["status"] = "checksum_mismatch"
            report["files"][name] = info
            continue
        if name.endswith(".parquet"):
            info.update(skeletons(path, sorted_roots, deep_scan))
            scan = info["numeric_scan"]
            fully_scanned = (
                scan["all_recognized_numeric_values_scanned"]
                and scan["xyz_coordinates_recognized"]
                and info["id_scan_scope"] == "all_rows"
            )
        else:
            info.update(nblast(path, sorted_roots, deep_scan))
            fully_scanned = info["score_scan"]["all_numeric_values_scanned"]
        info["numeric_content_full_scan"] = fully_scanned
        if not fully_scanned:
            report["numeric_content_full_scan"] = False
            report["incomplete"] = True
        report["files"][name] = info
        print(f"Morphologie analysiert: {name} ({info['rows']:,} Zeilen)", flush=True)
    if not report["integrity_complete"]:
        report["incomplete"] = True
    return report
