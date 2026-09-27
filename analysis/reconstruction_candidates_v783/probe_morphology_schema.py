"""Metadata-only schema probe for the *verified final* v783 skeleton parquet.

This deliberately does not infer a neuron-to-neuron connection from geometry.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/flywire_morphology_v783/sk_lod1_783_healed_ds2.parquet"
RECORD = ROOT / "data/flywire_morphology_v783/zenodo_record.json"
OUT = Path(__file__).resolve().parent / "morphology_schema_probe.json"


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError("Verified final skeleton parquet pending; partial file must not be read")
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    source = [r for r in record.get("files", []) if r.get("key") == SOURCE.name]
    if len(source) != 1 or SOURCE.stat().st_size != source[0]["size"]:
        raise ValueError("Final file size does not match published Zenodo record")
    parquet = pq.ParquetFile(SOURCE)
    schema = parquet.schema_arrow
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "source_url": "https://zenodo.org/records/10877326",
        "published_md5": source[0]["checksum"],
        "file_bytes": SOURCE.stat().st_size,
        "metadata_only": True,
        "rows": parquet.metadata.num_rows,
        "row_groups": parquet.num_row_groups,
        "columns": [{"name": f.name, "type": str(f.type), "nullable": f.nullable} for f in schema],
        "schema": str(schema),
        "interpretation": "This is a schema inventory, not proof of a particular segment identity or a new synapse.",
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("rows", "row_groups", "columns")}, indent=2))


if __name__ == "__main__":
    main()
