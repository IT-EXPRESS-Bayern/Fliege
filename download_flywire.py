"""Download and verify the published FlyWire FAFB v783 reconstruction.

Only derived connectome and morphology files are downloaded; electron
microscopy image volumes are intentionally excluded. Downloads are resumable
and split into HTTP ranges so Zenodo's per-connection speed is less limiting.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import subprocess
import threading
import time
from pathlib import Path


ZENODO_RECORDS = (10676866, 10877326)
ANNOTATION_URL = (
    "https://raw.githubusercontent.com/flyconnectome/flywire_annotations/"
    "v2.1.0/supplemental_files/Supplemental_file1_neuron_annotations.tsv"
)
ANNOTATION_SIZE = 27_015_208
ANNOTATION_GIT_BLOB_SHA1 = "1a3168731618ee62a47392252d3af7664e739e9e"
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def fetch_json(url: str) -> dict:
    result = subprocess.run(
        ["curl.exe", "--location", "--fail", "--silent", "--show-error", "--max-time", "30", url],
        check=True,
        capture_output=True,
        timeout=35,
    )
    return json.loads(result.stdout)


def md5sum(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as source:
        while block := source.read(8 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def download_file(entry: dict, output: Path, chunk_size: int, workers: int) -> None:
    size = entry["size"]
    wanted_hash = entry["checksum"].split(":", 1)[1].lower()
    url = entry["links"]["self"]
    output.parent.mkdir(parents=True, exist_ok=True)

    if output.exists() and output.stat().st_size == size:
        print(f"Checking existing {output.name} ...", flush=True)
        if md5sum(output) == wanted_hash:
            print(f"Verified: {output.name}", flush=True)
            return

    part_path = output.with_name(output.name + ".partial")
    state_path = output.with_name(output.name + ".progress.json")
    n_parts = (size + chunk_size - 1) // chunk_size
    if state_path.exists() and part_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("size") != size or state.get("chunk_size") != chunk_size:
            raise RuntimeError(f"Resume parameters changed for {output.name}")
        done = set(state["completed"])
    else:
        done = set()
        with part_path.open("wb") as target:
            target.truncate(size)
    lock = threading.Lock()
    started = time.monotonic()
    last_report = [0]

    def save_state() -> None:
        temp = state_path.with_name(state_path.name + ".tmp")
        temp.write_text(
            json.dumps(
                {"size": size, "chunk_size": chunk_size, "completed": sorted(done)},
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        os.replace(temp, state_path)

    def fetch_part(index: int) -> None:
        start = index * chunk_size
        end = min(size - 1, start + chunk_size - 1)
        expected = end - start + 1
        chunk_path = part_path.with_name(f"{part_path.name}.{index}.chunk")
        for attempt in range(9):
            try:
                subprocess.run(
                    [
                        "curl.exe", "--location", "--fail", "--silent", "--show-error",
                        "--connect-timeout", "15", "--max-time", "180",
                        "--max-filesize", str(expected), "--range", f"{start}-{end}",
                        "--output", str(chunk_path), url,
                    ],
                    check=True,
                    capture_output=True,
                    timeout=190,
                )
                received = chunk_path.stat().st_size
                if received != expected:
                    raise RuntimeError(f"Received {received} bytes, expected {expected}")
                with chunk_path.open("rb") as source, part_path.open("r+b", buffering=0) as target:
                    target.seek(start)
                    while block := source.read(1024 * 1024):
                        target.write(block)
                chunk_path.unlink()
                with lock:
                    done.add(index)
                    save_state()
                    completed_bytes = min(size, len(done) * chunk_size)
                    if completed_bytes - last_report[0] >= 128 * 1024 * 1024 or len(done) == n_parts:
                        elapsed = max(1, time.monotonic() - started)
                        print(
                            f"{output.name}: {len(done)}/{n_parts} parts, "
                            f"~{completed_bytes / 1e9:.2f}/{size / 1e9:.2f} GB, "
                            f"{completed_bytes / elapsed / 1e6:.2f} MB/s",
                            flush=True,
                        )
                        last_report[0] = completed_bytes
                return
            except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired, RuntimeError) as error:
                chunk_path.unlink(missing_ok=True)
                if attempt == 8:
                    detail = error.stderr.decode(errors="replace")[-300:] if isinstance(error, subprocess.CalledProcessError) and error.stderr else str(error)
                    raise RuntimeError(f"Failed chunk {index} of {output.name}: {detail}") from error
                time.sleep(min(60, 2**attempt))

    pending = (index for index in range(n_parts) if index not in done)
    print(f"Downloading {output.name} ({size / 1e9:.2f} GB) ...", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for _ in pool.map(fetch_part, pending):
            pass
    print(f"Checking MD5: {output.name} ...", flush=True)
    got_hash = md5sum(part_path)
    if got_hash != wanted_hash:
        raise RuntimeError(f"MD5 mismatch for {output.name}: {got_hash} != {wanted_hash}")
    os.replace(part_path, output)
    state_path.unlink(missing_ok=True)
    print(f"Verified: {output.name}", flush=True)


def download_annotation() -> None:
    output = DATA / "flywire_annotations_v2.1.0" / "Supplemental_file1_neuron_annotations.tsv"
    output.parent.mkdir(parents=True, exist_ok=True)
    def annotation_valid(path: Path) -> bool:
        if not path.exists() or path.stat().st_size != ANNOTATION_SIZE:
            return False
        digest = hashlib.sha1()
        digest.update(f"blob {ANNOTATION_SIZE}\0".encode())
        with path.open("rb") as source:
            while block := source.read(8 * 1024 * 1024):
                digest.update(block)
        return digest.hexdigest() == ANNOTATION_GIT_BLOB_SHA1

    if annotation_valid(output):
        print(f"Verified: {output.name}", flush=True)
        return
    temp = output.with_name(output.name + ".partial")
    subprocess.run(
        ["curl.exe", "--location", "--fail", "--show-error", "--silent", "--continue-at", "-", "--output", str(temp), ANNOTATION_URL],
        check=True,
        timeout=600,
    )
    if not annotation_valid(temp):
        raise RuntimeError(f"Annotation download failed integrity check: {temp}")
    os.replace(temp, output)
    print(f"Downloaded {output} ({output.stat().st_size / 1e6:.1f} MB)", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--chunk-mib", type=int, default=4)
    parser.add_argument("--record", type=int, choices=ZENODO_RECORDS, action="append")
    parser.add_argument("--only", action="append", help="Only download the named archive file; repeatable")
    parser.add_argument("--skip-annotation", action="store_true")
    args = parser.parse_args()
    if not args.skip_annotation:
        download_annotation()
    records = args.record or list(ZENODO_RECORDS)
    for record_id in records:
        metadata = fetch_json(f"https://zenodo.org/api/records/{record_id}")
        record_dir = DATA / ("flywire_fafb_v783" if record_id == 10676866 else "flywire_morphology_v783")
        record_dir.mkdir(parents=True, exist_ok=True)
        (record_dir / "zenodo_record.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        priorities = {
            "proofread_root_ids_783.npy": 0,
            "proofread_connections_783.feather": 1,
            "per_neuron_neuropil_count_pre_783.feather": 2,
            "per_neuron_neuropil_count_post_783.feather": 3,
            "sk_lod1_783_healed_ds2.parquet": 4,
            "flywire_synapses_783.feather": 5,
        }
        entries = sorted(metadata["files"], key=lambda item: priorities.get(item["key"], 10))
        for entry in entries:
            if args.only and entry["key"] not in args.only:
                continue
            download_file(entry, record_dir / entry["key"], args.chunk_mib * 1024 * 1024, args.workers)


if __name__ == "__main__":
    main()
