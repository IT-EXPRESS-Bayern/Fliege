"""Empirically test, without changing sources, point-size cutoffs and region labels.

The official point and connection exports have different GCS update dates. A
best-fitting cutoff is descriptive only and does not prove the Codex pipeline.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
POINTS = HERE / "princeton_individual_points_for_616.csv"
CONNECTIONS = HERE / "princeton_unfiltered_for_616.csv"
R7_EXCEPTION = "720575940623940963"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    points = rows(POINTS)
    connections = {}
    for row in rows(CONNECTIONS):
        key = row["pre_root_id"], row["post_root_id"], row["neuropil"]
        n = int(row["synapse_count"])
        if key in connections and connections[key] != n:
            raise ValueError("Duplicate selected-root view differs")
        connections[key] = n
    candidates = []
    for threshold in range(1, 21):
     for exclude_autapses in (False, True):
      for exclude_R7 in (False, True):
       for align_blank in (False, True):
        grouped = Counter()
        for row in points:
            if int(row["size"]) < threshold:
                continue
            if exclude_autapses and row["pre_root_id"] == row["post_root_id"]:
                continue
            if exclude_R7 and R7_EXCEPTION in (row["pre_root_id"], row["post_root_id"]):
                continue
            region = "UNASGD" if align_blank and row["neuropil"] == "" else row["neuropil"]
            key = row["pre_root_id"], row["post_root_id"], region
            grouped[key] += 1
        keys = grouped.keys() | connections.keys()
        differences = {key: grouped[key] - connections.get(key, 0) for key in keys}
        nonzero = {key: diff for key, diff in differences.items() if diff}
        candidates.append({
            "minimum_size_inclusive": threshold,
            "exclude_autapses": exclude_autapses,
            "exclude_R7_original_exception_root": exclude_R7,
            "align_blank_point_region_to_UNASGD": align_blank,
            "point_calls_kept": sum(grouped.values()),
            "connection_synapse_sum": sum(connections.values()),
            "net_point_minus_connection": sum(nonzero.values()),
            "pair_region_key_mismatches": len(nonzero),
            "absolute_count_difference": sum(abs(d) for d in nonzero.values()),
            "point_only_keys": sum(key not in connections for key in nonzero),
            "connection_only_keys": sum(key not in grouped for key in nonzero),
        })
    candidates.sort(key=lambda r: (r["absolute_count_difference"], r["pair_region_key_mismatches"],
                                   r["minimum_size_inclusive"],
                                   not r["exclude_autapses"], not r["exclude_R7_original_exception_root"],
                                   not r["align_blank_point_region_to_UNASGD"]))
    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_point_gcs_updated": "2025-07-24T16:41:26.464Z",
        "source_connection_gcs_updated": "2025-07-08T14:11:22.534Z",
        "method": "For 616 selected v783 IDs, count point rows by exact directed pair/neuropil after each integer size cutoff, optional autapse and R7 exclusion, and optional blank-region alignment; compare with the official unfiltered Princeton connection export. No source edits.",
        "best_fit": candidates[0],
        "all_candidates_by_fit": candidates,
        "caution": "These are empirical, release-specific comparison rules, not official biological judgments. Counts from the same detector are reconciled, not additive. Original point rows remain preserved.",
    }
    (HERE / "princeton_filter_reconciliation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"best_fit": candidates[:5]}, indent=2))


if __name__ == "__main__":
    main()
