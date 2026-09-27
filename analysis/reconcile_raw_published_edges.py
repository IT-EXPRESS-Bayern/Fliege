"""Reconcile every v783 proofread raw synapse against the published edge table.

Exact key: (presynaptic root ID, postsynaptic root ID, neuropil). The 130M-point
Feather file is streamed; rows with two official proofread IDs are hash
partitioned on the pre ID. Each small partition is aggregated and full-outer
joined to the corresponding published connection partition. Temporary Arrow
streams are removed after a successful run. The official files and CSR graph
are never modified.

    python analysis/reconcile_raw_published_edges.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.ipc as ipc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = ROOT / "data/flywire_fafb_v783/flywire_synapses_783.feather"
DEFAULT_PUBLISHED = ROOT / "data/flywire_fafb_v783/proofread_connections_783.feather"
DEFAULT_ROOT_IDS = ROOT / "data/flywire_fafb_v783/proofread_root_ids_783.npy"
DEFAULT_POINT_AUDIT = ROOT / "analysis/synapse_point_audit.json"
DEFAULT_PRIOR_EXCEPTIONS = ROOT / "data/research_sources/derived/observed_raw_proofread_edge_exceptions_for_616.csv"
DEFAULT_OUT = ROOT / "data/research_sources/derived/raw_published_edge_count_exceptions.csv"
DEFAULT_ALIGNED_OUT = ROOT / "data/research_sources/derived/raw_published_edge_exceptions_after_region_alignment.csv"
DEFAULT_AUDIT = ROOT / "analysis/raw_published_edge_reconciliation_audit.json"
KEYS = ("pre", "post", "neuropil")
RAW_SCHEMA = pa.schema([
    ("pre", pa.int64()), ("post", pa.int64()), ("neuropil", pa.string()), ("n", pa.int64()),
])
PUBLISHED_SCHEMA = pa.schema([
    ("pre", pa.int64()), ("post", pa.int64()), ("neuropil", pa.string()),
    ("syn_count", pa.int64()),
])
CSV_FIELDS = (
    "pre_root_id", "post_root_id", "neuropil", "raw_synapse_points",
    "published_syn_count", "raw_minus_published", "exception_type",
    "previously_identified_among_616",
)
ALIGNED_CSV_FIELDS = (*CSV_FIELDS, "raw_region_alignment_applied")


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def in_sorted(known: np.ndarray, values: np.ndarray) -> np.ndarray:
    indexes = np.searchsorted(known, values)
    return (indexes < len(known)) & (known[np.minimum(indexes, len(known) - 1)] == values)


class PartitionSink:
    """Buffers partition slices and writes compressed Arrow streams."""

    def __init__(self, folder: Path, prefix: str, schema: pa.Schema,
                 partitions: int, flush_rows: int) -> None:
        self.folder = folder
        self.prefix = prefix
        self.schema = schema
        self.partitions = partitions
        self.flush_rows = flush_rows
        self.pending: list[list[pa.Table]] = [[] for _ in range(partitions)]
        self.pending_counts = np.zeros(partitions, dtype=np.int64)
        self.partition_counts = np.zeros(partitions, dtype=np.int64)
        self.files: dict[int, pa.OSFile] = {}
        self.writers: dict[int, ipc.RecordBatchStreamWriter] = {}

    def path(self, partition: int) -> Path:
        return self.folder / f"{self.prefix}_{partition:03d}.arrow"

    def append(self, table: pa.Table) -> None:
        if not table.num_rows:
            return
        pre = table.column("pre").to_numpy(zero_copy_only=False)
        partitions = np.mod(pre, self.partitions).astype(np.int16)
        order = np.argsort(partitions, kind="stable")
        sorted_table = table.take(pa.array(order))
        sorted_partitions = partitions[order]
        boundaries = np.r_[0, np.flatnonzero(np.diff(sorted_partitions)) + 1, len(order)]
        for start, end in zip(boundaries[:-1], boundaries[1:]):
            partition = int(sorted_partitions[start])
            piece = sorted_table.slice(int(start), int(end - start))
            self.pending[partition].append(piece)
            self.pending_counts[partition] += piece.num_rows
            self.partition_counts[partition] += piece.num_rows
            if self.pending_counts[partition] >= self.flush_rows:
                self.flush(partition)

    def flush(self, partition: int) -> None:
        if not self.pending[partition]:
            return
        if partition not in self.writers:
            output = pa.OSFile(str(self.path(partition)), "wb")
            writer = ipc.new_stream(
                output, self.schema, options=ipc.IpcWriteOptions(compression="lz4")
            )
            self.files[partition] = output
            self.writers[partition] = writer
        table = pa.concat_tables(self.pending[partition]).combine_chunks()
        self.writers[partition].write_table(table)
        self.pending[partition] = []
        self.pending_counts[partition] = 0

    def close(self) -> None:
        for partition in range(self.partitions):
            self.flush(partition)
        for writer in self.writers.values():
            writer.close()
        for file in self.files.values():
            file.close()


def select_int_column(batch: pa.RecordBatch, name: str) -> tuple[np.ndarray, int]:
    column = batch.column(batch.schema.get_field_index(name))
    return pc.fill_null(column, 0).to_numpy(zero_copy_only=False).astype(np.int64), column.null_count


def partition_raw(path: Path, known: np.ndarray, sink: PartitionSink,
                  expected_rows: int | None) -> dict[str, int]:
    scanned = 0
    selected = 0
    null_pre = 0
    null_post = 0
    with pa.memory_map(str(path), "r") as source:
        reader = ipc.open_file(source)
        required = {"pre_pt_root_id", "post_pt_root_id", "neuropil"}
        if not required.issubset(reader.schema.names):
            raise ValueError(f"Raw schema missing {sorted(required - set(reader.schema.names))}")
        for index in range(reader.num_record_batches):
            batch = reader.get_batch(index)
            scanned += batch.num_rows
            pre, pre_null = select_int_column(batch, "pre_pt_root_id")
            post, post_null = select_int_column(batch, "post_pt_root_id")
            null_pre += pre_null
            null_post += post_null
            chosen = np.flatnonzero(in_sorted(known, pre) & in_sorted(known, post))
            if len(chosen):
                selected += len(chosen)
                neuropil = batch.column(batch.schema.get_field_index("neuropil")).take(pa.array(chosen))
                if neuropil.null_count:
                    raise ValueError("Raw both-proofread synapse has null neuropil")
                sink.append(pa.Table.from_arrays([
                    pa.array(pre[chosen]), pa.array(post[chosen]), neuropil,
                    pa.array(np.ones(len(chosen), dtype=np.int64)),
                ], schema=RAW_SCHEMA))
            if (index + 1) % 250 == 0:
                print(f"raw batches {index + 1}/{reader.num_record_batches}; "
                      f"rows {scanned:,}; both proofread {selected:,}", flush=True)
    sink.close()
    if expected_rows is not None and scanned != expected_rows:
        raise ValueError(f"Raw row count {scanned} != audited {expected_rows}")
    if int(sink.partition_counts.sum()) != selected:
        raise ValueError("Raw partition row counts do not match filtered points")
    return {"rows_scanned": scanned, "both_proofread_points": selected,
            "pre_root_id_null_rows": null_pre, "post_root_id_null_rows": null_post}


def partition_published(path: Path, sink: PartitionSink,
                        expected_rows: int | None) -> dict[str, int]:
    scanned = 0
    synapses = 0
    with pa.memory_map(str(path), "r") as source:
        reader = ipc.open_file(source)
        required = {"pre_pt_root_id", "post_pt_root_id", "neuropil", "syn_count"}
        if not required.issubset(reader.schema.names):
            raise ValueError(f"Published schema missing {sorted(required - set(reader.schema.names))}")
        for index in range(reader.num_record_batches):
            batch = reader.get_batch(index)
            scanned += batch.num_rows
            pre, pre_null = select_int_column(batch, "pre_pt_root_id")
            post, post_null = select_int_column(batch, "post_pt_root_id")
            counts, count_null = select_int_column(batch, "syn_count")
            neuropil = batch.column(batch.schema.get_field_index("neuropil"))
            if pre_null or post_null or count_null or neuropil.null_count:
                raise ValueError("Published edge table has null key or syn_count")
            if np.any(counts <= 0):
                raise ValueError("Published edge table has nonpositive syn_count")
            synapses += int(counts.sum())
            sink.append(pa.Table.from_arrays([
                pa.array(pre), pa.array(post), neuropil, pa.array(counts),
            ], schema=PUBLISHED_SCHEMA))
    sink.close()
    if expected_rows is not None and scanned != expected_rows:
        raise ValueError(f"Published row count {scanned} != audited {expected_rows}")
    if int(sink.partition_counts.sum()) != scanned:
        raise ValueError("Published partition row counts do not match source rows")
    return {"rows_scanned": scanned, "syn_count_sum": synapses}


def read_partition(path: Path, schema: pa.Schema) -> pa.Table:
    if not path.is_file():
        return pa.Table.from_arrays([pa.array([], type=field.type) for field in schema], schema=schema)
    with pa.memory_map(str(path), "r") as source:
        return ipc.open_stream(source).read_all()


def load_prior_exceptions(path: Path) -> dict[tuple[int, int, str], int]:
    prior: dict[tuple[int, int, str], int] = {}
    with path.open("r", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            key = (int(row["pre_root_id"]), int(row["post_root_id"]), row["neuropil"])
            if key in prior:
                raise ValueError(f"Duplicate previously identified exception key {key}")
            prior[key] = int(row["synapse_count"])
    return prior


def reconcile_partitions(raw_sink: PartitionSink, published_sink: PartitionSink,
                         out: Path, prior: dict[tuple[int, int, str], int]) -> dict[str, object]:
    out.parent.mkdir(parents=True, exist_ok=True)
    partial = out.with_name(out.name + ".partial")
    counts = Counter()
    mismatches: dict[tuple[int, int, str], tuple[int, int]] = {}
    raw_distinct_keys = 0
    published_distinct_keys = 0
    with partial.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for partition in range(raw_sink.partitions):
            raw = read_partition(raw_sink.path(partition), RAW_SCHEMA)
            published = read_partition(published_sink.path(partition), PUBLISHED_SCHEMA)
            grouped_raw = raw.group_by(list(KEYS)).aggregate([("n", "sum")]).rename_columns(
                [*KEYS, "raw_count"]
            )
            grouped_published = published.group_by(list(KEYS)).aggregate(
                [("syn_count", "sum")]
            ).rename_columns([*KEYS, "published_count"])
            raw_distinct_keys += grouped_raw.num_rows
            published_distinct_keys += grouped_published.num_rows
            joined = grouped_raw.join(grouped_published, keys=list(KEYS), join_type="full outer")
            raw_counts = pc.fill_null(joined["raw_count"], 0)
            published_counts = pc.fill_null(joined["published_count"], 0)
            mismatch = joined.filter(pc.not_equal(raw_counts, published_counts))
            if mismatch.num_rows:
                data = mismatch.to_pydict()
                for i in range(mismatch.num_rows):
                    pre, post = int(data["pre"][i]), int(data["post"][i])
                    neuropil = data["neuropil"][i]
                    raw_count = int(data["raw_count"][i] or 0)
                    published_count = int(data["published_count"][i] or 0)
                    key = (pre, post, neuropil)
                    if key in mismatches:
                        raise ValueError(f"Cross-partition duplicate key {key}")
                    mismatches[key] = (raw_count, published_count)
                    kind = ("raw_only" if not published_count else
                            "published_only" if not raw_count else "different_count")
                    counts[kind] += 1
                    counts["raw_points_in_exception_rows"] += raw_count
                    counts["published_synapses_in_exception_rows"] += published_count
                    writer.writerow({
                        "pre_root_id": str(pre), "post_root_id": str(post),
                        "neuropil": neuropil, "raw_synapse_points": raw_count,
                        "published_syn_count": published_count,
                        "raw_minus_published": raw_count - published_count,
                        "exception_type": kind,
                        "previously_identified_among_616": str(key in prior),
                    })
            if (partition + 1) % 16 == 0:
                print(f"joined partitions {partition + 1}/{raw_sink.partitions}; "
                      f"exceptions {len(mismatches)}", flush=True)
    partial.replace(out)
    prior_exact = all(mismatches.get(key) == (count, 0) for key, count in prior.items())
    return {
        "raw_distinct_pair_region_keys": raw_distinct_keys,
        "published_distinct_pair_region_keys": published_distinct_keys,
        "published_duplicate_pair_region_rows": int(published_sink.partition_counts.sum()) - published_distinct_keys,
        "exception_pair_region_keys": len(mismatches),
        "exception_types": {key: counts[key] for key in ("raw_only", "published_only", "different_count")},
        "raw_points_in_exception_rows": counts["raw_points_in_exception_rows"],
        "published_synapses_in_exception_rows": counts["published_synapses_in_exception_rows"],
        "prior_616_exception_keys": len(prior),
        "prior_616_exception_keys_with_exact_count": sum(
            mismatches.get(key) == (count, 0) for key, count in prior.items()
        ),
        "all_prior_616_exception_keys_exact": prior_exact,
        "all_exceptions_are_the_prior_616_keys": prior_exact and len(mismatches) == len(prior),
    }


def classify_region_alignment(exact_csv: Path, aligned_csv: Path,
                              prior: dict[tuple[int, int, str], int]) -> dict[str, object]:
    """Explain exact-key differences without erasing their original labels.

    The literal raw label ``None`` is aligned to official ``UNASGD`` only in
    this *derived comparison*. Both source files and the exact exception CSV
    retain their original values.
    """
    with exact_csv.open("r", encoding="utf-8", newline="") as file:
        exact = list(csv.DictReader(file))
    by_pair: dict[tuple[int, int], list[int]] = {}
    aligned: dict[tuple[int, int, str], dict[str, object]] = {}
    raw_none: dict[tuple[int, int], int] = {}
    published_unasgd: dict[tuple[int, int], int] = {}
    raw_none_rows = 0
    published_unasgd_rows = 0
    for row in exact:
        pre = int(row["pre_root_id"])
        post = int(row["post_root_id"])
        pair = (pre, post)
        raw_count = int(row["raw_synapse_points"])
        published_count = int(row["published_syn_count"])
        totals = by_pair.setdefault(pair, [0, 0])
        totals[0] += raw_count
        totals[1] += published_count
        region = row["neuropil"]
        if raw_count and region == "None":
            raw_none_rows += 1
            raw_none[pair] = raw_none.get(pair, 0) + raw_count
        if published_count and region == "UNASGD":
            published_unasgd_rows += 1
            published_unasgd[pair] = published_unasgd.get(pair, 0) + published_count
        normalized = "UNASGD" if raw_count and region == "None" else region
        key = (pre, post, normalized)
        bucket = aligned.setdefault(key, {"raw": 0, "published": 0, "mapped": False})
        bucket["raw"] += raw_count
        bucket["published"] += published_count
        bucket["mapped"] = bucket["mapped"] or (raw_count > 0 and region == "None")

    matched_region_pairs = {
        pair for pair, count in raw_none.items()
        if published_unasgd.get(pair) == count
    }
    if (len(matched_region_pairs) != len(raw_none) or
            len(matched_region_pairs) != len(published_unasgd)):
        raise ValueError("Raw literal None to published UNASGD is not a complete one-to-one count mapping")
    remaining = {
        key: value for key, value in aligned.items()
        if value["raw"] != value["published"]
    }
    pair_residual = {
        pair: totals for pair, totals in by_pair.items() if totals[0] != totals[1]
    }
    aligned_csv.parent.mkdir(parents=True, exist_ok=True)
    partial = aligned_csv.with_name(aligned_csv.name + ".partial")
    with partial.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=ALIGNED_CSV_FIELDS)
        writer.writeheader()
        for (pre, post, region), value in sorted(remaining.items()):
            raw_count = value["raw"]
            published_count = value["published"]
            kind = ("raw_only" if not published_count else
                    "published_only" if not raw_count else "different_count")
            writer.writerow({
                "pre_root_id": str(pre), "post_root_id": str(post),
                "neuropil": region, "raw_synapse_points": raw_count,
                "published_syn_count": published_count,
                "raw_minus_published": raw_count - published_count,
                "exception_type": kind,
                "previously_identified_among_616": str((pre, post, region) in prior),
                "raw_region_alignment_applied": str(value["mapped"]),
            })
    partial.replace(aligned_csv)
    all_remaining_match_prior = (
        len(remaining) == len(prior) and
        all((key in remaining and remaining[key]["raw"] == count and
             remaining[key]["published"] == 0) for key, count in prior.items())
    )
    return {
        "observed_raw_region_label": "None",
        "observed_published_region_label": "UNASGD",
        "alignment_scope": "derived comparison of v783 raw versus published pair-region counts only",
        "raw_only_None_keys": raw_none_rows,
        "published_only_UNASGD_keys": published_unasgd_rows,
        "one_to_one_matching_directed_pairs": len(matched_region_pairs),
        "matching_synapse_points": sum(raw_none.values()),
        "matching_published_synapses": sum(published_unasgd.values()),
        "directed_pairs_with_nonzero_total_difference": len(pair_residual),
        "pair_level_raw_minus_published_synapses": sum(
            value[0] - value[1] for value in pair_residual.values()
        ),
        "exception_pair_region_keys_after_alignment": len(remaining),
        "raw_points_in_remaining_exceptions": sum(value["raw"] for value in remaining.values()),
        "published_synapses_in_remaining_exceptions": sum(
            value["published"] for value in remaining.values()
        ),
        "all_remaining_exceptions_exactly_prior_616_R7_keys": all_remaining_match_prior,
        "aligned_exception_csv": relative(aligned_csv),
        "aligned_exception_csv_sha256": sha256(aligned_csv),
        "interpretation": (
            "The raw literal region label None and published UNASGD have identical "
            "directed pairs and counts for the discrepant 3,193 pairs. This is an "
            "empirical release-specific comparison rule, not an edit to source data "
            "or a general anatomical equivalence claim."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--published", type=Path, default=DEFAULT_PUBLISHED)
    parser.add_argument("--root-ids", type=Path, default=DEFAULT_ROOT_IDS)
    parser.add_argument("--point-audit", type=Path, default=DEFAULT_POINT_AUDIT)
    parser.add_argument("--prior-exceptions", type=Path, default=DEFAULT_PRIOR_EXCEPTIONS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--aligned-out", type=Path, default=DEFAULT_ALIGNED_OUT)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--partitions", type=int, default=128)
    parser.add_argument("--flush-rows", type=int, default=50000)
    args = parser.parse_args()
    if args.partitions < 2 or args.flush_rows < 1000:
        raise ValueError("Use at least 2 partitions and 1000 rows per flush")
    for path in (args.raw, args.published, args.root_ids, args.point_audit, args.prior_exceptions):
        if not path.is_file():
            raise SystemExit(f"Required input missing: {path}")
    known = np.sort(np.load(args.root_ids).astype(np.int64))
    if not len(known) or np.any(known[1:] == known[:-1]):
        raise ValueError("Official root ID array is empty or has duplicate IDs")
    point_audit = json.loads(args.point_audit.read_text(encoding="utf-8"))
    expected_raw_rows = point_audit["counts"]["rows"]
    expected_both = point_audit["counts"]["both_proofread"]
    prior = load_prior_exceptions(args.prior_exceptions)

    workspace = ROOT / "analysis"
    workspace.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="reconcile_partitions_", dir=workspace) as temporary:
        folder = Path(temporary).resolve()
        if not folder.is_relative_to(workspace.resolve()):
            raise RuntimeError("Temporary partition directory escaped the analysis workspace")
        raw_sink = PartitionSink(folder, "raw", RAW_SCHEMA, args.partitions, args.flush_rows)
        published_sink = PartitionSink(folder, "published", PUBLISHED_SCHEMA,
                                       args.partitions, args.flush_rows)
        raw_counts = partition_raw(args.raw, known, raw_sink, expected_raw_rows)
        published_counts = partition_published(args.published, published_sink, None)
        if raw_counts["both_proofread_points"] != expected_both:
            raise ValueError("Filtered raw proofread count differs from audited point scan")
        temp_bytes = sum(file.stat().st_size for file in folder.iterdir() if file.is_file())
        reconciliation = reconcile_partitions(raw_sink, published_sink, args.out, prior)
        region_alignment = classify_region_alignment(args.out, args.aligned_out, prior)
        partition_stats = {
            "partitions": args.partitions,
            "flush_rows": args.flush_rows,
            "temporary_partition_bytes": temp_bytes,
            "max_raw_rows_in_one_partition": int(raw_sink.partition_counts.max()),
            "max_published_rows_in_one_partition": int(published_sink.partition_counts.max()),
        }

    if (raw_counts["both_proofread_points"] - published_counts["syn_count_sum"] !=
            reconciliation["raw_points_in_exception_rows"] -
            reconciliation["published_synapses_in_exception_rows"]):
        raise ValueError("Global count difference does not equal sum of pair-region differences")
    audit = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_record": "https://zenodo.org/records/10676866",
        "inputs": {
            "raw_synapse_file": relative(args.raw),
            "raw_synapse_file_bytes": args.raw.stat().st_size,
            "published_edge_file": relative(args.published),
            "published_edge_file_bytes": args.published.stat().st_size,
            "official_root_ids": relative(args.root_ids),
            "official_root_ids_sha256": sha256(args.root_ids),
            "point_audit": relative(args.point_audit),
            "point_audit_sha256": sha256(args.point_audit),
            "prior_616_exception_csv": relative(args.prior_exceptions),
            "prior_616_exception_csv_sha256": sha256(args.prior_exceptions),
        },
        "method": "Stream all raw synapse rows, retain only rows whose two IDs are in official proofread_root_ids_783.npy, hash partition by pre root ID, aggregate exact directed pre/post/neuropil counts per partition, and full-outer join with all published proofread connection rows partitioned by the same key. Arrow partition files are temporary.",
        "raw_counts": raw_counts,
        "published_counts": published_counts,
        "partition_stats": partition_stats,
        "reconciliation": reconciliation,
        "region_alignment": region_alignment,
        "global_raw_minus_published_synapses": (
            raw_counts["both_proofread_points"] - published_counts["syn_count_sum"]
        ),
        "exception_csv": relative(args.out),
        "exception_csv_sha256": sha256(args.out),
        "interpretation": (
            "Every released raw both-proofread point has been compared by exact directed "
            "pair and neuropil with the published aggregate. An exception means a "
            "dataset discrepancy, not an inferred or newly detected biological synapse. "
            "The official graph and files remain unchanged."
        ),
    }
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    partial = args.audit.with_name(args.audit.name + ".partial")
    partial.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    partial.replace(args.audit)
    print(json.dumps({"exception_csv": audit["exception_csv"],
                      "global_raw_minus_published_synapses": audit["global_raw_minus_published_synapses"],
                      "reconciliation": reconciliation,
                      "region_alignment": region_alignment,
                      "audit_json": relative(args.audit)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
