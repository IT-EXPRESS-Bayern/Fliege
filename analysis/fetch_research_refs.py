"""Fetch pinned public model tables and validation material for the fly project.

The original FlyWire archive has its own downloader. These files are kept
separately because they are model inputs/results, not additional observations
of the FAFB specimen. GitHub files are verified against pinned Git blob IDs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "research_sources"
REPOS = {
    "shiu": ("philshiu/Drosophila_brain_model", "91bdd1e7dcf193f3e7ca5a8933497fcef63b7960"),
    "eon": ("eonsystemspbc/fly-brain", "a3db62f9436074e485c0278290c2164ed6150808"),
}
SMALL_PATHS = {
    "shiu": [
        "Completeness_783.csv", "example.ipynb", "figures.ipynb",
        "sez_neurons.pickle", "results/example/sugarR.parquet",
        "results/example/sugarR_100Hz.parquet",
    ],
    "eon": [
        "README.md", "LICENSE", "data/2025_Completeness_783.csv",
        "data/benchmark-results.csv", "data/results/nature_2026_07/manifest.csv",
        "data/results/nature_2026_07/checksums.sha256",
        "data/results/nature_2026_07/no_io/framework_summary.csv",
        "data/results/nature_2026_07/no_io/timing_summary.csv",
        "data/results/nature_2026_07/no_io/timings.csv",
        "code/benchmark.py", "code/run_brian2_cuda.py", "code/run_pytorch.py",
        "code/compare_ground_truth.py", "code/compare_spike_outputs.py",
        "main.py", "environment.yml",
    ],
}
SHIU_SUPPLEMENT = {
    "path": "shiu/supplementary_tables_1-12.xlsx",
    "url": "https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-024-07763-9/MediaObjects/41586_2024_7763_MOESM2_ESM.xlsx",
    "size": 2_539_037,
}


def request_json(url: str) -> dict:
    req = Request(url, headers={"User-Agent": "FlyWire-research-provenance/1"})
    with urlopen(req, timeout=60) as response:
        return json.load(response)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_blob_sha1(path: Path, size: int) -> str:
    digest = hashlib.sha1(f"blob {size}\0".encode())
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch(url: str, path: Path, size: int, blob_sha: str | None) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size == size and (
        blob_sha is None or git_blob_sha1(path, size) == blob_sha
    ):
        print(f"Verified existing: {path.relative_to(ROOT)}", flush=True)
    else:
        partial = path.with_name(path.name + ".partial")
        for attempt in range(5):
            offset = partial.stat().st_size if partial.exists() else 0
            if offset > size:
                raise ValueError(f"Partial file exceeds expected size: {partial}")
            headers = {"User-Agent": "FlyWire-research-provenance/1"}
            if offset:
                headers["Range"] = f"bytes={offset}-"
            try:
                with urlopen(Request(url, headers=headers), timeout=90) as response:
                    mode = "ab" if offset and response.status == 206 else "wb"
                    with partial.open(mode) as output:
                        while block := response.read(1024 * 1024):
                            output.write(block)
                if partial.stat().st_size == size:
                    break
            except (HTTPError, URLError, TimeoutError, OSError) as exc:
                print(f"Retry {attempt + 1}: {path.name}: {exc}", flush=True)
                time.sleep(min(2 ** attempt, 10))
        if not partial.exists() or partial.stat().st_size != size:
            raise ValueError(f"Incomplete download: {path}")
        if blob_sha is not None and git_blob_sha1(partial, size) != blob_sha:
            raise ValueError(f"Git blob mismatch: {path}")
        os.replace(partial, path)
        print(f"Downloaded and verified: {path.relative_to(ROOT)}", flush=True)
    return {
        "local_path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "source_url": url,
        "bytes": size,
        "sha256": sha256(path),
        "git_blob_sha1": blob_sha,
        "verified": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-large", action="store_true", help="Include the 100 MB Shiu v783 connectivity table")
    args = parser.parse_args()
    provenance = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Public pinned research/model sources; separate from original FAFB observations",
        "repos": {key: {"repo": repo, "commit": commit} for key, (repo, commit) in REPOS.items()},
        "files": [],
    }
    for key, (repo, commit) in REPOS.items():
        tree = request_json(f"https://api.github.com/repos/{repo}/git/trees/{commit}?recursive=1")
        entries = {item["path"]: item for item in tree["tree"] if item["type"] == "blob"}
        paths = list(SMALL_PATHS[key])
        if key == "shiu" and args.include_large:
            paths.append("Connectivity_783.parquet")
        for rel in paths:
            item = entries[rel]
            url = f"https://raw.githubusercontent.com/{repo}/{commit}/{rel}"
            provenance["files"].append(fetch(url, DEST / key / rel, item["size"], item["sha"]))
    provenance["files"].append(fetch(
        SHIU_SUPPLEMENT["url"], DEST / SHIU_SUPPLEMENT["path"],
        SHIU_SUPPLEMENT["size"], None,
    ))
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded {len(provenance['files'])} verified files", flush=True)


if __name__ == "__main__":
    main()
