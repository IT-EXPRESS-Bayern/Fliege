"""Fetch only two small BANC-v888 cross-specimen reference tables.

Both objects come from the public BANC GCS bucket. This script checks the
published object size and GCS MD5 before replacing a local file, and records
SHA-256 plus object generations for a repeatable inventory. BANC and FAFB
come from different individual flies; these tables only describe matches.
"""

from __future__ import annotations

import base64
import concurrent.futures
import hashlib
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


BUCKET = "lee-lab_brain-and-nerve-cord-fly-connectome"
OBJECTS = (
    "nblast/banc_fafb_reviewed_matches.csv",
    "neuron_annotations/v888/codex_annotations_flat_table_260520.csv",
)
DESTINATION = Path(__file__).resolve().parent.parent / "data" / "banc_v888"


def object_metadata(name: str) -> tuple[dict, str]:
    url = f"https://storage.googleapis.com/storage/v1/b/{BUCKET}/o/{quote(name, safe='')}"
    with urlopen(url, timeout=60) as response:
        return json.load(response), url


def hash_file(path: Path) -> tuple[str, str, int]:
    sha = hashlib.sha256()
    md5 = hashlib.md5()
    total = 0
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(4 * 1024 * 1024), b""):
            total += len(chunk)
            sha.update(chunk)
            md5.update(chunk)
    return sha.hexdigest(), base64.b64encode(md5.digest()).decode("ascii"), total


def ensure_object(name: str) -> dict:
    meta, meta_url = object_metadata(name)
    expected_size = int(meta["size"])
    expected_md5 = meta["md5Hash"]
    download_url = f"https://storage.googleapis.com/{BUCKET}/{quote(name, safe='/')}"
    destination = DESTINATION / Path(name).name
    if destination.is_file():
        sha, md5, size = hash_file(destination)
        if size == expected_size and md5 == expected_md5:
            return provenance(name, destination, meta, meta_url, download_url, sha, size)

    temporary = destination.with_name(destination.name + ".part")
    progress = destination.with_name(destination.name + ".progress.json")
    chunk_size = 256 * 1024
    part_count = (expected_size + chunk_size - 1) // chunk_size
    if temporary.is_file() and progress.is_file():
        state = json.loads(progress.read_text(encoding="utf-8"))
        if (state.get("generation") != meta["generation"] or
                state.get("chunk_size") != chunk_size or
                temporary.stat().st_size != expected_size):
            raise ValueError(f"Stale partial download: {temporary}")
        completed = set(state["completed"])
    else:
        completed = set()
        with temporary.open("wb") as output:
            output.truncate(expected_size)
    lock = threading.Lock()

    def fetch_range(index: int) -> None:
        start = index * chunk_size
        end = min(expected_size - 1, start + chunk_size - 1)
        request = Request(download_url, headers={"Range": f"bytes={start}-{end}"})
        for attempt in range(4):
            try:
                with urlopen(request, timeout=60) as response:
                    if response.status != 206:
                        raise ValueError(f"Server ignored Range: HTTP {response.status}")
                    wanted_range = f"bytes {start}-{end}/{expected_size}"
                    if response.headers.get("Content-Range") != wanted_range:
                        raise ValueError(f"Wrong Content-Range for part {index}")
                    data = response.read()
                if len(data) != end - start + 1:
                    raise ValueError(f"Short range {index}: {len(data)} bytes")
                with lock:
                    with temporary.open("r+b") as output:
                        output.seek(start)
                        output.write(data)
                    completed.add(index)
                    new_state = {"generation": meta["generation"],
                                 "chunk_size": chunk_size, "completed": sorted(completed)}
                    next_progress = progress.with_name(progress.name + ".tmp")
                    next_progress.write_text(json.dumps(new_state), encoding="utf-8")
                    os.replace(next_progress, progress)
                    if len(completed) % 20 == 0 or len(completed) == part_count:
                        print(f"{destination.name}: {len(completed)}/{part_count} ranges", flush=True)
                return
            except (OSError, ValueError):
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)

    pending = [index for index in range(part_count) if index not in completed]
    print(f"Downloading {destination.name}: {len(pending)} ranges pending", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(fetch_range, pending))
    sha, actual_md5, size = hash_file(temporary)
    if size != expected_size or actual_md5 != expected_md5:
        raise ValueError(f"Checksum mismatch for {name}: {size} bytes, MD5 {actual_md5}")
    os.replace(temporary, destination)
    progress.unlink(missing_ok=True)
    return provenance(name, destination, meta, meta_url, download_url, sha, size)


def provenance(name: str, destination: Path, meta: dict, meta_url: str,
               download_url: str, sha256: str, size: int) -> dict:
    return {
        "object_name": name,
        "local_file": destination.name,
        "download_url": download_url,
        "metadata_url": meta_url,
        "bytes": size,
        "gcs_md5_base64_verified": meta["md5Hash"],
        "sha256": sha256,
        "gcs_generation": meta["generation"],
        "gcs_updated": meta["updated"],
    }


def main() -> None:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    files = [ensure_object(name) for name in OBJECTS]
    record = {
        "dataset": "BANC v888",
        "citable_static_deposit": "https://doi.org/10.7910/DVN/7WTH1N",
        "license": "CC BY 4.0 per https://github.com/htem/BANC-project#license",
        "source": "Public BANC GCS bucket; mutable objects at the recorded generations",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "usage": "Cross-specimen FAFB-v783-to-BANC-v888 reference only; not the missing nerve cord of the FAFB fly",
        "files": files,
    }
    output = DESTINATION / "reference_provenance.json"
    temporary = DESTINATION / "reference_provenance.json.part"
    temporary.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, output)
    for item in files:
        print(f"Verified {item['local_file']}: {item['bytes']} bytes, sha256 {item['sha256']}")


if __name__ == "__main__":
    main()
