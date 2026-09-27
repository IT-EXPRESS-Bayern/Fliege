"""Summarize independent original-point and Princeton coverage for the 616 roots."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MISSING = ROOT / "data/research_sources/derived/model_missing_fafb_ids.csv"
ROOT_QUEUE = HERE / "root_review_queue.csv"
PRINCETON_ROOTS = HERE / "princeton_root_coverage_616.csv"
UNFILTERED = HERE / "princeton_unfiltered_for_616.csv"
FILTERED = HERE / "princeton_filtered_ge5_pair_for_616.csv"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def kind(row: dict[str, str]) -> str:
    cell_type = row["cell_type"]
    if cell_type in ("R1-6", "R7", "R8"):
        return cell_type
    if row["cell_class"] == "visual":
        return "other_visual"
    return "nonvisual_or_untyped"


def count_bin(count: int) -> str:
    if count == 1:
        return "1"
    if count <= 4:
        return "2-4"
    if count <= 9:
        return "5-9"
    if count <= 19:
        return "10-19"
    if count <= 49:
        return "20-49"
    return "50+"


def unique_pair_region(records: list[dict[str, str]]) -> dict[tuple[str, str, str], int]:
    distinct = {}
    for row in records:
        key = (row["pre_root_id"], row["post_root_id"], row["neuropil"])
        count = int(row["synapse_count"])
        if key in distinct and distinct[key] != count:
            raise ValueError("Duplicated selected-root view has inconsistent count")
        distinct[key] = count
    return distinct


def source_stats(path: Path, missing: dict[str, dict]) -> dict:
    data = rows(path)
    keys = unique_pair_region(data)
    pairs = defaultdict(int)
    regions = Counter()
    root_type_pair_occurrences = Counter()
    root_type_synapse_occurrences = Counter()
    by_region = Counter()
    for (pre, post, region), count in keys.items():
        pairs[(pre, post)] += count
        regions[region] += 1
        by_region[region] += count
        for root_id in {pre, post} & missing.keys():
            category = kind(missing[root_id])
            root_type_pair_occurrences[category] += 1
            root_type_synapse_occurrences[category] += count
    return {
        "selected_root_rows_in_output": len(data),
        "distinct_pair_region_rows": len(keys),
        "distinct_directed_pairs": len(pairs),
        "distinct_pair_region_synapse_sum": sum(keys.values()),
        "pair_synapse_count_bins": dict(sorted(Counter(count_bin(n) for n in pairs.values()).items())),
        "pair_region_count_bins": dict(sorted(Counter(count_bin(n) for n in keys.values()).items())),
        "by_neuropil_pair_region_rows": dict(regions.most_common()),
        "by_neuropil_synapse_count": dict(by_region.most_common()),
        "selected_root_type_pair_region_occurrences": dict(root_type_pair_occurrences),
        "selected_root_type_synapse_count_occurrences": dict(root_type_synapse_occurrences),
        "distinct_pairs_with_both_ends_among_616": sum(pre in missing and post in missing for pre, post in pairs),
    }


def main() -> None:
    missing_rows = rows(MISSING)
    missing = {row["root_id"]: row for row in missing_rows}
    queue = {row["root_id"]: row for row in rows(ROOT_QUEUE)}
    p_roots = {row["root_id"]: row for row in rows(PRINCETON_ROOTS)}
    if set(missing) != set(queue) or set(missing) != set(p_roots) or len(missing) != 616:
        raise ValueError("Root ID mismatch among 616-row sources")
    root_categories = defaultdict(Counter)
    old_and_new = Counter()
    new_only = []
    old_only = []
    neither = []
    for root_id, meta in missing.items():
        category = kind(meta)
        old = int(queue[root_id]["all_released_pre_points"]) + int(queue[root_id]["all_released_post_points"]) > 0
        new = int(p_roots[root_id]["Princeton_unfiltered_synapse_count"]) > 0
        filtered = int(p_roots[root_id]["Princeton_filtered_synapse_count"]) > 0
        key = ("old_raw_yes" if old else "old_raw_no") + "__" + ("new_detector_yes" if new else "new_detector_no")
        root_categories[category]["total"] += 1
        root_categories[category]["old_raw_point_roots"] += old
        root_categories[category]["Princeton_unfiltered_roots"] += new
        root_categories[category]["Princeton_filtered_roots"] += filtered
        root_categories[category][key] += 1
        old_and_new[key] += 1
        if new and not old:
            new_only.append(root_id)
        elif old and not new:
            old_only.append(root_id)
        elif not old and not new:
            neither.append(root_id)
    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "release_comparison": "Original Buhmann-v783 raw-point coverage versus Princeton-2025 same-specimen re-detection",
        "root_coverage_intersection": dict(old_and_new),
        "root_coverage_by_type": {k: dict(v) for k, v in sorted(root_categories.items())},
        "new_detector_only_root_ids": new_only,
        "old_raw_only_root_ids": old_only,
        "neither_source_root_ids": neither,
        "filtered_source": source_stats(FILTERED, missing),
        "unfiltered_source": source_stats(UNFILTERED, missing),
        "interpretation": "Counts are source-specific automated synapse calls and must not be added. Selected-root type occurrences count a pair twice when both ends are among the 616; distinct pair totals do not.",
    }
    (HERE / "princeton_strata.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"root_coverage_intersection": result["root_coverage_intersection"],
                      "root_coverage_by_type": result["root_coverage_by_type"],
                      "filtered_pair_bins": result["filtered_source"]["pair_synapse_count_bins"],
                      "unfiltered_pair_bins": result["unfiltered_source"]["pair_synapse_count_bins"]}, indent=2))


if __name__ == "__main__":
    main()
