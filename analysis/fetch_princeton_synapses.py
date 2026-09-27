"""Resume and verify the newer Princeton synapse exports for FAFB v783.

These are a second detector on the same EM specimen, not a new FAFB neuron
release. No electron-microscopy images are fetched.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "codex_fafb_v783"
STATE = ROOT / "logs" / "princeton_download_state.json"
MANIFEST = OUT / "princeton_provenance.json"
BUCKET = "flywire-data"
PREFIX = "codex/data/fafb/783/"
FILES = (
    "connections_princeton_no_threshold.csv.gz",
    "fafb_v783_princeton_synapse_table.csv.gz",
)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def mark(stage: str, name: str = "", **extra: object) -> None:
    state = {"stage": stage, "file": name, "updated_utc": datetime.now(timezone.utc).isoformat(), **extra}
    write_json(STATE, state)
    print(json.dumps(state, ensure_ascii=False), flush=True)


def metadata(name: str) -> dict:
    object_name = PREFIX + name
    url = f"https://storage.googleapis.com/storage/v1/b/{BUCKET}/o/{quote(object_name, safe='')}"
    for attempt in range(5):
        try:
            with urlopen(url, timeout=30) as response:
                data = json.load(response)
            if data["name"] != object_name or not data.get("md5Hash"):
                raise ValueError(f"Unexpected GCS metadata for {name}")
            return data
        except (OSError, ValueError, KeyError):
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def hashes(path: Path) -> tuple[str, str]:
    md5, sha256 = hashlib.md5(), hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b""):
            md5.update(block)
            sha256.update(block)
    return base64.b64encode(md5.digest()).decode("ascii"), sha256.hexdigest()


def fetch(name: str) -> dict:
    meta = metadata(name)
    expected_size = int(meta["size"])
    wanted_md5 = meta["md5Hash"]
    output = OUT / name
    part = OUT / (name + ".part")
    source_url = f"https://storage.googleapis.com/{BUCKET}/{PREFIX}{name}"
    if output.is_file():
        if output.stat().st_size != expected_size or hashes(output)[0] != wanted_md5:
            raise RuntimeError(f"Existing {name} fails official GCS size/MD5 check")
        mark("verified", name, bytes=expected_size, reused=True)
    else:
        for attempt in range(1, 11):
            current = part.stat().st_size if part.exists() else 0
            if current > expected_size:
                raise RuntimeError(f"Partial file exceeds official size: {name}")
            mark("download", name, attempt=attempt, bytes_done=current, bytes_total=expected_size)
            if current < expected_size:
                command = [
                    "curl.exe", "--location", "--fail", "--silent", "--show-error",
                    "--retry", "5", "--retry-all-errors", "--retry-delay", "3",
                    "--connect-timeout", "20", "--max-time", "3600",
                    "--continue-at", "-", "--output", str(part), source_url,
                ]
                result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
                if result.returncode:
                    mark("retry", name, attempt=attempt, bytes_done=part.stat().st_size if part.exists() else 0,
                         bytes_total=expected_size, error=result.stderr[-400:])
                    time.sleep(min(120, 5 * attempt))
                    continue
            if part.stat().st_size != expected_size:
                mark("retry", name, attempt=attempt, bytes_done=part.stat().st_size,
                     bytes_total=expected_size, error="Incomplete transfer")
                time.sleep(min(120, 5 * attempt))
                continue
            mark("checking_md5", name, bytes_done=expected_size, bytes_total=expected_size)
            found_md5, _ = hashes(part)
            if found_md5 != wanted_md5:
                raise RuntimeError(f"Official GCS MD5 mismatch for {name}; preserved {part}")
            os.replace(part, output)
            mark("verified", name, bytes=expected_size, reused=False)
            break
        else:
            raise RuntimeError(f"Could not finish {name} after 10 resumable attempts")
    found_md5, found_sha256 = hashes(output)
    return {
        "path": str(output.relative_to(ROOT)).replace("\\", "/"),
        "source_url": source_url,
        "metadata_url": f"https://storage.googleapis.com/storage/v1/b/{BUCKET}/o/{quote(PREFIX + name, safe='')}",
        "bytes": expected_size,
        "gcs_generation": meta.get("generation"),
        "gcs_updated": meta.get("updated"),
        "official_md5_base64": wanted_md5,
        "md5_base64": found_md5,
        "sha256": found_sha256,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files: list[dict] = []
    for name in FILES:
        files.append(fetch(name))
        write_json(MANIFEST, {
            "dataset": "FAFB v783, 2025 Princeton synapse detector",
            "source": "https://codex.flywire.ai/api/download?dataset=fafb",
            "paper": "https://doi.org/10.1101/2025.07.11.664377",
            "version_note": "Same v783 segmentation/root IDs as the older Buhmann detector; keep releases separate",
            "scope": "Connectivity and synapse point exports only; no EM images",
            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
            "files": files,
        })
    mark("complete", bytes=sum(row["bytes"] for row in files), file_count=len(files))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        mark("error", error=str(error))
        raise
