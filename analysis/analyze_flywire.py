#!/usr/bin/env python3
"""Audit the published FlyWire FAFB v783 files with bounded-memory reads.

The five data files are the static Zenodo 10676866 release. Neuron annotations
come from flyconnectome/flywire_annotations v2.1.0. No network access is used.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.ipc as ipc

from morphology_audit import analyze_morphology
from codex_graph_audit import audit_graph


FILES = {
    "flywire_synapses_783.feather": "f8f1b97c9d4b0ea9b4c8b287f6b99091",
    "per_neuron_neuropil_count_post_783.feather": "bb5999f10920ade803d9f37097a43a56",
    "per_neuron_neuropil_count_pre_783.feather": "90fcdb42c1ba05ed92820840fa1e6ba0",
    "proofread_connections_783.feather": "f48f972d262323a102aed49af1396b8a",
    "proofread_root_ids_783.npy": "e0e6c19732fd8c7a4e39a2d170105421",
}
EXPECTED_SIZES = {
    "flywire_synapses_783.feather": 9_492_998_242,
    "per_neuron_neuropil_count_post_783.feather": 233_843_050,
    "per_neuron_neuropil_count_pre_783.feather": 16_853_770,
    "proofread_connections_783.feather": 852_022_274,
    "proofread_root_ids_783.npy": 1_114_168,
}
NT = ("gaba", "ach", "glut", "oct", "ser", "da")
ANNOTATION_NAME = "Supplemental_file1_neuron_annotations.tsv"
ANNOTATION_SIZE = 27_015_208  # v2.1.0 release artifact, verified at source URL
ANNOTATION_MD5 = "8527e0a95ed5f112766b13260a91e8e2"
PROJECT = Path(__file__).resolve().parent.parent


def md5_file(path: Path) -> str:
    digest = hashlib.md5()  # noqa: S324 - checksum matches the published MD5
    with path.open("rb") as handle:
        while block := handle.read(8 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def as_number(scalar: pa.Scalar | None) -> int | float | None:
    return None if scalar is None else scalar.as_py()


def arrow_batches(path: Path, chunk_size: int) -> tuple[dict[str, Any], Iterator[pa.RecordBatch]]:
    """Return file schema and an iterator of slices of Arrow record batches."""
    source = pa.memory_map(str(path), "r")
    reader = ipc.open_file(source)
    metadata = {
        "columns": {field.name: str(field.type) for field in reader.schema},
        "record_batches": reader.num_record_batches,
    }

    def batches() -> Iterator[pa.RecordBatch]:
        try:
            for number in range(reader.num_record_batches):
                batch = reader.get_batch(number)
                for start in range(0, batch.num_rows, chunk_size):
                    yield batch.slice(start, min(chunk_size, batch.num_rows - start))
        finally:
            source.close()

    return metadata, batches()


def column(batch: pa.RecordBatch, name: str) -> pa.Array:
    index = batch.schema.get_field_index(name)
    if index < 0:
        raise ValueError(f"Missing required column: {name}")
    return batch.column(index)


def numpy_column(batch: pa.RecordBatch, name: str) -> np.ndarray:
    arr = column(batch, name)
    if arr.null_count:
        raise ValueError(f"Unexpected nulls in required numeric column {name}")
    return arr.to_numpy(zero_copy_only=False)


def count_column_name(batch: pa.RecordBatch) -> str:
    """Zenodo description says 'Count'; release Feather files use 'count'."""
    for name in ("count", "Count"):
        if batch.schema.get_field_index(name) >= 0:
            return name
    raise ValueError("Summary Feather file has neither 'count' nor 'Count' column")


def region_counts(values: pa.Array, counts: Counter[str]) -> None:
    for item in pc.value_counts(values).to_pylist():
        counts[str(item["values"])] += int(item["counts"])


def region_weight_counts(batch: pa.RecordBatch, weight_name: str, totals: Counter[str]) -> None:
    grouped = pa.Table.from_arrays(
        [column(batch, "neuropil"), column(batch, weight_name)],
        names=["neuropil", weight_name],
    ).group_by("neuropil").aggregate([(weight_name, "sum")])
    region_values = grouped.column("neuropil").to_pylist()
    weights = grouped.column(f"{weight_name}_sum").to_pylist()
    for region, weight in zip(region_values, weights):
        totals[str(region)] += int(weight or 0)


def stats_update(values: pa.Array, stats: dict[str, Any]) -> None:
    stats["count"] += len(values) - values.null_count
    stats["nulls"] += values.null_count
    count = len(values) - values.null_count
    if count:
        stats["sum"] += float(as_number(pc.sum(values)) or 0)
        low = as_number(pc.min(values))
        high = as_number(pc.max(values))
        stats["min"] = low if stats["min"] is None else min(stats["min"], low)
        stats["max"] = high if stats["max"] is None else max(stats["max"], high)
        outside = pc.or_(pc.less(values, 0), pc.greater(values, 1))
        stats["outside_0_1"] += int(as_number(pc.sum(outside)) or 0)


def empty_stats() -> dict[str, Any]:
    return {"count": 0, "nulls": 0, "sum": 0.0, "min": None, "max": None, "outside_0_1": 0}


def finish_stats(stats: dict[str, Any]) -> dict[str, Any]:
    result = dict(stats)
    result["mean"] = result["sum"] / result["count"] if result["count"] else None
    return result


def root_positions(values: np.ndarray, sorted_ids: np.ndarray) -> np.ndarray:
    # Feather root IDs are int64 while the proofread .npy IDs are uint64.
    # NumPy can promote a mixed search to float64, losing bits above 2**53.
    return np.searchsorted(sorted_ids, values.astype(sorted_ids.dtype, copy=False))


def membership(values: np.ndarray, sorted_ids: np.ndarray) -> np.ndarray:
    cast_values = values.astype(sorted_ids.dtype, copy=False)
    positions = root_positions(values, sorted_ids)
    valid = positions < len(sorted_ids)
    result = np.zeros(len(values), dtype=bool)
    result[valid] = sorted_ids[positions[valid]] == cast_values[valid]
    if sorted_ids.dtype.kind == "u" and values.dtype.kind == "i":
        result &= values >= 0
    elif sorted_ids.dtype.kind == "i" and values.dtype.kind == "u":
        result &= values <= np.iinfo(sorted_ids.dtype).max
    return result


def annotation_analysis(path: Path, sorted_ids: np.ndarray | None) -> dict[str, Any]:
    root_ids: set[int] = set()
    proofread_ids = set(map(int, sorted_ids)) if sorted_ids is not None else None
    transmitter = Counter()
    flow = Counter()
    super_class = Counter()
    cell_class = Counter()
    cell_type = Counter()
    side = Counter()
    soma_present = 0
    anchor_present = 0
    duplicates = 0
    rows = 0
    matched = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"root_id", "pos_x", "pos_y", "pos_z", "soma_x", "soma_y", "soma_z", "top_nt"}
        missing = sorted(required.difference(reader.fieldnames or []))
        if missing:
            raise ValueError(f"Annotation TSV missing columns: {', '.join(missing)}")
        headers = reader.fieldnames or []
        for row in reader:
            rows += 1
            cell_id = int(row["root_id"])
            if cell_id in root_ids:
                duplicates += 1
            else:
                root_ids.add(cell_id)
            if all(row.get(key) for key in ("soma_x", "soma_y", "soma_z")):
                soma_present += 1
            if all(row.get(key) for key in ("pos_x", "pos_y", "pos_z")):
                anchor_present += 1
            transmitter[row.get("top_nt") or "(missing)"] += 1
            flow[row.get("flow") or "(missing)"] += 1
            super_class[row.get("super_class") or "(missing)"] += 1
            cell_class[row.get("cell_class") or "(missing)"] += 1
            cell_type[row.get("cell_type") or "(missing)"] += 1
            side[row.get("side") or "(missing)"] += 1
            if proofread_ids is not None:
                matched += int(cell_id in proofread_ids)
    return {
        "rows": rows,
        "unique_root_ids": len(root_ids),
        "duplicate_root_id_rows": duplicates,
        "matched_proofread_root_ids": matched if sorted_ids is not None else None,
        "proofread_join_fraction": matched / rows if rows and sorted_ids is not None else None,
        "proofread_neurons_annotated_fraction": matched / len(sorted_ids) if sorted_ids is not None and len(sorted_ids) else None,
        "soma_coordinates_present": soma_present,
        "anchor_coordinates_present": anchor_present,
        "top_nt_counts": dict(transmitter.most_common()),
        "flow_counts": dict(flow.most_common()),
        "super_class_counts": dict(super_class.most_common()),
        "cell_class_top_30": dict(cell_class.most_common(30)),
        "cell_type_top_30": dict(cell_type.most_common(30)),
        "distinct_named_cell_types": len(cell_type) - int("(missing)" in cell_type),
        "named_cell_type_rows": rows - cell_type["(missing)"],
        "side_counts": dict(side.most_common()),
        "columns": headers,
        "coordinate_units": "4 x 4 x 40 nm voxels",
    }


def analyze_feather(
    path: Path,
    chunk_size: int,
    sorted_ids: np.ndarray | None,
    max_batches: int | None,
) -> dict[str, Any]:
    metadata, batches = arrow_batches(path, chunk_size)
    result: dict[str, Any] = {**metadata, "rows_read": 0, "complete_scan": True}
    regions: Counter[str] = Counter()
    region_synapses: Counter[str] = Counter()
    nt_stats = {name: empty_stats() for name in NT}
    kind = path.name
    proofread_pre = proofread_post = proofread_both = 0
    seen_proofread_pre = np.zeros(len(sorted_ids), dtype=bool) if sorted_ids is not None else None
    seen_proofread_post = np.zeros(len(sorted_ids), dtype=bool) if sorted_ids is not None else None
    pre_id_chunks: list[np.ndarray] = []
    post_id_chunks: list[np.ndarray] = []
    self_rows = 0
    total_weight = 0
    bad_weight = 0
    next_progress = 5_000_000
    top_pre = top_post = None
    if kind == "proofread_connections_783.feather" and sorted_ids is not None:
        top_pre = np.zeros(len(sorted_ids), dtype=np.int64)
        top_post = np.zeros(len(sorted_ids), dtype=np.int64)
    for batch_number, batch in enumerate(batches):
        if max_batches is not None and batch_number >= max_batches:
            result["complete_scan"] = False
            break
        result["rows_read"] += batch.num_rows
        if result["rows_read"] >= next_progress:
            print(f"{kind}: {result['rows_read']:,} Zeilen gelesen", flush=True)
            next_progress += 5_000_000
        region_counts(column(batch, "neuropil"), regions)
        if kind == "flywire_synapses_783.feather":
            pre = numpy_column(batch, "pre_pt_root_id")
            post = numpy_column(batch, "post_pt_root_id")
            for name in NT:
                stats_update(column(batch, name), nt_stats[name])
            result["cleft_score_min"] = min(
                result.get("cleft_score_min", math.inf),
                int(as_number(pc.min(column(batch, "cleft_score"))) or 0),
            )
            result["cleft_score_below_50"] = result.get("cleft_score_below_50", 0) + int(
                as_number(pc.sum(pc.less(column(batch, "cleft_score"), 50))) or 0
            )
        elif kind == "proofread_connections_783.feather":
            pre = numpy_column(batch, "pre_pt_root_id")
            post = numpy_column(batch, "post_pt_root_id")
            weights = numpy_column(batch, "syn_count").astype(np.int64, copy=False)
            total_weight += int(weights.sum(dtype=np.int64))
            region_weight_counts(batch, "syn_count", region_synapses)
            bad_weight += int(np.count_nonzero(weights < 1))
            for name in NT:
                stats_update(column(batch, f"{name}_avg"), nt_stats[name])
            if sorted_ids is not None and top_pre is not None and top_post is not None:
                pre_ok = membership(pre, sorted_ids)
                post_ok = membership(post, sorted_ids)
                np.add.at(top_pre, root_positions(pre[pre_ok], sorted_ids), weights[pre_ok])
                np.add.at(top_post, root_positions(post[post_ok], sorted_ids), weights[post_ok])
        elif kind == "per_neuron_neuropil_count_pre_783.feather":
            pre = numpy_column(batch, "pre_pt_root_id")
            post = None
            count_name = count_column_name(batch)
            counts = numpy_column(batch, count_name).astype(np.int64, copy=False)
            total_weight += int(counts.sum(dtype=np.int64))
            region_weight_counts(batch, count_name, region_synapses)
            bad_weight += int(np.count_nonzero(counts < 1))
        elif kind == "per_neuron_neuropil_count_post_783.feather":
            pre = None
            post = numpy_column(batch, "post_pt_root_id")
            count_name = count_column_name(batch)
            counts = numpy_column(batch, count_name).astype(np.int64, copy=False)
            total_weight += int(counts.sum(dtype=np.int64))
            region_weight_counts(batch, count_name, region_synapses)
            bad_weight += int(np.count_nonzero(counts < 1))
        else:
            raise ValueError(f"Unknown Feather file: {kind}")
        # The synapse table is ~130M rows; exact unique IDs are taken from the
        # much smaller pre/post summary files instead of retaining all IDs here.
        if kind != "flywire_synapses_783.feather":
            if pre is not None:
                pre_id_chunks.append(np.unique(pre))
            if post is not None:
                post_id_chunks.append(np.unique(post))
        if pre is not None and post is not None:
            self_rows += int(np.count_nonzero(pre == post))
        if sorted_ids is not None:
            if pre is not None:
                pre_ok = membership(pre, sorted_ids)
                proofread_pre += int(pre_ok.sum())
                seen_proofread_pre[root_positions(pre[pre_ok], sorted_ids)] = True
            if post is not None:
                post_ok = membership(post, sorted_ids)
                proofread_post += int(post_ok.sum())
                seen_proofread_post[root_positions(post[post_ok], sorted_ids)] = True
            if pre is not None and post is not None:
                proofread_both += int(np.count_nonzero(pre_ok & post_ok))
    result["region_rows"] = dict(regions.most_common())
    if region_synapses:
        result["region_synapse_counts"] = dict(region_synapses.most_common())
    result["distinct_regions"] = len(regions)
    result["unique_pre_root_ids"] = int(np.unique(np.concatenate(pre_id_chunks)).size) if pre_id_chunks else None
    result["unique_post_root_ids"] = int(np.unique(np.concatenate(post_id_chunks)).size) if post_id_chunks else None
    result["self_connection_rows"] = self_rows if kind in (
        "flywire_synapses_783.feather", "proofread_connections_783.feather"
    ) else None
    has_pre = kind != "per_neuron_neuropil_count_post_783.feather"
    has_post = kind != "per_neuron_neuropil_count_pre_783.feather"
    result["rows_with_proofread_pre"] = proofread_pre if sorted_ids is not None and has_pre else None
    result["rows_with_proofread_post"] = proofread_post if sorted_ids is not None and has_post else None
    result["rows_with_both_proofread"] = proofread_both if sorted_ids is not None and has_pre and has_post else None
    result["unique_proofread_pre_root_ids"] = int(seen_proofread_pre.sum()) if seen_proofread_pre is not None and has_pre else None
    result["unique_proofread_post_root_ids"] = int(seen_proofread_post.sum()) if seen_proofread_post is not None and has_post else None
    if kind != "flywire_synapses_783.feather":
        result["synapse_count_sum"] = total_weight
        result["nonpositive_count_rows"] = bad_weight
    if kind in ("flywire_synapses_783.feather", "proofread_connections_783.feather"):
        result["nt_probability_summary"] = {name: finish_stats(value) for name, value in nt_stats.items()}
    if top_pre is not None and top_post is not None:
        result["top_output_by_synapses"] = top_neurons(sorted_ids, top_pre)
        result["top_input_by_synapses"] = top_neurons(sorted_ids, top_post)
    return result


def top_neurons(ids: np.ndarray, counts: np.ndarray, number: int = 10) -> list[dict[str, Any]]:
    indices = np.argsort(counts)[-number:][::-1]
    return [{"root_id": str(int(ids[i])), "synapses": int(counts[i])} for i in indices]


def cross_checks(report: dict[str, Any]) -> dict[str, Any]:
    products = report["files"]

    def stat(name: str, key: str) -> Any:
        entry = products.get(name) or {}
        return entry.get(key) if entry.get("complete_scan") else None

    synapses = stat("flywire_synapses_783.feather", "rows_read")
    pre = stat("per_neuron_neuropil_count_pre_783.feather", "synapse_count_sum")
    post = stat("per_neuron_neuropil_count_post_783.feather", "synapse_count_sum")
    edges = stat("proofread_connections_783.feather", "synapse_count_sum")
    syn_regions = stat("flywire_synapses_783.feather", "region_rows")
    pre_regions = stat("per_neuron_neuropil_count_pre_783.feather", "region_synapse_counts")
    post_regions = stat("per_neuron_neuropil_count_post_783.feather", "region_synapse_counts")
    return {
        "pre_summary_equals_synapse_rows": pre == synapses if pre is not None and synapses is not None else None,
        "post_summary_equals_synapse_rows": post == synapses if post is not None and synapses is not None else None,
        "pre_summary_equals_synapses_by_region": pre_regions == syn_regions if pre_regions is not None and syn_regions is not None else None,
        "post_summary_equals_synapses_by_region": post_regions == syn_regions if post_regions is not None and syn_regions is not None else None,
        "proofread_edge_synapses_do_not_exceed_all_synapses": edges <= synapses if edges is not None and synapses is not None else None,
        "proofread_edge_row_partners_all_in_root_array": (
            (products["proofread_connections_783.feather"].get("rows_with_both_proofread") ==
             products["proofread_connections_783.feather"].get("rows_read"))
            if products.get("proofread_connections_783.feather", {}).get("complete_scan") and report.get("proofread_neurons") else None
        ),
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# FlyWire FAFB v783: Datenanalyse",
        "",
        f"Erstellt: {report['generated_at_utc']}",
        "",
        "Quelle: [FlyWire-Zenodo-Release 783.0](https://zenodo.org/records/10676866); "
        "[Neuronannotationen v2.1.0](https://github.com/flyconnectome/flywire_annotations/releases/tag/v2.1.0).",
        "",
        "## Integrität und Umfang",
        "",
        "| Datei | Größe (Bytes) | MD5 | Zeilen | Status |",
        "|---|---:|---|---:|---|",
    ]
    for name, info in report["files"].items():
        state = "fehlt" if info["status"] == "missing" else (
            "Größe weicht ab" if info["status"] == "size_mismatch" else
            "nicht geprüft" if info["md5_matches_published"] is None else
            "OK" if info["md5_matches_published"] else "MD5 weicht ab"
        )
        lines.append(f"| `{name}` | {info.get('bytes', '–')} | `{info.get('md5') or '–'}` | {info.get('rows_read', info.get('rows', '–'))} | {state} |")
    roots = report.get("proofread_neurons") or {}
    ann = report.get("annotations") or {}
    syn = report["files"].get("flywire_synapses_783.feather") or {}
    edge = report["files"].get("proofread_connections_783.feather") or {}
    pre_summary = report["files"].get("per_neuron_neuropil_count_pre_783.feather") or {}
    lines += [
        "",
        "## Kernergebnisse",
        "",
        f"- Gegengelesene Neuronen: **{roots.get('unique_root_ids', '–')}** (Duplikate: {roots.get('duplicate_ids', '–')}).",
        f"- Einzel-Synapsen-Zeilen: **{syn.get('rows_read', '–')}**; davon beide Partner gegengelesen: **{syn.get('rows_with_both_proofread', '–')}**.",
        f"- Aggregierte Kanten pro Neuronenpaar und Region: **{edge.get('rows_read', '–')}**; Synapsenzahl: **{edge.get('synapse_count_sum', '–')}**.",
        f"- Prä-Synapsen-Region-Summary: **{pre_summary.get('rows_read', '–')}** Zeilen; gewichtete Synapsensumme **{pre_summary.get('synapse_count_sum', '–')}** (erst mit kompletter Einzel-Synapsentabelle querprüfbar).",
        f"- Annotationen: **{ann.get('rows', '–')}** Zeilen, **{ann.get('unique_root_ids', '–')}** eindeutige Root-IDs; mit Soma-Koordinaten: **{ann.get('soma_coordinates_present', '–')}**.",
        "",
        "### Für Sensorik und Motorik relevante Klassen",
        "",
    ]
    for key in ("sensory", "ascending", "descending", "motor"):
        lines.append(f"- {key}: **{(ann.get('super_class_counts') or {}).get(key, '–')}**")
    lines += [
        "",
        "## Querprüfungen",
        "",
    ]
    for key, value in report["cross_checks"].items():
        lines.append(f"- {key}: **{value if value is not None else 'nicht prüfbar'}**")
    lines += ["", "## Regionen mit den meisten Einzel-Synapsen", ""]
    for region, count in list((syn.get("region_rows") or {}).items())[:15]:
        lines.append(f"- {region}: {count}")
    if not syn.get("region_rows"):
        lines.append("Einzel-Synapsentabelle noch nicht verfügbar.")
    lines += ["", "## Neurotransmitter-Prognosen der Einzel-Synapsen", ""]
    for name, stats in (syn.get("nt_probability_summary") or {}).items():
        mean = stats.get("mean")
        lines.append(f"- {name}: Mittelwert {mean:.4f}; fehlend {stats['nulls']}; außerhalb [0,1] {stats['outside_0_1']}" if mean is not None else f"- {name}: keine Werte")
    if not syn.get("nt_probability_summary"):
        lines.append("Einzel-Synapsentabelle noch nicht verfügbar.")
    lines += [
        "", "## Grenzen", "",
        "- Die Analyse betrifft ausschließlich FAFB v783, also das Gehirn einer adulten weiblichen Fruchtfliege. BANC ist ein separater Datensatz.",
        "- `proofread_connections` enthält ab einer Synapse eine Zeile pro gerichtetem Neuronenpaar **und Region**. Die Zeilenzahl ist nicht die Anzahl eindeutiger Neuronenpaare.",
        "- `flywire_synapses` enthält auch Synapsen mit nicht gegengelesenen Partnern. Der Anteil beidseitig gegengelesener Synapsen wird separat ausgewiesen.",
        "- Neurotransmitterwerte sind Modellprognosen, keine gemessenen neuronalen Dynamikparameter. Anatomische Soma-Punkte liefern allein keine Axon- oder Dendritenverläufe.",
        "- Die v2.1.0-Annotationen entsprechen der 2024 veröffentlichten Klassifikation; spätere Codex-Annotationen können abweichen.",
    ]
    morphology = report.get("morphology") or {}
    lines += [
        "", "## Morphologie (Zenodo 10877326)", "",
        f"- Dateiintegrität per Größe und MD5: **{'vollständig geprüft' if morphology.get('integrity_complete') else 'ausstehend/fehlgeschlagen'}**.",
        f"- Schema und Zeilenzahl: **{'für alle Dateien geprüft' if morphology.get('structure_complete') else 'teilweise/ausstehend'}**.",
        f"- Numerische Inhalte: **{'erkannte Werte vollständig gelesen' if morphology.get('numeric_content_full_scan') else 'nur teilweise gelesen oder nicht interpretierbar'}**.",
        "",
        "| Datei | Größe (Bytes) | MD5 | Zeilen | Datenprüfung |",
        "|---|---:|---|---:|---|",
    ]
    for name, info in (morphology.get("files") or {}).items():
        status = info.get("status", "unbekannt")
        status = {"missing": "fehlt", "size_mismatch": "Größe weicht ab", "checksum_mismatch": "MD5 weicht ab"}.get(status, status)
        if status == "present":
            integrity = "MD5 OK" if info.get("md5_matches_published") else (
                "MD5 nicht geprüft" if info.get("md5_matches_published") is None else "MD5 weicht ab"
            )
            scan = info.get("numeric_scan") or info.get("score_scan") or {}
            if info.get("numeric_content_full_scan"):
                content = "numerischer Vollscan"
            elif scan.get("mode", "").startswith("sampled"):
                content = "numerische Stichprobe"
            else:
                content = "numerischer Inhalt unvollständig"
            status = f"{integrity}; {content}"
        lines.append(f"| `{name}` | {info.get('bytes') or '–'} | `{info.get('md5') or '–'}` | {info.get('rows', '–')} | {status} |")
    lines += [
        "", "Die Skelette liegen als SWC-Knoten in einer Parquet-Datei vor: Eine Tabellenzeile beschreibt einen Knoten, `neuron` ist die FlyWire-Root-ID. Ihre Koordinaten sind in nm.",
        "Die NBLAST-Scores wurden von den Herausgebern auf vier Dezimalstellen gerundet und negative Werte bei 0 abgeschnitten.",
        "Dateiintegrität, Schema, ID-Abdeckung und numerische Inhaltsprüfung sind getrennt im JSON-Bericht ausgewiesen.",
        "Ein numerischer Vollscan umfasst alle erkannten numerischen Spalten und Skelettzeilen. Nicht erkannte verschachtelte oder textuelle SWC-Inhalte werden ausdrücklich als ungeprüft markiert.",
    ]
    graph = report.get("codex_graph") or {}
    graph_stats = graph.get("graph_stats") or {}
    codex_source = graph.get("codex_source") or {}
    lines += [
        "", "## Separater Codex-v783-Graph", "",
        f"- Status: **{'vorhanden' if graph.get('status') == 'present' else 'fehlt'}**; Integritätsprüfungen: **{'bestanden' if graph.get('checks_all_true') else 'nicht bestanden/ausstehend'}**.",
        f"- Neuronen: **{graph_stats.get('nodes', '–')}**; gerichtete Paarkanten: **{graph_stats.get('directed_pair_edges', '–')}**; darin enthaltene Synapsen: **{graph_stats.get('synapses_in_graph', '–')}**.",
        f"- Quelle: `connections_princeton.csv.gz` mit **{graph_stats.get('precombined_neuropil_rows', '–')}** Paar×Neuropil-Zeilen vor der Aggregation.",
        "- Die Codex-Quelle ist bereits auf Paare mit mindestens fünf Synapsen über alle Regionen gefiltert. Der Graph-Parameter `min_synapses_per_edge=1` stellt ausgelassene Paare nicht wieder her.",
        "- Die sechs Transmitterkanäle im Graphen kodieren gewichtete Anteile kategorischer `nt_type`-Labels. Sie sind **keine** ursprünglichen Wahrscheinlichkeiten wie in der Zenodo-Feather-Tabelle.",
        "- Der Codex-Graph und die Original-Zenodo-Verbindungstabelle sind verschiedene Datenprodukte; ihre Kantenzahlen und Synapsensummen dürfen nicht gleichgesetzt werden.",
    ]
    if codex_source.get("region_rows"):
        lines += ["", "Häufigste Neuropile im Codex-Export (Paar×Neuropil-Zeilen):", ""]
        for region, count in list(codex_source["region_rows"].items())[:10]:
            lines.append(f"- {region}: {count}")
    if codex_source.get("nt_type_synapses"):
        lines += ["", "Synapsen nach kategorischem Codex-`nt_type`:", ""]
        for transmitter, count in codex_source["nt_type_synapses"].items():
            lines.append(f"- {transmitter}: {count}")
    if report["incomplete"]:
        lines.append("- **Teilbericht:** Mindestens eine Datei fehlt, ist nicht integritätsgeprüft oder wurde inhaltlich nur teilweise untersucht. Kennzahlen vollständig gescannter Dateien bleiben auf diese Dateien begrenzt gültig.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=PROJECT / "data" / "flywire_fafb_v783")
    parser.add_argument("--annotations", type=Path, default=PROJECT / "data" / "flywire_annotations_v2.1.0" / ANNOTATION_NAME)
    parser.add_argument("--morphology-dir", type=Path, default=PROJECT / "data" / "flywire_morphology_v783")
    parser.add_argument("--graph-dir", type=Path, default=PROJECT / "brain" / "graph-v783")
    parser.add_argument("--codex-source-dir", type=Path, default=PROJECT / "data" / "codex_fafb_v783")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--batch-size", type=int, default=65_536)
    parser.add_argument("--allow-incomplete", action="store_true", help="Write a partial report if files are missing")
    parser.add_argument("--max-batches", type=int, help="Read only this many Arrow slices per Feather file (test run)")
    parser.add_argument("--skip-md5", action="store_true", help="Skip full checksum reads (test run only)")
    morphology_mode = parser.add_mutually_exclusive_group()
    morphology_mode.add_argument("--deep-morphology", action="store_true", help="Scan every recognized numeric morphology column and skeleton row (default)")
    morphology_mode.add_argument("--sample-morphology", action="store_true", help="Only sample morphology numeric values; report stays partial")
    args = parser.parse_args()
    if args.batch_size < 1 or (args.max_batches is not None and args.max_batches < 1):
        parser.error("batch-size and max-batches must be positive")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": "FlyWire FAFB v783.0 (female adult fly brain)",
        "zenodo_url": "https://zenodo.org/records/10676866",
        "annotation_version": "flywire_annotations v2.1.0",
        "data_dir": str(args.data_dir.resolve()),
        "annotation_path": str(args.annotations.resolve()),
        "morphology_dir": str(args.morphology_dir.resolve()),
        "codex_graph_dir": str(args.graph_dir.resolve()),
        "scan_options": {"batch_size": args.batch_size, "max_batches": args.max_batches, "skip_md5": args.skip_md5,
                         "deep_morphology": not args.sample_morphology},
        "files": {},
        "incomplete": args.skip_md5 or args.max_batches is not None,
    }
    roots_path = args.data_dir / "proofread_root_ids_783.npy"
    sorted_ids: np.ndarray | None = None
    roots_can_load = (
        roots_path.is_file()
        and roots_path.stat().st_size == EXPECTED_SIZES[roots_path.name]
        and (args.skip_md5 or md5_file(roots_path) == FILES[roots_path.name])
    )
    if roots_can_load:
        roots = np.load(roots_path, mmap_mode="r", allow_pickle=False)
        if roots.ndim != 1 or roots.dtype.kind not in "iu":
            raise ValueError("proofread_root_ids_783.npy must be a one-dimensional integer array")
        sorted_ids = np.unique(roots)
        report["proofread_neurons"] = {
            "rows": int(roots.size), "unique_root_ids": int(sorted_ids.size),
            "duplicate_ids": int(roots.size - sorted_ids.size), "dtype": str(roots.dtype),
        }
    else:
        report["incomplete"] = True
    for filename, expected in FILES.items():
        path = args.data_dir / filename
        if not path.is_file():
            report["files"][filename] = {"status": "missing", "expected_md5": expected, "expected_bytes": EXPECTED_SIZES[filename]}
            report["incomplete"] = True
            continue
        if path.stat().st_size != EXPECTED_SIZES[filename]:
            report["files"][filename] = {
                "status": "size_mismatch", "bytes": path.stat().st_size,
                "expected_bytes": EXPECTED_SIZES[filename], "expected_md5": expected,
            }
            report["incomplete"] = True
            continue
        info: dict[str, Any] = {
            "status": "present", "bytes": path.stat().st_size,
            "expected_bytes": EXPECTED_SIZES[filename],
            "expected_md5": expected,
            "md5": md5_file(path) if not args.skip_md5 else None,
        }
        info["md5_matches_published"] = info["md5"] == expected if info["md5"] else None
        if info["md5_matches_published"] is False:
            report["incomplete"] = True
            info["status"] = "checksum_mismatch"
            report["files"][filename] = info
            continue
        if filename.endswith(".feather"):
            info.update(analyze_feather(path, args.batch_size, sorted_ids, args.max_batches))
            if not info["complete_scan"]:
                report["incomplete"] = True
        elif sorted_ids is not None:
            info.update(report["proofread_neurons"])
            info["complete_scan"] = True
        report["files"][filename] = info
        print(f"Analysiert: {filename} ({info.get('rows_read', info.get('rows', '–'))} Zeilen)", flush=True)
    if args.annotations.is_file() and args.annotations.stat().st_size == ANNOTATION_SIZE:
        report["annotations"] = annotation_analysis(args.annotations, sorted_ids)
        report["annotations"]["bytes"] = args.annotations.stat().st_size
        report["annotations"]["expected_md5"] = ANNOTATION_MD5
        report["annotations"]["md5"] = md5_file(args.annotations) if not args.skip_md5 else None
        report["annotations"]["md5_matches_pinned_release"] = (
            report["annotations"]["md5"] == ANNOTATION_MD5 if report["annotations"]["md5"] else None
        )
        if report["annotations"]["md5_matches_pinned_release"] is False:
            report["incomplete"] = True
    else:
        report["annotations"] = {
            "status": "missing" if not args.annotations.is_file() else "size_mismatch",
            "bytes": args.annotations.stat().st_size if args.annotations.is_file() else None,
            "expected_bytes": ANNOTATION_SIZE,
        }
        report["incomplete"] = True
    report["cross_checks"] = cross_checks(report)
    report["morphology"] = analyze_morphology(
        args.morphology_dir, sorted_ids, args.skip_md5, deep_scan=not args.sample_morphology
    )
    if report["morphology"]["incomplete"]:
        report["incomplete"] = True
    report["codex_graph"] = audit_graph(args.graph_dir, args.codex_source_dir, sorted_ids, args.skip_md5)
    if report["codex_graph"]["incomplete"]:
        report["incomplete"] = True
    (args.output_dir / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.output_dir / "report.md").write_text(markdown(report), encoding="utf-8")
    if report["incomplete"] and not args.allow_incomplete:
        print("Bericht ist unvollständig. Fehlende Dateien, Prüffehler oder Inhalts-Stichproben siehe report.json.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
