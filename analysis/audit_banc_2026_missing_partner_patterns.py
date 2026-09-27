"""Compare observed BANC partner patterns for reviewed homologs of 34 FAFB IDs.

This never creates or inserts a FAFB edge. It produces cross-animal, type-level
hypotheses from two versions of the *same* BANC specimen's edgelist.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as feather
import pyarrow.ipc as ipc


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/research_sources/other/banc_2026"
MISSING = ROOT / "data/research_sources/derived/model_missing_fafb_ids.csv"
FAFB = ROOT / "data/flywire_annotations_v2.1.0/Supplemental_file1_neuron_annotations.tsv"
VERSIONS = {
    "v2_paper_size_ge_5": "banc_888_edgelist_simple_v2.feather",
    "v3_updated_size_ge_10": "banc_888_edgelist_simple_v3.feather",
}
EVIDENCE = "cross_animal_comparative_homology_only_not_observed_fafb_edge"


def clean(value: object) -> str:
    s = "" if value is None else str(value).strip()
    return "" if s.lower() in {"", "na", "nan", "none", "null", "<na>"} else s


def read_csv(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def unique_join(values: set[str] | list[str], limit: int | None = None) -> str:
    ordered = sorted({v for v in values if v})
    if limit is not None and len(ordered) > limit:
        return ";".join(ordered[:limit]) + f";...({len(ordered)} total)"
    return ";".join(ordered)


def main() -> None:
    edgelist_audit = json.loads((DATA / "edgelist_audit.json").read_text(encoding="utf-8"))
    for filename in VERSIONS.values():
        if edgelist_audit["edgelists"].get(filename, {}).get("status") != "verified":
            raise RuntimeError(f"MD5-verified edgelist audit required first: {filename}")

    missing_ids = {int(row["root_id"]) for row in read_csv(MISSING)}
    fafb = {int(row["root_id"]): row for row in read_csv(FAFB, delimiter="\t")}
    columns = [
        "banc_888_id", "root_626", "root_850", "root_888", "supervoxel_id",
        "cell_type", "cell_sub_class", "cell_class", "super_class",
        "fafb_cell_type", "fafb_alignment_cell_type",
        "side", "region", "body_part_sensory", "body_part_effector",
        "peripheral_target_type", "fafb_match",
    ]
    table = feather.read_table(DATA / "banc_888_meta.feather", columns=columns)
    values = table.to_pydict()
    meta = {
        int(values["banc_888_id"][i]): {key: clean(values[key][i]) for key in columns[1:]}
        for i in range(table.num_rows)
    }
    old_to_current: dict[str, set[int]] = defaultdict(set)
    supervoxel_to_current: dict[str, set[int]] = defaultdict(set)
    for current_id, row in meta.items():
        for key in ("root_626", "root_850", "root_888"):
            if row[key].isdigit():
                old_to_current[row[key]].add(current_id)
        if row["supervoxel_id"].isdigit():
            supervoxel_to_current[row["supervoxel_id"]].add(current_id)

    reviewed = read_csv(DATA / "banc_fafb_reviewed_matches.csv.gz")
    matches: dict[int, dict[int, str]] = defaultdict(dict)
    banc_to_fafb: dict[int, set[int]] = defaultdict(set)
    malformed_valid_match_rows = 0
    original_valid_rows_for_missing = 0
    resolution_rows: list[dict[str, str]] = []
    for row in reviewed:
        if row["valid"] != "t":
            continue
        if not row["match_id"].isdigit() or not row["query_id"].isdigit():
            malformed_valid_match_rows += 1
            continue
        fid = int(row["match_id"])
        if fid not in missing_ids:
            continue
        original_valid_rows_for_missing += 1
        source_candidates = [
            ("pt_supervoxel_in_v888_meta", supervoxel_to_current.get(row["pt_supervoxel_id"], set())),
            ("pt_root_direct_v888", {int(row["pt_root_id"])} if row["pt_root_id"].isdigit() and int(row["pt_root_id"]) in meta else set()),
            ("query_direct_v888", {int(row["query_id"])} if int(row["query_id"]) in meta else set()),
            ("pt_root_version_crosswalk", old_to_current.get(row["pt_root_id"], set())),
            ("query_version_crosswalk", old_to_current.get(row["query_id"], set())),
        ]
        candidates = [(method, candidate) for method, candidate in source_candidates if len(candidate) == 1]
        method, bid_set = candidates[0] if candidates else ("unresolved", set())
        bid = next(iter(bid_set)) if bid_set else None
        anchored = source_candidates[0][1]
        direct = source_candidates[1][1]
        if anchored and direct and anchored != direct:
            raise AssertionError(f"Conflicting supervoxel vs current root in reviewed match: {row}")
        resolution_rows.append({
            "fafb_v783_root_id": str(fid),
            "reviewed_pt_root_id": row["pt_root_id"],
            "reviewed_query_id": row["query_id"],
            "reviewed_pt_supervoxel_id": row["pt_supervoxel_id"],
            "resolved_banc_v888_root_id": "" if bid is None else str(bid),
            "resolution_method": method,
            "reviewed_match_cell_type": clean(row["match_cell_type"]),
            "evidence": EVIDENCE,
        })
        if bid is None:
            continue
        matches[fid][bid] = clean(row["match_cell_type"])
        banc_to_fafb[bid].add(fid)
    resolution_path = DATA / "banc_reviewed_matches_resolved_to_v888_for_34_fafb_ids.csv"
    with resolution_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(resolution_rows[0]))
        writer.writeheader()
        writer.writerows(resolution_rows)
    target_ids = pa.array([str(x) for x in sorted(banc_to_fafb)], type=pa.string())
    absent_targets = sorted(x for x in banc_to_fafb if x not in meta)
    if absent_targets:
        raise AssertionError(f"Reviewed BANC roots absent from v888 meta: {absent_targets[:10]}")

    functions_by_type: dict[str, set[str]] = defaultdict(set)
    dois_by_type: dict[str, set[str]] = defaultdict(set)
    for row in read_csv(DATA / "supplemental_data_9.txt"):
        cell_type = clean(row["cell_type"])
        if cell_type:
            functions_by_type[cell_type].add(clean(row["cell_function"]))
            dois_by_type[cell_type].add(clean(row["doi"]))

    records: list[dict[str, object]] = []
    per_version_selected_edges: dict[str, int] = {}
    per_version_autapses_excluded: dict[str, int] = {}
    for version, filename in VERSIONS.items():
        count_selected = 0
        autapses_excluded = 0
        with pa.memory_map(str(DATA / filename), "r") as mapped:
            reader = ipc.open_file(mapped)
            for batch_index in range(reader.num_record_batches):
                batch = reader.get_batch(batch_index)
                pre = batch.column("pre").to_numpy(zero_copy_only=False)
                post = batch.column("post").to_numpy(zero_copy_only=False)
                count = batch.column("count").to_numpy(zero_copy_only=False)
                selected = np.flatnonzero(
                    pc.or_(
                        pc.is_in(batch.column("pre"), value_set=target_ids),
                        pc.is_in(batch.column("post"), value_set=target_ids),
                    ).to_numpy(zero_copy_only=False)
                )
                count_selected += len(selected)
                for i in selected:
                    a, b, n = int(pre[i]), int(post[i]), int(count[i])
                    if a == b:
                        autapses_excluded += 1
                        continue
                    for target, partner, direction in ((a, b, "out"), (b, a, "in")):
                        if target not in banc_to_fafb:
                            continue
                        target_meta = meta[target]
                        partner_meta = meta[partner]
                        partner_type = (
                            partner_meta["cell_type"] or partner_meta["cell_sub_class"]
                            or partner_meta["cell_class"] or partner_meta["super_class"] or "unknown"
                        )
                        for fid in banc_to_fafb[target]:
                            fafb_meta = fafb[fid]
                            official_type = clean(fafb_meta.get("cell_type"))
                            reviewed_type = clean(matches[fid][target])
                            comparison_type = official_type or reviewed_type
                            target_type = target_meta["fafb_cell_type"] or target_meta["cell_type"]
                            fafb_side = clean(fafb_meta.get("side"))
                            banc_side = target_meta["side"]
                            type_status = (
                                "same" if comparison_type and target_type and comparison_type == target_type
                                else "different" if comparison_type and target_type
                                else "unknown"
                            )
                            side_status = (
                                "same" if fafb_side and banc_side and fafb_side == banc_side
                                else "different" if fafb_side and banc_side
                                else "unknown"
                            )
                            records.append({
                                "fafb_v783_root_id": str(fid),
                                "fafb_official_cell_type": official_type,
                                "fafb_side": fafb_side,
                                "reviewed_match_cell_type": reviewed_type,
                                "banc_v888_homolog_id": str(target),
                                "banc_homolog_cell_type": target_type,
                                "banc_homolog_native_cell_type": target_meta["cell_type"],
                                "banc_homolog_fafb_cell_type": target_meta["fafb_cell_type"],
                                "banc_homolog_side": banc_side,
                                "homolog_type_status": type_status,
                                "homolog_side_status": side_status,
                                "direction_from_homolog": direction,
                                "banc_v888_partner_id": str(partner),
                                "banc_partner_cell_type_or_class": partner_type,
                                "banc_partner_super_class": partner_meta["super_class"],
                                "banc_partner_side": partner_meta["side"],
                                "banc_partner_region": partner_meta["region"],
                                "banc_partner_body_part_sensory": partner_meta["body_part_sensory"],
                                "banc_partner_body_part_effector": partner_meta["body_part_effector"],
                                "banc_partner_peripheral_target_type": partner_meta["peripheral_target_type"],
                                "banc_partner_fafb_match_id_cross_animal": partner_meta["fafb_match"],
                                "banc_synapse_count": n,
                                "banc_edgelist_version": version,
                                "evidence": EVIDENCE,
                            })
        per_version_selected_edges[version] = count_selected - autapses_excluded
        per_version_autapses_excluded[version] = autapses_excluded
        print(f"{version}: {count_selected - autapses_excluded:,} non-autapse BANC edges incident to reviewed homologs", flush=True)

    detail_path = DATA / "banc_observed_partner_edges_for_34_fafb_ids.csv"
    with detail_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    groups: dict[tuple[str, str, str], dict[str, object]] = {}
    for record in records:
        key = (
            str(record["fafb_v783_root_id"]),
            str(record["direction_from_homolog"]),
            str(record["banc_partner_cell_type_or_class"]),
        )
        if key not in groups:
            groups[key] = {
                "versions": defaultdict(lambda: {"pairs": set(), "pair_counts": {}, "homologs": set(), "partners": set(), "synapses": 0}),
                "homolog_type_status": set(),
                "homolog_side_status": set(),
                "partner_super_classes": set(),
                "partner_sides": set(),
                "partner_body_part_sensory": set(),
                "partner_body_part_effector": set(),
                "partner_peripheral_target_types": set(),
                "partner_fafb_matches": set(),
            }
        group = groups[key]
        version = str(record["banc_edgelist_version"])
        version_group = group["versions"][version]
        pair = (str(record["banc_v888_homolog_id"]), str(record["banc_v888_partner_id"]))
        version_group["pairs"].add(pair)
        version_group["pair_counts"][pair] = int(record["banc_synapse_count"])
        version_group["homologs"].add(str(record["banc_v888_homolog_id"]))
        version_group["partners"].add(str(record["banc_v888_partner_id"]))
        version_group["synapses"] += int(record["banc_synapse_count"])
        for field, dest in (
            ("homolog_type_status", "homolog_type_status"),
            ("homolog_side_status", "homolog_side_status"),
            ("banc_partner_super_class", "partner_super_classes"),
            ("banc_partner_side", "partner_sides"),
            ("banc_partner_body_part_sensory", "partner_body_part_sensory"),
            ("banc_partner_body_part_effector", "partner_body_part_effector"),
            ("banc_partner_peripheral_target_type", "partner_peripheral_target_types"),
            ("banc_partner_fafb_match_id_cross_animal", "partner_fafb_matches"),
        ):
            value = clean(record[field])
            if value:
                group[dest].add(value)

    hypotheses: list[dict[str, object]] = []
    for (fid, direction, partner_type), group in groups.items():
        v2 = group["versions"].get("v2_paper_size_ge_5", {})
        v3 = group["versions"].get("v3_updated_size_ge_10", {})
        pairs2 = v2.get("pairs", set())
        pairs3 = v3.get("pairs", set())
        shared = pairs2 & pairs3
        shared_strong = {
            pair for pair in shared
            if v2.get("pair_counts", {}).get(pair, 0) >= 5
            and v3.get("pair_counts", {}).get(pair, 0) >= 5
        }
        union = pairs2 | pairs3
        type_status = group["homolog_type_status"]
        side_status = group["homolog_side_status"]
        official_type_known = bool(clean(fafb[int(fid)].get("cell_type")))
        no_contradiction = (
            "different" not in side_status
            and (not official_type_known or "different" not in type_status)
        )
        homolog_support = len(v2.get("homologs", set()) | v3.get("homologs", set()))
        if shared_strong and homolog_support >= 2 and no_contradiction:
            priority = 1
        elif shared_strong and no_contradiction:
            priority = 2
        else:
            priority = 3
        hypotheses.append({
            "fafb_v783_root_id": fid,
            "fafb_official_cell_type": clean(fafb[int(fid)].get("cell_type")),
            "fafb_side": clean(fafb[int(fid)].get("side")),
            "direction_from_homolog": direction,
            "banc_partner_cell_type_or_class": partner_type,
            "banc_partner_super_classes": unique_join(group["partner_super_classes"]),
            "banc_partner_sides": unique_join(group["partner_sides"]),
            "banc_partner_body_part_sensory": unique_join(group["partner_body_part_sensory"]),
            "banc_partner_body_part_effector": unique_join(group["partner_body_part_effector"]),
            "banc_partner_peripheral_target_types": unique_join(group["partner_peripheral_target_types"]),
            "reviewed_banc_homologs_for_fafb_id": len(matches[int(fid)]),
            "supporting_banc_homolog_ids": unique_join(v2.get("homologs", set()) | v3.get("homologs", set())),
            "homolog_type_statuses": unique_join(type_status),
            "homolog_side_statuses": unique_join(side_status),
            "v2_banc_homologs": len(v2.get("homologs", set())),
            "v2_banc_partner_ids": len(v2.get("partners", set())),
            "v2_observed_banc_pair_rows": len(pairs2),
            "v2_banc_synapse_count": v2.get("synapses", 0),
            "v3_banc_homologs": len(v3.get("homologs", set())),
            "v3_banc_partner_ids": len(v3.get("partners", set())),
            "v3_observed_banc_pair_rows": len(pairs3),
            "v3_banc_synapse_count": v3.get("synapses", 0),
            "banc_pairs_in_both_versions": len(shared),
            "banc_pairs_with_at_least_5_synapses_in_both_versions": len(shared_strong),
            "banc_pair_jaccard_v2_v3": round(len(shared) / len(union), 6) if union else 0,
            "banc_partner_fafb_match_ids_cross_animal": unique_join(group["partner_fafb_matches"], limit=20),
            "literature_partner_functions": unique_join(functions_by_type.get(partner_type, set())),
            "literature_partner_dois": unique_join(dois_by_type.get(partner_type, set())),
            "comparison_priority": priority,
            "priority_rule": "1=shared_BANC_pair_count_ge_5_each_version_multiple_homologs_no_side_or_known_official_type_label_conflict;2=same_shared_pair_rule_one_homolog;3=other",
            "evidence": EVIDENCE,
        })
    hypotheses.sort(key=lambda row: (
        int(row["fafb_v783_root_id"]),
        int(row["comparison_priority"]),
        -int(row["banc_pairs_with_at_least_5_synapses_in_both_versions"]),
        -int(row["banc_pairs_in_both_versions"]),
        -min(int(row["v2_banc_synapse_count"]), int(row["v3_banc_synapse_count"])),
        str(row["direction_from_homolog"]),
        str(row["banc_partner_cell_type_or_class"]),
    ))
    candidate_path = DATA / "banc_partner_type_hypotheses_for_34_fafb_ids.csv"
    with candidate_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(hypotheses[0]))
        writer.writeheader()
        writer.writerows(hypotheses)

    by_fafb_hypotheses: dict[int, list[dict[str, object]]] = defaultdict(list)
    for row in hypotheses:
        by_fafb_hypotheses[int(row["fafb_v783_root_id"])].append(row)
    by_fafb_records: dict[int, dict[str, set[tuple[str, str, str]]]] = defaultdict(lambda: defaultdict(set))
    for row in records:
        fid = int(str(row["fafb_v783_root_id"]))
        pair = (
            str(row["direction_from_homolog"]),
            str(row["banc_v888_homolog_id"]),
            str(row["banc_v888_partner_id"]),
        )
        by_fafb_records[fid][str(row["banc_edgelist_version"])].add(pair)
    id_summaries: list[dict[str, object]] = []
    for fid in sorted(matches):
        same_type = different_type = unknown_type = 0
        same_side = different_side = unknown_side = 0
        homolog_types: set[str] = set()
        for bid, reviewed_type in matches[fid].items():
            official_type = clean(fafb[fid].get("cell_type"))
            reference_type = official_type or reviewed_type
            banc_type = meta[bid]["fafb_cell_type"] or meta[bid]["cell_type"]
            homolog_types.add(banc_type)
            if reference_type and banc_type:
                if reference_type == banc_type:
                    same_type += 1
                else:
                    different_type += 1
            else:
                unknown_type += 1
            fafb_side = clean(fafb[fid].get("side"))
            banc_side = meta[bid]["side"]
            if fafb_side and banc_side:
                if fafb_side == banc_side:
                    same_side += 1
                else:
                    different_side += 1
            else:
                unknown_side += 1
        v2_pairs = by_fafb_records[fid].get("v2_paper_size_ge_5", set())
        v3_pairs = by_fafb_records[fid].get("v3_updated_size_ge_10", set())
        top = by_fafb_hypotheses[fid][:6]
        id_summaries.append({
            "fafb_v783_root_id": str(fid),
            "fafb_official_cell_type": clean(fafb[fid].get("cell_type")),
            "fafb_side": clean(fafb[fid].get("side")),
            "reviewed_valid_source_rows": sum(int(r["fafb_v783_root_id"]) == fid for r in resolution_rows),
            "reviewed_source_rows_unresolved_v888": sum(int(r["fafb_v783_root_id"]) == fid and not r["resolved_banc_v888_root_id"] for r in resolution_rows),
            "unique_resolved_banc_v888_homologs": len(matches[fid]),
            "resolved_banc_v888_homolog_ids": unique_join({str(x) for x in matches[fid]}),
            "banc_homolog_cell_types": unique_join(homolog_types),
            "homolog_type_same": same_type,
            "homolog_type_different": different_type,
            "homolog_type_unknown": unknown_type,
            "homolog_side_same": same_side,
            "homolog_side_different": different_side,
            "homolog_side_unknown": unknown_side,
            "v2_non_autapse_incident_banc_pairs": len(v2_pairs),
            "v3_non_autapse_incident_banc_pairs": len(v3_pairs),
            "same_banc_pairs_in_both_versions": len(v2_pairs & v3_pairs),
            "partner_type_hypotheses": len(by_fafb_hypotheses[fid]),
            "comparison_priority_1_hypotheses": sum(r["comparison_priority"] == 1 for r in by_fafb_hypotheses[fid]),
            "top_comparative_partner_types": unique_join([f'{r["direction_from_homolog"]}:{r["banc_partner_cell_type_or_class"]}' for r in top]),
            "evidence": EVIDENCE,
        })
    id_summary_path = DATA / "banc_34_fafb_id_summary.csv"
    with id_summary_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(id_summaries[0]))
        writer.writeheader()
        writer.writerows(id_summaries)

    summary = {
        "dataset": "BANC v888, Harvard Dataverse doi:10.7910/DVN/7WTH1N",
        "release_comparison": {"v2": "paper synapse detector size >=5", "v3": "updated synapse detector size >=10"},
        "fafb_unconnected_ids_total": len(missing_ids),
        "fafb_ids_with_valid_reviewed_cross_animal_match": len(matches),
        "reviewed_valid_source_rows_for_those_ids": original_valid_rows_for_missing,
        "reviewed_source_rows_resolved_to_v888": sum(bool(r["resolved_banc_v888_root_id"]) for r in resolution_rows),
        "reviewed_source_rows_unresolved_at_v888": sum(not r["resolved_banc_v888_root_id"] for r in resolution_rows),
        "unique_resolved_fafb_banc_homolog_pairs": sum(len(x) for x in matches.values()),
        "reviewed_valid_rows_skipped_for_non_numeric_ids": malformed_valid_match_rows,
        "unique_banc_homolog_ids": len(banc_to_fafb),
        "selected_banc_edgelist_rows_incident_to_homologs": per_version_selected_edges,
        "autapse_rows_excluded_for_these_homologs": per_version_autapses_excluded,
        "detail_rows_with_fafb_match_duplication": len(records),
        "partner_type_hypothesis_rows": len(hypotheses),
        "hypotheses_with_shared_banc_pair_count_ge_5_in_both_versions": sum(int(row["banc_pairs_with_at_least_5_synapses_in_both_versions"]) > 0 for row in hypotheses),
        "priority_1_rows": sum(row["comparison_priority"] == 1 for row in hypotheses),
        "priority_2_rows": sum(row["comparison_priority"] == 2 for row in hypotheses),
        "priority_3_rows": sum(row["comparison_priority"] == 3 for row in hypotheses),
        "detail_csv": detail_path.name,
        "hypotheses_csv": candidate_path.name,
        "per_fafb_id_summary_csv": id_summary_path.name,
        "v888_resolution_csv": resolution_path.name,
        "type_status_definition": "Literal equality of FAFB official cell_type (or reviewed-match label if official is blank) and BANC fafb_cell_type when present, otherwise BANC cell_type. A 'different' label is not proof of biological mismatch because nomenclature changes across datasets.",
        "side_status_definition": "Literal left/right/center agreement between the official FAFB annotation and BANC meta; cross-animal mirror matches can be biologically valid.",
        "interpretation": "Every edge in the detail CSV is observed in the BANC specimen only. FAFB IDs are reviewed cross-animal homolog matches. Version agreement is algorithmic robustness in one specimen, not independent biological replication. Candidate priority is heuristic, never a probability or an FAFB connection claim.",
    }
    (DATA / "partner_pattern_audit.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
