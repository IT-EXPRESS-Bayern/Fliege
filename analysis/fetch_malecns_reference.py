"""Fetch official MaleCNS v1.0 modeling reference tables with provenance.

The bulk EM, segmentation and synapse-point/partner files are deliberately not
part of this reference fetch. Run this script again to verify cached files.
"""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import pathlib
import urllib.parse
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "malecns_v1_reference"
GCS_BUCKET = "flyem-male-cns"
GCS_PREFIX = "v1.0/connectome-data/flat-connectome/"
GCS_FILES = (
    "body-annotations-male-cns-v1.0-minconf-0.5.feather",
    "body-neurotransmitters-male-cns-v1.0.feather",
    "connectome-weights-male-cns-v1.0-minconf-0.5-traced-only.feather",
)
GITHUB_REPO = "flyconnectome/2025malecns"
GITHUB_FILES = (
    "supplemental_data/quantify-neuron-connections.ipynb",
    "supplemental_data/dnan_cluster_function_20260509.csv",
    "supplemental_data/male-cns-v1.0-synapse-connection-precision-recall-by-roi.csv",
    "supplemental_data/male-cns-v1.0-synapse-tbar-precision-recall-by-roi.csv",
    "supplemental_data/male-cns-v1.0-traced-synapse-capture-by-roi.csv",
    "supplemental_data/mcns_fw_edge_comp_mappings.json",
    "supplemental_data/mcns_lvl_6_hsbm_communities.feather",
    "supplemental_data/optic-column-type-assignments-v1.0.xlsx",
    "supplemental_data/sensory_network_traversal_model_layers.feather",
)


def read_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "FlyResearch/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def fetch_file(url: str, target: pathlib.Path, expected_size: int) -> None:
    if target.exists() and target.stat().st_size == expected_size:
        return
    tmp = target.with_suffix(target.suffix + ".part")
    have = tmp.stat().st_size if tmp.exists() else 0
    if have > expected_size:
        tmp.unlink()
        have = 0
    headers = {"User-Agent": "FlyResearch/1.0"}
    if have:
        headers["Range"] = f"bytes={have}-"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as response:
        if have and response.status != 206:
            raise ValueError(f"server did not honor resume request for {target}")
        stream = tmp.open("ab" if have else "wb")
        with stream:
            while chunk := response.read(1024 * 1024):
                stream.write(chunk)
    if tmp.stat().st_size != expected_size:
        raise ValueError(f"wrong size: {target}: {tmp.stat().st_size} != {expected_size}")
    tmp.replace(target)


def hashes(path: pathlib.Path) -> dict[str, str]:
    h_md5 = hashlib.md5()
    h_sha256 = hashlib.sha256()
    size = path.stat().st_size
    h_blob = hashlib.sha1(f"blob {size}\0".encode())
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            h_md5.update(chunk)
            h_sha256.update(chunk)
            h_blob.update(chunk)
    return {
        "md5_base64": base64.b64encode(h_md5.digest()).decode(),
        "sha256": h_sha256.hexdigest(),
        "git_blob_sha1": h_blob.hexdigest(),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    for name in GCS_FILES:
        key = GCS_PREFIX + name
        metadata_url = (
            f"https://storage.googleapis.com/storage/v1/b/{GCS_BUCKET}/o/"
            + urllib.parse.quote(key, safe="")
        )
        meta = read_json(metadata_url)
        url = f"https://storage.googleapis.com/{GCS_BUCKET}/{key}"
        target = OUT / name
        fetch_file(url, target, int(meta["size"]))
        digest = hashes(target)
        if digest["md5_base64"] != meta["md5Hash"]:
            raise ValueError(f"official GCS MD5 mismatch: {target}")
        records.append(
            {
                "path": str(target.relative_to(ROOT)).replace("\\", "/"),
                "source_url": url,
                "metadata_url": metadata_url,
                "bytes": target.stat().st_size,
                "gcs_generation": meta["generation"],
                "gcs_updated": meta["updated"],
                "official_md5_base64": meta["md5Hash"],
                **digest,
            }
        )
        print(f"verified GCS {name}: {target.stat().st_size:,} bytes", flush=True)

    commit = read_json(f"https://api.github.com/repos/{GITHUB_REPO}/commits/main")
    revision = commit["sha"]
    tree = read_json(
        f"https://api.github.com/repos/{GITHUB_REPO}/git/trees/{revision}?recursive=1"
    )
    entries = {item["path"]: item for item in tree["tree"]}
    for path in GITHUB_FILES:
        item = entries[path]
        url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{revision}/{path}"
        target = OUT / pathlib.Path(path).name
        fetch_file(url, target, int(item["size"]))
        digest = hashes(target)
        if digest["git_blob_sha1"] != item["sha"]:
            raise ValueError(f"official Git blob SHA mismatch: {target}")
        records.append(
            {
                "path": str(target.relative_to(ROOT)).replace("\\", "/"),
                "source_url": url,
                "bytes": target.stat().st_size,
                "github_commit": revision,
                "official_git_blob_sha1": item["sha"],
                **digest,
            }
        )
        print(f"verified GitHub {path}: {target.stat().st_size:,} bytes", flush=True)

    manifest = {
        "dataset": "MaleCNS v1.0 modeling reference",
        "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "license": "CC-BY 4.0 (MaleCNS dataset); supplemental repository license to check per file",
        "scope": "metadata, traced-only graph and derived author analysis tables; no EM image volume",
        "project": "https://male-cns.janelia.org/",
        "download_page": "https://male-cns.janelia.org/download/",
        "paper": "https://doi.org/10.1016/j.cell.2026.08.015",
        "supplemental_repository": f"https://github.com/{GITHUB_REPO}",
        "supplemental_commit": revision,
        "files": records,
    }
    path = OUT / "provenance.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path}", flush=True)


if __name__ == "__main__":
    main()
