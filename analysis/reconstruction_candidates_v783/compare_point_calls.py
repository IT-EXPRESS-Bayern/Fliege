"""Compare Buhmann-v783 and Princeton-2025 individual point calls for 616 roots.

Exact root-ID / direction / neuropil agreement is retained without adding the
two detector counts. Exact six-coordinate overlap is reported separately; a
non-match is not proof that an anatomical synapse differs or is absent.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OLD = ROOT / "data/research_sources/derived/points_for_616_ids_without_proofread_edges.csv"
NEW = HERE / "princeton_individual_points_for_616.csv"
NEW_AUDIT = HERE / "princeton_point_audit.json"
MISSING = ROOT / "data/research_sources/derived/model_missing_fafb_ids.csv"
FIELDS = (
    "review_rank", "evidence_class", "pre_root_id", "post_root_id", "neuropil",
    "selected_root_ids", "partner_proofreading_class", "Buhmann_2024_point_calls",
    "Princeton_2025_point_calls", "exact_six_coordinate_matches",
    "both_detectors_same_pair_region", "interpretation",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def coords(row: dict[str, str], old: bool) -> tuple[str, ...]:
    if old:
        return tuple(row[f"{side}_{axis}_nm"] for side in ("pre", "post") for axis in ("x", "y", "z"))
    return tuple(row[f"{side}_{axis}"] for side in ("pre", "post") for axis in ("x", "y", "z"))


def main() -> None:
    if not NEW_AUDIT.is_file():
        raise FileNotFoundError("Verified Princeton point scan must run first")
    new_audit = json.loads(NEW_AUDIT.read_text(encoding="utf-8"))
    if sha256(NEW) != new_audit["outputs"]["points"]["sha256"]:
        raise ValueError("Princeton selected point output changed since scan")
    missing = {r["root_id"] for r in rows(MISSING)}
    if len(missing) != 616:
        raise ValueError("Expected 616 missing IDs")

    counts = {"old": Counter(), "new": Counter()}
    sites = {"old": defaultdict(Counter), "new": defaultdict(Counter)}
    root_ids = defaultdict(set)
    partner_class = {}
    for row in rows(OLD):
        key = row["pre_root_id"], row["post_root_id"], row["neuropil"]
        counts["old"][key] += 1
        sites["old"][key][coords(row, True)] += 1
        root_ids[key].update({row["pre_root_id"], row["post_root_id"]} & missing)
        klass = ("both_officially_proofread" if row["pre_root_proofread"] == row["post_root_proofread"] == "True"
                 else "one_unproofread_segment")
        if key in partner_class and partner_class[key] != klass:
            raise ValueError("Old point group has inconsistent proofreading class")
        partner_class[key] = klass
    for row in rows(NEW):
        key = row["pre_root_id"], row["post_root_id"], row["neuropil"]
        counts["new"][key] += 1
        sites["new"][key][coords(row, False)] += 1
        root_ids[key].update(row["selected_root_ids"].split(";"))
        klass = ("both_officially_proofread" if row["partner_proofreading_class"] == "both_officially_proofread"
                 else "one_unproofread_segment")
        if key in partner_class and partner_class[key] != klass:
            raise ValueError("Detector sources disagree about official proofread membership")
        partner_class[key] = klass

    output = []
    for key in counts["old"].keys() | counts["new"].keys():
        old_n, new_n = counts["old"][key], counts["new"][key]
        exact_sites = sum(min(n, sites["new"][key].get(site, 0)) for site, n in sites["old"][key].items())
        klass = partner_class[key]
        if klass == "both_officially_proofread":
            evidence = ("A_raw_P_dual_proofread_pair" if old_n and new_n else
                        "A_raw_Buhmann_only_proofread_pair" if old_n else
                        "P_Princeton_only_proofread_pair")
        else:
            evidence = ("B_dual_detector_segment" if old_n and new_n else
                        "B_Buhmann_only_segment" if old_n else "B_Princeton_only_segment")
        output.append({
            "evidence_class": evidence,
            "pre_root_id": key[0], "post_root_id": key[1], "neuropil": key[2],
            "selected_root_ids": ";".join(sorted(root_ids[key])),
            "partner_proofreading_class": klass,
            "Buhmann_2024_point_calls": old_n,
            "Princeton_2025_point_calls": new_n,
            "exact_six_coordinate_matches": exact_sites,
            "both_detectors_same_pair_region": "yes" if old_n and new_n else "no",
            "interpretation": "Two automated detector counts shown separately; segment IDs are not identified whole neurons",
        })
    rank_order = {"A_raw_P_dual_proofread_pair": 0,
                  "A_raw_Buhmann_only_proofread_pair": 1,
                  "P_Princeton_only_proofread_pair": 2,
                  "B_dual_detector_segment": 3, "B_Buhmann_only_segment": 4,
                  "B_Princeton_only_segment": 5}
    output.sort(key=lambda r: (
        rank_order[r["evidence_class"]],
        -min(int(r["Buhmann_2024_point_calls"]), int(r["Princeton_2025_point_calls"])),
        -max(int(r["Buhmann_2024_point_calls"]), int(r["Princeton_2025_point_calls"])),
        r["pre_root_id"], r["post_root_id"], r["neuropil"],
    ))
    for rank, row in enumerate(output, 1):
        row["review_rank"] = rank
    with (HERE / "dual_detector_pair_region_review.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(output)
    dual = [r for r in output if r["evidence_class"] == "B_dual_detector_segment"]
    with (HERE / "dual_detector_segment_candidates.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(dual)
    audit = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha256": {
            str(OLD.relative_to(ROOT)).replace("\\", "/"): sha256(OLD),
            str(NEW.relative_to(ROOT)).replace("\\", "/"): sha256(NEW),
        },
        "counts": {
            "Buhmann_points": sum(counts["old"].values()),
            "Princeton_points": sum(counts["new"].values()),
            "Buhmann_pair_region_keys": len(counts["old"]),
            "Princeton_pair_region_keys": len(counts["new"]),
            "pair_region_union": len(output),
            "pair_region_intersection": sum(r["both_detectors_same_pair_region"] == "yes" for r in output),
            "exact_six_coordinate_matches_on_shared_keys": sum(int(r["exact_six_coordinate_matches"]) for r in output),
            "evidence_class_rows": dict(Counter(r["evidence_class"] for r in output)),
            "dual_detector_segment_rows": len(dual),
            "dual_detector_segment_old_points": sum(int(r["Buhmann_2024_point_calls"]) for r in dual),
            "dual_detector_segment_new_points": sum(int(r["Princeton_2025_point_calls"]) for r in dual),
        },
        "output": {
            name: sha256(HERE / name) for name in (
                "dual_detector_pair_region_review.csv", "dual_detector_segment_candidates.csv")
        },
        "interpretation": "Pair-region overlap from two automated detectors strengthens review priority but is not physiological validation; exact coordinate identity is narrower than anatomical equivalence. Counts cannot be added.",
    }
    (HERE / "dual_detector_point_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(audit["counts"], indent=2))


if __name__ == "__main__":
    main()
