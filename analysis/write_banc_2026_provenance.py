"""Verify selected BANC files against the official Dataverse checksums."""

from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/research_sources/other/banc_2026"


def main() -> None:
    catalog = json.loads((DATA / "dataverse_catalog.json").read_text(encoding="utf-8-sig"))
    catalog_files = {entry["filename"]: entry for entry in catalog["catalog"]}
    files = []
    for name in catalog["selected_files"]:
        official = catalog_files[name]
        path = DATA / name
        md5 = hashlib.md5()
        sha256 = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(16 * 1024 * 1024), b""):
                md5.update(chunk)
                sha256.update(chunk)
        actual_hex = md5.hexdigest()
        expected_hex = official["md5"].lower()
        actual_size = path.stat().st_size
        if actual_size != official["bytes"] or actual_hex != expected_hex:
            raise AssertionError(f"BANC checksum/size mismatch: {name}")
        files.append({
            "path": path.relative_to(ROOT).as_posix(),
            "source_url": f"https://dataverse.harvard.edu/api/access/datafile/{official['id']}",
            "dataverse_file_id": official["id"],
            "bytes": actual_size,
            "published_bytes": official["bytes"],
            "md5": actual_hex,
            "published_md5": expected_hex,
            "md5_base64": base64.b64encode(md5.digest()).decode("ascii"),
            "official_md5_base64": base64.b64encode(bytes.fromhex(expected_hex)).decode("ascii"),
            "sha256": sha256.hexdigest(),
            "verified": True,
        })
    provenance = {
        "dataset_doi": catalog["dataset_doi"],
        "dataset_url": "https://doi.org/10.7910/DVN/7WTH1N",
        "release": catalog["release"],
        "dataverse_dataset_id": catalog["dataverse_dataset_id"],
        "dataverse_version_number": catalog["dataverse_version_number"],
        "dataverse_version_minor_number": catalog["dataverse_version_minor_number"],
        "dataverse_version_id": catalog["dataverse_version_id"],
        "dataverse_release_time": catalog["dataverse_release_time"],
        "license": catalog["license"],
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "selected_file_count": len(files),
        "selected_total_bytes": sum(item["bytes"] for item in files),
        "files": files,
    }
    (DATA / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Verified {len(files)} BANC files / {provenance['selected_total_bytes']:,} bytes")


if __name__ == "__main__":
    main()
