"""Compare the exceptional FAFB-v783 R7 point calls between two detectors.

This compares published numeric coordinates within the same directed pair and
neuropil. Spatial proximity is a review aid, not synapse identity or proof.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
R7 = "720575940623940963"
OLD = ROOT / "data/research_sources/derived/points_for_616_ids_without_proofread_edges.csv"
NEW = ROOT / "analysis/reconstruction_candidates_v783/princeton_individual_points_for_616.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def xyz(row: dict, prefix: str, old: bool) -> tuple[float, float, float]:
    suffix = "_nm" if old else ""
    return tuple(float(row[f"{prefix}_{axis}{suffix}"]) for axis in "xyz")


def distance(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return math.dist(a, b)


def main() -> None:
    with OLD.open(newline="", encoding="utf-8") as handle:
        old = [row for row in csv.DictReader(handle)
               if R7 in (row["pre_root_id"], row["post_root_id"])
               and row["pre_root_proofread"] == "True"
               and row["post_root_proofread"] == "True"]
    with NEW.open(newline="", encoding="utf-8") as handle:
        new_all = [row for row in csv.DictReader(handle)
                   if R7 in (row["pre_root_id"], row["post_root_id"])]
    new = [row for row in new_all if row["pre_root_id"] != row["post_root_id"]]
    assert len(old) == 48
    assert len(new_all) == 215 and len(new) == 213
    assert {row["neuropil"] for row in old} == {"ME_R"}
    old_by_key = defaultdict(list)
    new_by_key = defaultdict(list)
    for row in old:
        old_by_key[(row["pre_root_id"], row["post_root_id"], row["neuropil"])].append(row)
    for row in new:
        new_by_key[(row["pre_root_id"], row["post_root_id"], row["neuropil"])].append(row)
    old_keys = set(old_by_key)
    new_keys = set(new_by_key)

    pair_rows = []
    for key in sorted(old_keys | new_keys):
        old_rows = old_by_key.get(key, [])
        new_rows = new_by_key.get(key, [])
        pair_rows.append({
            "pre_root_id": key[0], "post_root_id": key[1], "neuropil": key[2],
            "old_Buhmann_points": len(old_rows),
            "new_Princeton_points": len(new_rows),
            "in_both_point_exports": "yes" if old_rows and new_rows else "no",
            "interpretation": "Shared directed pair and region is detector agreement at partner level, not point identity",
        })

    nearest_rows = []
    for row in sorted(old, key=lambda item: int(item["synapse_id"])):
        key = row["pre_root_id"], row["post_root_id"], row["neuropil"]
        old_pre, old_post = xyz(row, "pre", True), xyz(row, "post", True)
        ranked = []
        for candidate in new_by_key.get(key, []):
            new_pre, new_post = xyz(candidate, "pre", False), xyz(candidate, "post", False)
            pre_d = distance(old_pre, new_pre)
            post_d = distance(old_post, new_post)
            old_mid = tuple((a + b) / 2 for a, b in zip(old_pre, old_post))
            new_mid = tuple((a + b) / 2 for a, b in zip(new_pre, new_post))
            mid_d = distance(old_mid, new_mid)
            joint_d = math.sqrt((pre_d * pre_d + post_d * post_d) / 2)
            ranked.append((joint_d, pre_d, post_d, mid_d, candidate))
        ranked.sort(key=lambda item: (item[0], int(item[4]["source_row_number"])))
        best = ranked[0] if ranked else None
        nearest_rows.append({
            "old_synapse_id": row["synapse_id"],
            "pre_root_id": key[0], "post_root_id": key[1], "neuropil": key[2],
            "new_same_pair_region_points": len(ranked),
            "nearest_new_source_row": best[4]["source_row_number"] if best else "",
            "pre_distance_nm": f"{best[1]:.3f}" if best else "",
            "post_distance_nm": f"{best[2]:.3f}" if best else "",
            "midpoint_distance_nm": f"{best[3]:.3f}" if best else "",
            "joint_distance_nm": f"{best[0]:.3f}" if best else "",
            "exact_six_coordinate_match": "yes" if best and best[0] == 0 else "no",
            "interpretation": "Nearest call in same directed pair and neuropil; proximity does not prove same synapse",
        })

    def write_rows(name: str, rows: list[dict]) -> None:
        with (HERE / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    write_rows("r7_pair_point_comparison.csv", pair_rows)
    write_rows("r7_old_to_new_nearest_points.csv", nearest_rows)
    matched = [float(row["joint_distance_nm"]) for row in nearest_rows if row["joint_distance_nm"]]
    thresholds = (100, 250, 500, 1_000, 5_000)
    audit = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "r7_root_id": R7,
        "source_sha256": {str(OLD.relative_to(ROOT)).replace("\\", "/"): sha256(OLD),
                          str(NEW.relative_to(ROOT)).replace("\\", "/"): sha256(NEW)},
        "counts": {
            "old_buhmann_two_proofread_points": len(old),
            "old_directed_pair_region_keys": len(old_keys),
            "new_princeton_points_total": len(new_all),
            "new_princeton_autapses": len(new_all) - len(new),
            "new_princeton_non_autaptic_points": len(new),
            "new_directed_pair_region_keys_non_autaptic": len(new_keys),
            "shared_directed_pair_region_keys": len(old_keys & new_keys),
            "old_points_with_same_pair_region_in_new": len(matched),
            "old_points_without_same_pair_region_in_new": len(old) - len(matched),
            "exact_six_coordinate_matches": sum(row["exact_six_coordinate_match"] == "yes" for row in nearest_rows),
            "distinct_nearest_new_calls": len({row["nearest_new_source_row"] for row in nearest_rows if row["nearest_new_source_row"]}),
            "old_points_with_nearest_joint_distance_at_most_nm": {
                str(threshold): sum(d <= threshold for d in matched) for threshold in thresholds
            },
            "old_point_nearest_joint_distance_nm_min": min(matched) if matched else None,
            "old_point_nearest_joint_distance_nm_median": sorted(matched)[len(matched) // 2] if matched else None,
            "old_point_nearest_joint_distance_nm_max": max(matched) if matched else None,
            "new_point_region_counts": dict(Counter(row["neuropil"] for row in new)),
        },
        "method": "Within identical directed pre/post root IDs and neuropil, find each old point's nearest new point by root-mean-square of presynaptic and postsynaptic 3D coordinate distances. Old CSV names coordinates in nm; new FAFB coordinate grid is treated as nm and is compatible with the separately audited skeleton coordinates. No one-to-one matching is imposed, so multiple old points may choose the same new point.",
        "limitations": "Two automated detectors and different export dates; location proximity is not synapse identity, physiological function, or a proofread graph edge. Princeton point release has R7 calls absent from its earlier pair export; why that pair export excluded R7 is not established.",
        "output_sha256": {name: sha256(HERE / name) for name in ("r7_pair_point_comparison.csv", "r7_old_to_new_nearest_points.csv")},
    }
    (HERE / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit["counts"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
