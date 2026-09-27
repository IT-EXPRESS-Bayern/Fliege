"""Integrity and minimal graph audit for the two public BANC v888 edgelists.

Run with analysis/.venv/Scripts/python.exe after fetch_banc_2026.ps1 completes.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as feather
import pyarrow.ipc as ipc


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/research_sources/other/banc_2026"
NAMES = (
    "banc_888_edgelist_simple_v2.feather",
    "banc_888_edgelist_simple_v3.feather",
)


def md5_file(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(16 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    catalog = json.loads((DATA / "dataverse_catalog.json").read_text(encoding="utf-8-sig"))
    listing = {item["filename"]: item for item in catalog["catalog"]}
    meta_name = "banc_888_meta.feather"
    meta_path = DATA / meta_name
    assert meta_path.exists(), f"Missing {meta_name}"
    meta_expected = listing[meta_name]
    assert meta_path.stat().st_size == meta_expected["bytes"]
    assert md5_file(meta_path) == meta_expected["md5"]
    meta = feather.read_table(meta_path, columns=["banc_888_id"])
    meta_ids = set(int(v) for v in pc.unique(meta["banc_888_id"]).to_pylist() if v is not None)
    summary = {
        "dataset": "Harvard Dataverse doi:10.7910/DVN/7WTH1N",
        "release": "BANC v888",
        "license": catalog["license"],
        "meta_rows": meta.num_rows,
        "meta_unique_banc_ids": len(meta_ids),
        "edgelists": {},
    }
    for name in NAMES:
        path = DATA / name
        if not path.exists():
            summary["edgelists"][name] = {"status": "missing"}
            continue
        expected = listing[name]
        size = path.stat().st_size
        md5 = md5_file(path)
        assert size == expected["bytes"], f"Size mismatch: {name}"
        assert md5 == expected["md5"], f"MD5 mismatch: {name}"
        pre_ids: set[int] = set()
        post_ids: set[int] = set()
        total_rows = 0
        total_synapses = 0
        min_count = None
        max_count = None
        autapses = 0
        with pa.memory_map(str(path), "r") as mapped:
            reader = ipc.open_file(mapped)
            columns = reader.schema.names
            for i in range(reader.num_record_batches):
                batch = reader.get_batch(i)
                pre = batch.column("pre").to_numpy(zero_copy_only=False)
                post = batch.column("post").to_numpy(zero_copy_only=False)
                count = batch.column("count").to_numpy(zero_copy_only=False)
                total_rows += batch.num_rows
                total_synapses += int(np.sum(count, dtype=np.int64))
                min_count = int(np.min(count)) if min_count is None else min(min_count, int(np.min(count)))
                max_count = int(np.max(count)) if max_count is None else max(max_count, int(np.max(count)))
                autapses += int(np.sum(pre == post))
                pre_ids.update(int(v) for v in np.unique(pre))
                post_ids.update(int(v) for v in np.unique(post))
        all_ids = pre_ids | post_ids
        summary["edgelists"][name] = {
            "status": "verified",
            "bytes": size,
            "md5": md5,
            "columns": columns,
            "directed_pair_rows": total_rows,
            "synapse_count_sum": total_synapses,
            "unique_pre_ids": len(pre_ids),
            "unique_post_ids": len(post_ids),
            "unique_incident_ids": len(all_ids),
            "incident_ids_missing_from_meta": len(all_ids - meta_ids),
            "min_pair_count": min_count,
            "max_pair_count": max_count,
            "autapse_rows": autapses,
        }
        print(f"Audited {name}: {total_rows:,} pairs, {total_synapses:,} synapses", flush=True)
    (DATA / "edgelist_audit.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
