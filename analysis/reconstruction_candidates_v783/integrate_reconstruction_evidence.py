"""Integrate review *indexes* while preserving the separate detector layers."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT_QUEUE = HERE / "root_review_queue.csv"
P_ROOTS = HERE / "princeton_root_coverage_616.csv"
P_EDGES = HERE / "princeton_unfiltered_for_616.csv"
P_FILTERED = HERE / "princeton_filtered_ge5_pair_for_616.csv"
P_POINTS = HERE / "princeton_individual_points_for_616.csv"
EXCLUSIONS = HERE / "princeton_point_exclusion_audit.json"
R7 = "720575940623940963"
PAIR_FIELDS = (
    "review_rank", "evidence_class", "pre_root_id", "post_root_id", "neuropil",
    "selected_root_ids", "Princeton_2025_synapse_count", "Princeton_2025_point_source_rows",
    "Princeton_2025_nt_type_labels", "appears_in_Codex_ge5_pair_export",
    "Buhmann_original_v783_aggregate_edge_exists", "interpretation",
)
ROOT_FIELDS = (
    "review_rank", "review_band", "root_id", "cell_type", "side",
    "Buhmann_v783_A_raw_points", "Buhmann_v783_B_segment_points",
    "Princeton_2025_published_pairs", "Princeton_2025_published_synapses",
    "Princeton_2025_filtered_ge5_pair_rows", "Princeton_2025_total_point_rows",
    "Princeton_2025_autapse_point_rows", "Buhmann_C_type_hypotheses",
    "next_manual_check", "model_use", "interpretation",
)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, fields: tuple[str, ...], data: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data)


def main() -> None:
    exclusions = json.loads(EXCLUSIONS.read_text(encoding="utf-8"))
    if not exclusions["checks"]["retained_point_groups_equal_unfiltered_connection_groups_exactly"]:
        raise ValueError("Princeton point/connection equality not established")
    roots = {r["root_id"]: r for r in rows(ROOT_QUEUE)}
    p_roots = {r["root_id"]: r for r in rows(P_ROOTS)}
    if len(roots) != 616 or len(p_roots) != 616 or set(roots) != set(p_roots):
        raise ValueError("616 root index mismatch")
    filtered_keys = {(r["pre_root_id"], r["post_root_id"], r["neuropil"])
                     for r in rows(P_FILTERED)}
    point_rows_by_root = Counter()
    autapse_rows_by_root = Counter()
    point_support = defaultdict(list)
    for row in rows(P_POINTS):
        touched = row["selected_root_ids"].split(";")
        self_call = row["pre_root_id"] == row["post_root_id"]
        r7_call = R7 in (row["pre_root_id"], row["post_root_id"])
        for root_id in touched:
            point_rows_by_root[root_id] += 1
            autapse_rows_by_root[root_id] += self_call
        if self_call or r7_call:
            continue
        key = (row["pre_root_id"], row["post_root_id"], row["neuropil"] or "UNASGD")
        point_support[key].append(int(row["source_row_number"]))
    p_edges = {}
    selected_ids_by_pair = defaultdict(set)
    for row in rows(P_EDGES):
        key = row["pre_root_id"], row["post_root_id"], row["neuropil"]
        if key in p_edges and int(row["synapse_count"]) != int(p_edges[key]["synapse_count"]):
            raise ValueError("Duplicate selected-root view has inconsistent pair count")
        p_edges[key] = row
        selected_ids_by_pair[key].add(row["selected_root_id"])
    if len(p_edges) != 3233 or set(p_edges) != set(point_support):
        raise ValueError("Princeton exact pair-region key reconciliation changed")
    pair_output = []
    for key, row in p_edges.items():
        point_ids = sorted(point_support[key])
        count = int(row["synapse_count"])
        if len(point_ids) != count:
            raise ValueError("Princeton pair count does not match individual point rows")
        pair_output.append({
            "evidence_class": "P_alternate_automated_detector_same_specimen",
            "pre_root_id": key[0], "post_root_id": key[1], "neuropil": key[2],
            "selected_root_ids": ";".join(sorted(selected_ids_by_pair[key])),
            "Princeton_2025_synapse_count": count,
            "Princeton_2025_point_source_rows": ";".join(map(str, point_ids)),
            "Princeton_2025_nt_type_labels": row["nt_type_labels"],
            "appears_in_Codex_ge5_pair_export": "yes" if key in filtered_keys else "no",
            "Buhmann_original_v783_aggregate_edge_exists": "no",
            "interpretation": "Exact alternative detector pair with point-row provenance; not added to original v783 graph or physiologically validated",
        })
    pair_output.sort(key=lambda r: (-int(r["Princeton_2025_synapse_count"]),
                                    r["pre_root_id"], r["post_root_id"], r["neuropil"]))
    for rank, row in enumerate(pair_output, 1):
        row["review_rank"] = rank
    write_csv(HERE / "princeton_exact_pair_candidates_3233.csv", PAIR_FIELDS, pair_output)

    root_output = []
    for root_id, old in roots.items():
        p = p_roots[root_id]
        filtered_rows = int(p["Princeton_filtered_pair_region_rows"])
        pairs = int(p["Princeton_unfiltered_directed_pairs"])
        if root_id == R7:
            band = "R7_cross_detector_point_exception"
            action = "Inspect two point clouds and omission from both pair exports"
            use = "No edge in either published pair graph; keep as point-only exception"
        elif filtered_rows:
            band = "P_pair_ge5_export"
            action = "Review exact 2025 point sites and map sensory context"
            use = "Optional separately labeled Princeton detector graph layer"
        elif pairs:
            band = "P_pair_1_to_4_only"
            action = "Review single/few-contact 2025 pair sites and false-positive risk"
            use = "Optional separately labeled low-count Princeton layer"
        elif int(old["segment_points"]):
            band = "B_old_segment_only"
            action = "Resolve unproofread partner segment morphology/proofreading"
            use = "Segment graph only; no exact neuron-neuron edge"
        elif point_rows_by_root[root_id] and autapse_rows_by_root[root_id] == point_rows_by_root[root_id]:
            band = "P_autapse_points_only"
            action = "Inspect autapse calls; no distinct-partner edge"
            use = "Exception only"
        else:
            band = "C_or_no_direct_points"
            action = "Seek new detection/proofreading evidence; type hypotheses are search aids"
            use = "No exact edge"
        root_output.append({
            "review_band": band,
            "root_id": root_id,
            "cell_type": old["cell_type"], "side": old["side"],
            "Buhmann_v783_A_raw_points": old["raw_proofread_points"],
            "Buhmann_v783_B_segment_points": old["segment_points"],
            "Princeton_2025_published_pairs": pairs,
            "Princeton_2025_published_synapses": p["Princeton_unfiltered_synapse_count"],
            "Princeton_2025_filtered_ge5_pair_rows": filtered_rows,
            "Princeton_2025_total_point_rows": point_rows_by_root[root_id],
            "Princeton_2025_autapse_point_rows": autapse_rows_by_root[root_id],
            "Buhmann_C_type_hypotheses": old["type_hypothesis_rows"],
            "next_manual_check": action,
            "model_use": use,
            "interpretation": "Review band is a workflow order, not calibrated confidence or functional evidence",
        })
    order = {"R7_cross_detector_point_exception": 0,
             "P_pair_ge5_export": 1, "P_pair_1_to_4_only": 2,
             "B_old_segment_only": 3, "P_autapse_points_only": 4,
             "C_or_no_direct_points": 5}
    root_output.sort(key=lambda r: (order[r["review_band"]],
                                    -int(r["Princeton_2025_published_synapses"]),
                                    -int(r["Buhmann_v783_B_segment_points"]), r["root_id"]))
    for rank, row in enumerate(root_output, 1):
        row["review_rank"] = rank
    write_csv(HERE / "integrated_root_review_queue_616.csv", ROOT_FIELDS, root_output)
    audit = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "candidate_pair_region_rows": len(pair_output),
            "candidate_pair_region_synapse_sum": sum(int(r["Princeton_2025_synapse_count"]) for r in pair_output),
            "roots": len(root_output),
            "review_bands": dict(Counter(r["review_band"] for r in root_output)),
        },
        "inputs_sha256": {str(p.name): sha256(p) for p in (ROOT_QUEUE, P_ROOTS, P_EDGES, P_FILTERED, P_POINTS, EXCLUSIONS)},
        "outputs_sha256": {name: sha256(HERE / name) for name in (
            "princeton_exact_pair_candidates_3233.csv", "integrated_root_review_queue_616.csv")},
        "checks": {
            "princeton_point_rows_reconcile_to_every_published_pair_region": True,
            "original_v783_graph_unmodified": True,
            "alternative_detector_counts_kept_separate": True,
        },
        "interpretation": "The P layer is an alternate automated detector on the same specimen, with point-row provenance and exact official proofread IDs. A/B/C and P remain distinct. Review order is not confidence.",
    }
    (HERE / "integrated_evidence_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(audit["counts"], indent=2))


if __name__ == "__main__":
    main()
