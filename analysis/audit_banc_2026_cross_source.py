"""Triangulate 34 BANC-matched FAFB IDs with same-animal released evidence."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/research_sources/other/banc_2026"
OTHER = ROOT / "analysis/reconstruction_candidates_v783"


def rows(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def write(path: Path, content: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(content[0]))
        writer.writeheader()
        writer.writerows(content)


def main() -> None:
    banc = rows(DATA / "banc_34_fafb_id_summary.csv")
    ids = {row["fafb_v783_root_id"] for row in banc}
    princeton = {
        row["root_id"]: row for row in rows(OTHER / "princeton_root_coverage_616.csv")
        if row["root_id"] in ids
    }
    raw_points = Counter()
    raw_points_with_unproofread_partner = Counter()
    raw_points_with_proofread_partner = Counter()
    for row in rows(ROOT / "data/research_sources/derived/points_for_616_ids_without_proofread_edges.csv"):
        for fid in {row["pre_root_id"], row["post_root_id"]} & ids:
            raw_points[fid] += 1
            partner_proofread = row["post_root_proofread"] if row["pre_root_id"] == fid else row["pre_root_proofread"]
            if partner_proofread.lower() == "true":
                raw_points_with_proofread_partner[fid] += 1
            else:
                raw_points_with_unproofread_partner[fid] += 1
    type_hypotheses = defaultdict(list)
    for row in rows(ROOT / "data/research_sources/derived/missing_neuron_type_link_hypotheses.csv"):
        if row["root_id"] in ids and row["status"] == "type_level_hypothesis_only":
            type_hypotheses[row["root_id"]].append(row)

    official_types = {
        row["root_id"]: row["cell_type"]
        for row in rows(ROOT / "data/flywire_annotations_v2.1.0/Supplemental_file1_neuron_annotations.tsv", "\t")
    }
    princeton_partner_types = defaultdict(lambda: {"rows": 0, "synapses": 0, "partner_ids": set()})
    for row in rows(OTHER / "princeton_filtered_ge5_pair_for_616.csv"):
        fid = row["selected_root_id"]
        if fid not in ids:
            continue
        direction = "out" if row["pre_root_id"] == fid else "in"
        partner_id = row["partner_root_id"]
        partner_type = official_types.get(partner_id, "")
        if not partner_type:
            continue
        item = princeton_partner_types[(fid, direction, partner_type)]
        item["rows"] += 1
        item["synapses"] += int(row["synapse_count"])
        item["partner_ids"].add(partner_id)

    per_id = []
    for row in banc:
        fid = row["fafb_v783_root_id"]
        p = princeton[fid]
        top_internal = sorted(
            type_hypotheses[fid],
            key=lambda h: float(h["homolog_support_fraction"] or 0),
            reverse=True,
        )
        per_id.append({
            "fafb_v783_root_id": fid,
            "fafb_cell_type": row["fafb_official_cell_type"],
            "fafb_side": row["fafb_side"],
            "banc_v888_reviewed_resolved_homologs": row["unique_resolved_banc_v888_homologs"],
            "banc_priority_1_type_patterns": row["comparison_priority_1_hypotheses"],
            "banc_pairs_stable_across_v2_v3": row["same_banc_pairs_in_both_versions"],
            "princeton_filtered_directed_pairs_same_fafb_sample": p["Princeton_filtered_directed_pairs"],
            "princeton_filtered_synapse_count": p["Princeton_filtered_synapse_count"],
            "princeton_unfiltered_directed_pairs_same_fafb_sample": p["Princeton_unfiltered_directed_pairs"],
            "buhmann_raw_a_proofread_pair_exception_points": p["Buhmann_raw_A_points"],
            "buhmann_released_synapse_calls_any_partner": raw_points[fid],
            "buhmann_released_calls_with_unproofread_partner": raw_points_with_unproofread_partner[fid],
            "buhmann_released_calls_with_proofread_partner": raw_points_with_proofread_partner[fid],
            "internal_fafb_type_hypothesis_rows": len(top_internal),
            "top_internal_fafb_candidate_types": ";".join(h["candidate_target_type"] for h in top_internal[:5]),
            "research_priority": (
                1 if int(p["Princeton_filtered_directed_pairs"]) > 0 and int(row["comparison_priority_1_hypotheses"]) > 0
                else 2 if int(p["Princeton_filtered_directed_pairs"]) > 0
                else 3 if int(row["comparison_priority_1_hypotheses"]) > 0
                else 4
            ),
            "evidence": "source_comparison_only_no_new_observed_fafb_connection",
        })
    per_id.sort(key=lambda row: (row["research_priority"], -int(row["princeton_filtered_synapse_count"]), -int(row["banc_priority_1_type_patterns"]), row["fafb_v783_root_id"]))
    summary_path = DATA / "banc_34_fafb_cross_source_summary.csv"
    write(summary_path, per_id)

    priority1 = []
    for row in rows(DATA / "banc_partner_type_hypotheses_for_34_fafb_ids.csv"):
        if row["comparison_priority"] != "1":
            continue
        fid = row["fafb_v783_root_id"]
        key = (fid, row["direction_from_homolog"], row["banc_partner_cell_type_or_class"])
        p = princeton_partner_types.get(key, {"rows": 0, "synapses": 0, "partner_ids": set()})
        internal = next((h for h in type_hypotheses[fid] if h["candidate_target_type"] == key[2]), None)
        priority1.append({
            "fafb_v783_root_id": fid,
            "direction_from_banc_homolog": key[1],
            "banc_partner_type": key[2],
            "banc_shared_pairs_with_count_ge5_each_version": row["banc_pairs_with_at_least_5_synapses_in_both_versions"],
            "banc_supporting_homologs": row["supporting_banc_homolog_ids"],
            "same_fafb_princeton_filtered_partner_type_label_rows": p["rows"],
            "same_fafb_princeton_filtered_partner_type_label_synapses": p["synapses"],
            "same_fafb_princeton_filtered_partner_ids": ";".join(sorted(p["partner_ids"])),
            "internal_fafb_homolog_type_label_agreement": bool(internal),
            "internal_fafb_homolog_support_fraction": internal["homolog_support_fraction"] if internal else "",
            "evidence": "BANC_cross_animal_type_pattern_with_separate_same_fafb_detector_comparison_no_exact_fafb_edge_claim",
        })
    priority1.sort(key=lambda row: (-int(row["same_fafb_princeton_filtered_partner_type_label_rows"]), -int(row["banc_shared_pairs_with_count_ge5_each_version"]), row["fafb_v783_root_id"]))
    priority_path = DATA / "banc_priority1_cross_source_79_type_patterns.csv"
    write(priority_path, priority1)

    audit = {
        "banc_reviewed_matched_fafb_ids": len(ids),
        "ids_with_princeton_filtered_same_fafb_candidate_pair": sum(int(row["princeton_filtered_directed_pairs_same_fafb_sample"]) > 0 for row in per_id),
        "ids_with_princeton_unfiltered_same_fafb_candidate_pair": sum(int(row["princeton_unfiltered_directed_pairs_same_fafb_sample"]) > 0 for row in per_id),
        "ids_with_buhmann_released_raw_call_any_partner": sum(int(row["buhmann_released_synapse_calls_any_partner"]) > 0 for row in per_id),
        "ids_with_buhmann_raw_a_two_proofread_partner_exception": sum(int(row["buhmann_raw_a_proofread_pair_exception_points"]) > 0 for row in per_id),
        "ids_with_buhmann_raw_call_to_unproofread_partner": sum(int(row["buhmann_released_calls_with_unproofread_partner"]) > 0 for row in per_id),
        "ids_with_valid_internal_fafb_type_hypothesis": sum(int(row["internal_fafb_type_hypothesis_rows"]) > 0 for row in per_id),
        "ids_with_both_princeton_filtered_and_internal_type_hypothesis": sum(int(row["princeton_filtered_directed_pairs_same_fafb_sample"]) > 0 and int(row["internal_fafb_type_hypothesis_rows"]) > 0 for row in per_id),
        "banc_priority_1_type_patterns": len(priority1),
        "priority_1_patterns_with_same_fafb_princeton_exact_partner_type_label": sum(int(row["same_fafb_princeton_filtered_partner_type_label_rows"]) > 0 for row in priority1),
        "priority_1_patterns_with_internal_fafb_homolog_type_label_agreement": sum(row["internal_fafb_homolog_type_label_agreement"] for row in priority1),
        "per_id_summary_csv": summary_path.name,
        "priority_1_pattern_csv": priority_path.name,
        "interpretation": "Princeton is an alternative automated detector on the FAFB specimen; BANC is a separate specimen. The Princeton coverage column Buhmann_raw_A_points counts only the 21 raw two-proofread exception keys, whereas points_for_616_ids_without_proofread_edges.csv includes published raw calls to unproofread segments. These and internal FAFB homolog patterns and BANC v2/v3 patterns are not additive measurements. Type-label overlap is only a search/prioritization clue. No new exact FAFB edge is asserted.",
    }
    (DATA / "cross_source_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
