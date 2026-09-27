"""Build a browser-readable, directed CSR graph from FlyWire connection data.

The large Feather input is read in record batches. Runs are sorted on disk and
merged, so memory use does not grow with the number of connections.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import heapq
import json
import tempfile
from pathlib import Path
from typing import Iterator

import numpy as np


NT_COLUMNS = ("ach_avg", "gaba_avg", "glut_avg", "da_avg", "ser_avg", "oct_avg")
NT_NAMES = ("acetylcholine", "GABA", "glutamate", "dopamine", "serotonin", "octopamine")
REQUIRED_COLUMNS = ("pre_pt_root_id", "post_pt_root_id", "syn_count", *NT_COLUMNS)
CODEX_COLUMNS = ("pre_root_id", "post_root_id", "syn_count", "nt_type")
CODEX_NT = {"ACH": "ach_avg", "GABA": "gaba_avg", "GLUT": "glut_avg",
            "DA": "da_avg", "SER": "ser_avg", "OCT": "oct_avg"}
CODEX_URL = "https://storage.googleapis.com/flywire-data/codex/data/fafb/783/connections_princeton.csv.gz"
CODEX_MD5 = "5e5101c6ffc17d7e300541d8f71842c1"
RUN_DTYPE = np.dtype([
    ("src", "<u4"), ("dst", "<u4"), ("syn", "<u8"), ("nt_sum", "<f8", (6,)),
])
ANNOTATION_FIELDS = (
    "flow", "super_class", "cell_class", "cell_sub_class", "cell_type",
    "hemibrain_type", "side", "top_nt", "top_nt_conf", "known_nt",
    "nerve", "soma_x", "soma_y", "soma_z",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def connection_source(path: Path) -> dict[str, str]:
    """Identify the meaning of NT columns before any graph data is emitted."""
    name = path.name.lower()
    if name.endswith(".feather"):
        return {
            "format": "flywire_probability_columns",
            "neurotransmitter_semantics": "Six source-predicted per-row mean probabilities, synapse-weighted when neuropils are merged.",
        }
    if not name.endswith((".csv", ".tsv", ".csv.gz", ".tsv.gz")):
        raise ValueError("Connections must be .feather, .csv, .tsv, .csv.gz or .tsv.gz")
    opener = gzip.open if name.endswith(".gz") else open
    delimiter = "\t" if name.endswith((".tsv", ".tsv.gz")) else ","
    with opener(path, "rt", encoding="utf-8-sig", newline="") as f:
        fields = set(next(csv.reader(f, delimiter=delimiter)))
    if set(REQUIRED_COLUMNS) <= fields:
        return {
            "format": "flywire_probability_columns",
            "neurotransmitter_semantics": "Six source-predicted per-row mean probabilities, synapse-weighted when neuropils are merged.",
        }
    if set(CODEX_COLUMNS) <= fields:
        info = {
            "format": "codex_princeton_categorical_nt",
            "neurotransmitter_semantics": "Source nt_type is one categorical prediction per row. Six graph channels are one-hot encodings of that category, averaged by synapse count when neuropils are merged; they are not source probability estimates.",
        }
        if path.name == "connections_princeton.csv.gz":
            info["download_url"] = CODEX_URL
            info["published_md5"] = CODEX_MD5
        return info
    raise ValueError(f"Unrecognized connection columns: {sorted(fields)}")


def _csv_chunks(path: Path, chunk_rows: int) -> Iterator[dict[str, np.ndarray]]:
    name = path.name.lower()
    delimiter = "\t" if name.endswith((".tsv", ".tsv.gz")) else ","
    opener = gzip.open if name.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        fields = set(reader.fieldnames or ())
        codex = set(CODEX_COLUMNS) <= fields and not set(REQUIRED_COLUMNS) <= fields
        required = CODEX_COLUMNS if codex else REQUIRED_COLUMNS
        missing = set(required) - fields
        if missing:
            raise ValueError(f"Missing connection columns: {sorted(missing)}")
        rows: list[dict[str, str]] = []
        for row in reader:
            rows.append(row)
            if len(rows) >= chunk_rows:
                yield _rows_to_arrays(rows, codex)
                rows.clear()
        if rows:
            yield _rows_to_arrays(rows, codex)


def _rows_to_arrays(rows: list[dict[str, str]], codex: bool = False) -> dict[str, np.ndarray]:
    if codex:
        labels = [r["nt_type"].strip().upper() for r in rows]
        unknown = set(labels) - set(CODEX_NT)
        if unknown:
            raise ValueError(f"Unknown Codex nt_type label(s): {sorted(unknown)}")
        return {
            "pre_pt_root_id": np.asarray([int(r["pre_root_id"]) for r in rows], dtype=np.uint64),
            "post_pt_root_id": np.asarray([int(r["post_root_id"]) for r in rows], dtype=np.uint64),
            "syn_count": np.asarray([int(r["syn_count"]) for r in rows], dtype=np.uint64),
            **{c: np.asarray([float(CODEX_NT[label] == c) for label in labels], dtype=np.float64)
               for c in NT_COLUMNS},
        }
    return {
        "pre_pt_root_id": np.asarray([int(r["pre_pt_root_id"]) for r in rows], dtype=np.uint64),
        "post_pt_root_id": np.asarray([int(r["post_pt_root_id"]) for r in rows], dtype=np.uint64),
        "syn_count": np.asarray([int(r["syn_count"]) for r in rows], dtype=np.uint64),
        **{c: np.asarray([float(r[c] or "nan") for r in rows], dtype=np.float64)
           for c in NT_COLUMNS},
    }


def _feather_chunks(path: Path, chunk_rows: int) -> Iterator[dict[str, np.ndarray]]:
    try:
        import pyarrow as pa
        import pyarrow.ipc as ipc
    except ImportError as exc:
        raise RuntimeError("Feather input needs pyarrow; install brain/requirements.txt") from exc

    with pa.memory_map(str(path), "r") as source:
        reader = ipc.open_file(source)
        missing = set(REQUIRED_COLUMNS) - set(reader.schema.names)
        if missing:
            raise ValueError(f"Missing connection columns: {sorted(missing)}")
        batches = []
        count = 0
        for i in range(reader.num_record_batches):
            batch = reader.get_batch(i)
            batches.append(batch)
            count += batch.num_rows
            if count >= chunk_rows:
                table = pa.Table.from_batches(batches)
                yield {c: table[c].to_numpy(zero_copy_only=False) for c in REQUIRED_COLUMNS}
                batches.clear()
                count = 0
        if batches:
            table = pa.Table.from_batches(batches)
            yield {c: table[c].to_numpy(zero_copy_only=False) for c in REQUIRED_COLUMNS}


def connection_chunks(path: Path, chunk_rows: int) -> Iterator[dict[str, np.ndarray]]:
    name = path.name.lower()
    if name.endswith(".feather"):
        yield from _feather_chunks(path, chunk_rows)
    elif name.endswith((".csv", ".tsv", ".csv.gz", ".tsv.gz")):
        # Avoid holding a million Python row dictionaries for compressed CSV.
        yield from _csv_chunks(path, min(chunk_rows, 100_000))
    else:
        raise ValueError("Connections must be .feather, .csv, .tsv, .csv.gz or .tsv.gz")


def _make_run(cols: dict[str, np.ndarray], ids: np.ndarray, path: Path) -> tuple[int, int, int]:
    pre = np.asarray(cols["pre_pt_root_id"], dtype=np.uint64)
    post = np.asarray(cols["post_pt_root_id"], dtype=np.uint64)
    syn = np.asarray(cols["syn_count"], dtype=np.uint64)
    src = np.searchsorted(ids, pre)
    dst = np.searchsorted(ids, post)
    valid = (src < len(ids)) & (dst < len(ids)) & (syn > 0)
    valid &= ids[np.minimum(src, len(ids) - 1)] == pre
    valid &= ids[np.minimum(dst, len(ids) - 1)] == post
    dropped_rows = int((~valid).sum())
    dropped_synapses = int(syn[~valid].sum(dtype=np.uint64))
    if not np.any(valid):
        np.save(path, np.empty(0, dtype=RUN_DTYPE), allow_pickle=False)
        return 0, dropped_rows, dropped_synapses

    src = src[valid].astype(np.uint32)
    dst = dst[valid].astype(np.uint32)
    syn = syn[valid]
    order = np.lexsort((dst, src))
    src, dst, syn = src[order], dst[order], syn[order]
    start = np.r_[0, np.flatnonzero((src[1:] != src[:-1]) | (dst[1:] != dst[:-1])) + 1]
    result = np.empty(len(start), dtype=RUN_DTYPE)
    result["src"] = src[start]
    result["dst"] = dst[start]
    result["syn"] = np.add.reduceat(syn, start, dtype=np.uint64)
    for j, col in enumerate(NT_COLUMNS):
        p = np.asarray(cols[col], dtype=np.float64)[valid][order]
        p = np.clip(np.nan_to_num(p, nan=0.0, posinf=0.0, neginf=0.0), 0.0, 1.0)
        result["nt_sum"][:, j] = np.add.reduceat(p * syn, start, dtype=np.float64)
    np.save(path, result, allow_pickle=False)
    return len(result), dropped_rows, dropped_synapses


def _load_annotations(path: Path | None, ids: np.ndarray, output: Path) -> int:
    index = {}
    if path is not None:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            if "root_id" not in (reader.fieldnames or ()):
                raise ValueError("Annotations TSV is missing root_id")
            for row in reader:
                root = row.get("root_id", "")
                if root:
                    index[int(root)] = {k: row[k] for k in ANNOTATION_FIELDS if k in row and row[k]}
    matched = 0
    with output.open("w", encoding="utf-8", newline="\n") as f:
        f.write("[\n")
        for i, root in enumerate(ids):
            numeric = int(root)
            ann = index.get(numeric, {})
            matched += bool(ann)
            # JSON decimal strings preserve IDs beyond JavaScript's safe integer range.
            item = {"id": str(numeric), **ann}
            f.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")))
            f.write(",\n" if i + 1 < len(ids) else "\n")
        f.write("]\n")
    return matched


def _merge_runs(runs: list[Path], out: Path, node_count: int, min_synapses: int) -> tuple[int, int]:
    arrays = [np.load(p, mmap_mode="r", allow_pickle=False) for p in runs]
    cursor = [0] * len(arrays)
    heap = [(int(a[0]["src"]), int(a[0]["dst"]), i)
            for i, a in enumerate(arrays) if len(a)]
    heapq.heapify(heap)
    offsets = np.zeros(node_count + 1, dtype=np.uint64)
    targets: list[int] = []
    synapses: list[int] = []
    probabilities: list[np.ndarray] = []
    edge_count = 0
    total_synapses = 0

    def flush(t_file, s_file, p_file) -> None:
        if not targets:
            return
        np.asarray(targets, dtype="<u4").tofile(t_file)
        np.asarray(synapses, dtype="<u4").tofile(s_file)
        np.asarray(probabilities, dtype=np.uint8).reshape(-1, 6).tofile(p_file)
        targets.clear()
        synapses.clear()
        probabilities.clear()

    with (out / "targets.u32").open("wb") as tf, \
         (out / "synapses.u32").open("wb") as sf, \
         (out / "nt_probs.u8").open("wb") as pf:
        while heap:
            src, dst, run = heap[0]
            count = 0
            nt_sum = np.zeros(6, dtype=np.float64)
            while heap and heap[0][:2] == (src, dst):
                _, _, run = heapq.heappop(heap)
                row = arrays[run][cursor[run]]
                count += int(row["syn"])
                nt_sum += row["nt_sum"]
                cursor[run] += 1
                if cursor[run] < len(arrays[run]):
                    next_row = arrays[run][cursor[run]]
                    heapq.heappush(heap, (int(next_row["src"]), int(next_row["dst"]), run))
            if count < min_synapses:
                continue
            if count > np.iinfo(np.uint32).max:
                raise OverflowError(f"Synapse count exceeds uint32 for edge {src}->{dst}")
            q = np.rint(np.clip(nt_sum / count, 0.0, 1.0) * 255.0).astype(np.uint8)
            targets.append(dst)
            synapses.append(count)
            probabilities.append(q)
            offsets[src + 1] += 1
            edge_count += 1
            total_synapses += count
            if len(targets) >= 100_000:
                flush(tf, sf, pf)
        flush(tf, sf, pf)

    if edge_count > np.iinfo(np.uint32).max:
        raise OverflowError("CSR edge count exceeds uint32")
    np.cumsum(offsets, out=offsets)
    offsets.astype("<u4").tofile(out / "offsets.u32")
    return edge_count, total_synapses


def build(connections: Path, root_ids: Path, annotations: Path | None, out: Path,
          dataset: str, min_synapses: int = 1, chunk_rows: int = 1_000_000) -> dict:
    if min_synapses < 1 or chunk_rows < 1:
        raise ValueError("min_synapses and chunk_rows must be positive")
    source = connection_source(connections)
    if source.get("published_md5"):
        digest = hashlib.md5()
        with connections.open("rb") as f:
            for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
                digest.update(block)
        actual_md5 = digest.hexdigest()
        if actual_md5 != source["published_md5"]:
            raise ValueError(f"Codex export MD5 mismatch: {actual_md5} != {source['published_md5']}")
        source["verified_md5"] = actual_md5
        source["preexisting_filter"] = (
            "Filtered Codex export: in this exact file, every ordered neuron pair "
            "has at least five synapses across neuropils; individual neuropil rows may have fewer."
        )
    ids = np.load(root_ids, allow_pickle=False)
    if ids.ndim != 1 or ids.dtype.kind not in "iu" or not len(ids):
        raise ValueError("root_ids must be a non-empty one-dimensional integer NPY")
    if ids.dtype.kind == "i" and np.any(ids < 0):
        raise ValueError("root_ids must be non-negative")
    ids = np.sort(ids.astype(np.uint64))
    if np.any(ids[1:] == ids[:-1]):
        raise ValueError("root_ids contains duplicates")
    if len(ids) > np.iinfo(np.uint32).max:
        raise OverflowError("Node count exceeds uint32")
    out.mkdir(parents=True, exist_ok=True)
    ids.astype("<u8").tofile(out / "nodes.u64")
    matched = _load_annotations(annotations, ids, out / "annotations.json")
    input_rows = dropped_rows = dropped_synapses = 0
    with tempfile.TemporaryDirectory(prefix="brain-runs-", dir=out) as temp:
        run_paths = []
        for i, cols in enumerate(connection_chunks(connections, chunk_rows)):
            rows = len(cols["syn_count"])
            input_rows += rows
            run_path = Path(temp) / f"run_{i:05}.npy"
            _, dropped, dropped_syn = _make_run(cols, ids, run_path)
            dropped_rows += dropped
            dropped_synapses += dropped_syn
            run_paths.append(run_path)
        edge_count, synapse_count = _merge_runs(run_paths, out, len(ids), min_synapses)

    files = ("nodes.u64", "offsets.u32", "targets.u32", "synapses.u32", "nt_probs.u8", "annotations.json")
    manifest = {
        "schema": "brain-csr-v1", "dataset": dataset,
        "node_count": len(ids), "edge_count": edge_count,
        "synapse_count": synapse_count, "min_synapses_per_edge": min_synapses,
        "input_rows": input_rows, "dropped_rows": dropped_rows,
        "dropped_synapses": dropped_synapses, "annotated_nodes": matched,
        "neurotransmitter_order": list(NT_NAMES),
        "neurotransmitter_encoding": "uint8 six-channel score; divide by 255; consult sources.connections.neurotransmitter_semantics",
        "node_id_encoding": "little-endian uint64; JSON IDs are decimal strings",
        "edge_encoding": "directed CSR; targets are uint32 node indexes; counts are uint32",
        "region_handling": "neuropil rows combined per ordered neuron pair; six transmitter channels weighted by syn_count",
        "sources": {
            "connections": {"file": connections.name, "sha256": sha256(connections), **source},
            "root_ids": {"file": root_ids.name, "sha256": sha256(root_ids)},
            "annotations": ({"file": annotations.name, "sha256": sha256(annotations)}
                            if annotations else None),
        },
        "files": {name: {"bytes": (out / name).stat().st_size, "sha256": sha256(out / name)}
                  for name in files},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    here = Path(__file__).resolve().parent
    data = here.parent / "data"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--connections", type=Path, default=data / "flywire_fafb_v783" / "proofread_connections_783.feather")
    parser.add_argument("--root-ids", type=Path, default=data / "flywire_fafb_v783" / "proofread_root_ids_783.npy")
    parser.add_argument("--annotations", type=Path, default=data / "flywire_annotations_v2.1.0" / "Supplemental_file1_neuron_annotations.tsv")
    parser.add_argument("--out", type=Path, default=here / "graph-v783")
    parser.add_argument("--dataset", default="flywire_fafb_v783")
    parser.add_argument("--min-synapses", type=int, default=1)
    parser.add_argument("--chunk-rows", type=int, default=1_000_000)
    args = parser.parse_args()
    for p in (args.connections, args.root_ids):
        if not p.is_file():
            parser.error(f"Input missing: {p}")
    if args.annotations is not None and not args.annotations.is_file():
        parser.error(f"Annotations missing: {args.annotations}")
    print(json.dumps(build(args.connections, args.root_ids, args.annotations, args.out,
                           args.dataset, args.min_synapses, args.chunk_rows), indent=2))


if __name__ == "__main__":
    main()
