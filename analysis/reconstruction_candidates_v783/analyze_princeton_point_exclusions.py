"""Explain why the official Princeton point and connection files differ."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
POINTS = HERE / "princeton_individual_points_for_616.csv"
CONNECTIONS = HERE / "princeton_unfiltered_for_616.csv"
ROOTS = HERE / "princeton_root_coverage_616.csv"
R7 = "720575940623940963"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    points = read_csv(POINTS)
    root_rows = read_csv(ROOTS)
    connection_roots = {r["root_id"] for r in root_rows if int(r["Princeton_unfiltered_synapse_count"]) > 0}
    point_roots = set()
    self_rows = 0
    r7_rows = 0
    r7_nonself = 0
    blank_rows = 0
    blank_after_exclusion = 0
    per_root = defaultdict(Counter)
    retained = Counter()
    R7_keys = Counter()
    for row in points:
        roots = row["selected_root_ids"].split(";")
        point_roots.update(roots)
        is_self = row["pre_root_id"] == row["post_root_id"]
        is_r7 = R7 in (row["pre_root_id"], row["post_root_id"])
        blank = not row["neuropil"]
        self_rows += is_self
        r7_rows += is_r7
        r7_nonself += is_r7 and not is_self
        blank_rows += blank
        blank_after_exclusion += blank and not is_self and not is_r7
        for root_id in roots:
            per_root[root_id]["all"] += 1
            per_root[root_id]["self"] += is_self
            per_root[root_id]["R7"] += is_r7
            per_root[root_id]["nonself_nonR7"] += not is_self and not is_r7
        if is_r7 and not is_self:
            R7_keys[(row["pre_root_id"], row["post_root_id"], row["neuropil"])] += 1
        if is_self or is_r7:
            continue
        region = row["neuropil"] or "UNASGD"
        retained[(row["pre_root_id"], row["post_root_id"], region)] += 1
    if len(point_roots) != 550 or len(connection_roots) != 477:
        raise ValueError("Unexpected root coverage")
    connection_groups = {}
    for row in read_csv(CONNECTIONS):
        key = row["pre_root_id"], row["post_root_id"], row["neuropil"]
        n = int(row["synapse_count"])
        if key in connection_groups and connection_groups[key] != n:
            raise ValueError("Duplicate selected-root view has inconsistent count")
        connection_groups[key] = n
    if retained != connection_groups:
        raise ValueError("Empirical point-to-connection reconciliation is not exact")
    point_only = point_roots - connection_roots
    point_only_rows = []
    for root_id in sorted(point_only):
        stat = per_root[root_id]
        klass = "R7_nonself_exception" if root_id == R7 else "autapse_only" if stat["all"] == stat["self"] else "other"
        point_only_rows.append({
            "root_id": root_id,
            "Princeton_point_rows": stat["all"],
            "autapse_point_rows": stat["self"],
            "R7_exception_point_rows": stat["R7"],
            "point_only_class": klass,
            "interpretation": "Observed point rows omitted from connection export under empirical release comparison; not a published pair edge",
        })
    with (HERE / "princeton_point_only_73_roots.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(point_only_rows[0]))
        writer.writeheader()
        writer.writerows(point_only_rows)
    audit = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "point_rows_touching_616": len(points),
            "point_roots": len(point_roots),
            "connection_roots": len(connection_roots),
            "point_only_roots": len(point_only),
            "point_only_root_classes": dict(Counter(r["point_only_class"] for r in point_only_rows)),
            "autapse_rows": self_rows,
            "R7_rows_total": r7_rows,
            "R7_rows_nonself": r7_nonself,
            "R7_rows_self": r7_rows - r7_nonself,
            "raw_blank_neuropil_rows": blank_rows,
            "blank_neuropil_rows_after_exclusions": blank_after_exclusion,
            "retained_rows": sum(retained.values()),
            "retained_pair_region_keys": len(retained),
            "R7_nonself_pair_region_keys": len(R7_keys),
            "R7_nonself_points": sum(R7_keys.values()),
        },
        "checks": {
            "point_rows_equal_autapses_plus_R7_nonself_plus_connection_rows":
                len(points) == self_rows + r7_nonself + sum(retained.values()),
            "retained_point_groups_equal_unfiltered_connection_groups_exactly": retained == connection_groups,
            "root_coverage_point_only_explained": len(point_only_rows) == 73 and all(
                r["point_only_class"] != "other" for r in point_only_rows),
        },
        "method": "Exclude same-ID autapses, then all remaining rows involving the specific R7 root 720575940623940963; map empty point-region label to UNASGD only for comparison. The remaining directed pair+region counts match the official no-threshold Princeton connection export exactly. This is an empirical reconciliation, not a documented biological or canonical filter.",
        "source_subrelease_dates": {
            "point_export_GCS_updated": "2025-07-24T16:41:26.464Z",
            "connection_export_GCS_updated": "2025-07-08T14:11:22.534Z",
        },
        "R7_nonself_pairs": [
            {"pre_root_id": pre, "post_root_id": post, "neuropil": region, "point_rows": n}
            for (pre, post, region), n in R7_keys.most_common()
        ],
        "interpretation": "No point rows are discarded from source or changed. The retained layer is cross-checked against official pair data; the autapses and R7 rows stay as separate exceptions requiring scientific review.",
    }
    (HERE / "princeton_point_exclusion_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(audit["counts"], indent=2))


if __name__ == "__main__":
    main()
