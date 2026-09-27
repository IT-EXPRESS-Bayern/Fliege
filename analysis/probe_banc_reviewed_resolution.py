"""Inspect whether BANC reviewed-match query roots resolve to v888 metadata."""

import csv
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow.feather as feather

root = Path(__file__).resolve().parents[1]
data = root / "data/research_sources/other/banc_2026"
meta = feather.read_table(data / "banc_888_meta.feather", columns=[
    "banc_888_id", "root_626", "root_850", "root_888", "supervoxel_id", "fafb_match"
]).to_pylist()
current = {r["banc_888_id"] for r in meta}
crosswalk = defaultdict(set)
supervoxels = defaultdict(set)
for r in meta:
    for field in ("root_626", "root_850", "root_888"):
        if r[field] and r[field] != "NA":
            crosswalk[r[field]].add(r["banc_888_id"])
    if r["supervoxel_id"] and r["supervoxel_id"] != "NA":
        supervoxels[r["supervoxel_id"]].add(r["banc_888_id"])
with (root / "data/research_sources/derived/model_missing_fafb_ids.csv").open(encoding="utf-8-sig") as f:
    missing = {r["root_id"] for r in csv.DictReader(f)}
with (data / "banc_fafb_reviewed_matches.csv.gz").open(encoding="utf-8-sig") as f:
    rows = [r for r in csv.DictReader(f) if r["valid"] == "t" and r["match_id"] in missing]
counts = Counter()
covered = defaultdict(set)
conflicts = []
unresolved = []
for r in rows:
    sources = {
        "sv": supervoxels.get(r["pt_supervoxel_id"], set()),
        "pt_current": {r["pt_root_id"]} if r["pt_root_id"] in current else set(),
        "query_current": {r["query_id"]} if r["query_id"] in current else set(),
        "pt_old": crosswalk.get(r["pt_root_id"], set()),
        "query_old": crosswalk.get(r["query_id"], set()),
    }
    for name, values in sources.items():
        if values:
            counts[name] += 1
            covered[name].add(r["match_id"])
    if sources["sv"] and sources["pt_current"] and sources["sv"] != sources["pt_current"]:
        conflicts.append((r["match_id"], r["pt_root_id"], r["pt_supervoxel_id"], sources))
    if not any(sources.values()):
        unresolved.append((r["match_id"], r["pt_root_id"], r["query_id"], r["pt_supervoxel_id"]))
print("reviewed rows", len(rows), "FAFB IDs", len({r["match_id"] for r in rows}))
print("source row counts", counts)
print("covered FAFB IDs", {k:len(v) for k,v in covered.items()})
print("sv-vs-direct conflicts",len(conflicts), conflicts[:5])
print("unresolved rows", len(unresolved), unresolved[:10])
