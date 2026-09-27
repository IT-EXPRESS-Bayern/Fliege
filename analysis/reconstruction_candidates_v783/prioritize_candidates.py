"""Build a review queue for v783's 616 proofread roots without aggregate edges.

The queue preserves three independent evidence classes. It never inserts an
edge into the published graph and never equates an unproofread segment with a
whole neuron. Run from any directory with the bundled Python runtime::

    python analysis/reconstruction_candidates_v783/prioritize_candidates.py
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
DERIVED = ROOT / "data/research_sources/derived"
MISSING = DERIVED / "model_missing_fafb_ids.csv"
POINTS = DERIVED / "points_for_616_ids_without_proofread_edges.csv"
RAW = DERIVED / "observed_raw_proofread_edge_exceptions_for_616.csv"
SEGMENTS = DERIVED / "observed_segment_links_for_616.csv"
TYPES = DERIVED / "missing_neuron_type_link_hypotheses.csv"
RAW_AUDIT = ROOT / "analysis/observed_raw_proofread_edge_exceptions_audit.json"
SEGMENT_AUDIT = ROOT / "analysis/observed_segment_links_audit.json"
GLOBAL_AUDIT = ROOT / "analysis/raw_published_edge_reconciliation_audit.json"

RAW_FIELDS = (
    "review_rank", "evidence_tier", "selected_root_id", "selected_cell_type",
    "selected_side", "pre_root_id", "post_root_id", "neuropil",
    "synapse_count", "repeated_support", "synapse_ids", "cleft_score_min",
    "cleft_score_mean", "connection_score_mean", "side_relation",
    "root_dominant_neuropil", "matches_root_dominant_neuropil",
    "photoreceptor_output_gap_flag", "pre_centroid_x_nm", "pre_centroid_y_nm",
    "pre_centroid_z_nm", "post_centroid_x_nm", "post_centroid_y_nm",
    "post_centroid_z_nm", "review_action", "interpretation",
)
SEGMENT_FIELDS = (
    "review_rank", "review_band", "evidence_tier", "proofread_root_id",
    "cell_type", "side", "unproofread_segment_id", "direction", "neuropil",
    "synapse_count", "repeated_support", "synapse_ids", "cleft_score_min",
    "cleft_score_mean", "connection_score_mean", "side_relation",
    "root_dominant_neuropil", "matches_root_dominant_neuropil",
    "segment_seen_from_missing_roots", "photoreceptor_output_gap_flag",
    "pre_centroid_x_nm", "pre_centroid_y_nm", "pre_centroid_z_nm",
    "post_centroid_x_nm", "post_centroid_y_nm", "post_centroid_z_nm",
    "review_action", "interpretation",
)
TYPE_FIELDS = (
    "review_rank", "evidence_tier", "root_id", "cell_type", "side",
    "candidate_target_type", "connected_homologs_same_type_side",
    "homologs_with_target_type", "homolog_support_fraction",
    "published_visual_type_connections", "photoreceptor_output_gap_flag",
    "review_action", "interpretation",
)
ROOT_FIELDS = (
    "review_rank", "root_id", "cell_type", "side", "primary_review_tier",
    "raw_proofread_pair_rows", "raw_proofread_points", "segment_pair_region_rows",
    "segment_points", "repeated_segment_rows", "unproofread_segment_ids",
    "type_hypothesis_rows", "best_homolog_support_fraction",
    "photoreceptor_output_gap_flag", "dominant_observed_neuropil",
    "observed_neuropils", "all_released_pre_points", "all_released_post_points",
    "next_review_action", "interpretation",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, columns: tuple[str, ...], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def point_ids(row: dict[str, str]) -> set[str]:
    ids = row["synapse_ids"].split(";")
    check(len(ids) == int(row["synapse_count"]), "Group synapse_count disagrees with IDs")
    check(len(ids) == len(set(ids)), "Duplicate synapse ID within a group")
    return set(ids)


def side_relation(side: str, neuropil: str) -> str:
    if not neuropil.endswith(("_L", "_R")) or side not in ("left", "right"):
        return "unlateralized_or_unknown"
    return "same_named_side" if (side == "left") == neuropil.endswith("_L") else "opposite_named_side"


def is_photoreceptor(cell_type: str) -> bool:
    # Published photoreceptor-output caveat: R1-6, R7 and R8.
    return cell_type in {"R1-6", "R7", "R8"}


def main() -> None:
    missing_rows = read_csv(MISSING)
    missing = {row["root_id"]: row for row in missing_rows}
    check(len(missing_rows) == len(missing) == 616, "Expected 616 unique missing roots")

    points = read_csv(POINTS)
    raw = read_csv(RAW)
    segments = read_csv(SEGMENTS)
    type_rows = read_csv(TYPES)
    check(len(points) == 7385, "Unexpected released point count")
    check(len(raw) == 21 and len(segments) == 4327, "Unexpected grouped row count")

    raw_audit = json.loads(RAW_AUDIT.read_text(encoding="utf-8"))
    segment_audit = json.loads(SEGMENT_AUDIT.read_text(encoding="utf-8"))
    global_audit = json.loads(GLOBAL_AUDIT.read_text(encoding="utf-8"))
    check(raw_audit["checks"]["all_raw_exception_pair_region_keys_absent_from_published_table"],
          "Upstream exact pair-region check is not valid")
    check(global_audit["region_alignment"]["all_remaining_exceptions_exactly_prior_616_R7_keys"],
          "Global raw/aggregate reconciliation is not valid")
    check(segment_audit["checks"]["segment_output_opposing_partners_absent_from_official_proofread_ids"],
          "Upstream segment proofread-membership check is not valid")
    for source, audit, audit_field in (
        (POINTS, raw_audit, "points_csv_sha256"),
        (RAW, raw_audit, "output_csv_sha256"),
        (SEGMENTS, segment_audit, "output_csv_sha256"),
    ):
        expected = audit.get("inputs", {}).get(audit_field) or audit.get(audit_field)
        check(sha256(source) == expected, f"Input changed since audited: {source.name}")

    observed_ids = set()
    point_lookup = {}
    points_by_root: Counter[str] = Counter()
    neuropils_by_root: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for row in points:
        synapse_id = row["synapse_id"]
        check(synapse_id not in observed_ids, "Duplicate released synapse ID")
        observed_ids.add(synapse_id)
        point_lookup[synapse_id] = row
        touched = {row["pre_root_id"], row["post_root_id"]} & missing.keys()
        check(len(touched) == 1, "Point does not touch exactly one missing root")
        root_id = next(iter(touched))
        points_by_root[root_id] += 1
        neuropils_by_root[root_id][row["neuropil"]] += 1
    dominant = {
        root_id: sorted(counts, key=lambda n: (-counts[n], n))[0]
        for root_id, counts in neuropils_by_root.items()
    }

    raw_ids = set()
    seen_raw_keys = set()
    raw_by_root: defaultdict[str, list[dict]] = defaultdict(list)
    raw_output = []
    for row in raw:
        key = (row["pre_root_id"], row["post_root_id"], row["neuropil"])
        check(key not in seen_raw_keys, "Duplicate proofread pair-region key")
        seen_raw_keys.add(key)
        touched = {row["pre_root_id"], row["post_root_id"]} & missing.keys()
        check(len(touched) == 1, "Raw pair does not touch exactly one missing root")
        root_id = next(iter(touched))
        ids = point_ids(row)
        for synapse_id in ids:
            point = point_lookup.get(synapse_id)
            check(point is not None, "Raw group references unknown point")
            check((point["pre_root_id"], point["post_root_id"], point["neuropil"]) == key,
                  "Raw group disagrees with point pair/neuropil")
            check(point["pre_root_proofread"] == point["post_root_proofread"] == "True",
                  "Raw group includes an unproofread partner")
        check(not (raw_ids & ids), "Synapse IDs overlap across raw groups")
        raw_ids.update(ids)
        raw_by_root[root_id].append(row)
        meta = missing[root_id]
        photo_gap = is_photoreceptor(meta["cell_type"]) and row["pre_root_id"] == root_id
        raw_output.append({
            **row,
            "evidence_tier": "A_raw_exception",
            "selected_root_id": root_id,
            "selected_cell_type": meta["cell_type"],
            "selected_side": meta["side"],
            "repeated_support": "yes" if int(row["synapse_count"]) > 1 else "no",
            "side_relation": side_relation(meta["side"], row["neuropil"]),
            "root_dominant_neuropil": dominant.get(root_id, ""),
            "matches_root_dominant_neuropil": "yes" if row["neuropil"] == dominant.get(root_id) else "no",
            "photoreceptor_output_gap_flag": "yes" if photo_gap else "no",
            "review_action": "Inspect exact released points and why the published pair table omitted this key",
            "interpretation": "Released automated calls between two proofread roots; not a physiologically validated connection",
        })
    raw_output.sort(key=lambda r: (
        -int(r["synapse_count"]), -float(r["cleft_score_min"]),
        -float(r["cleft_score_mean"]), -float(r["connection_score_mean"]),
        r["pre_root_id"], r["post_root_id"], r["neuropil"],
    ))
    for rank, row in enumerate(raw_output, 1):
        row["review_rank"] = rank

    segment_ids = set()
    seen_segment_keys = set()
    segment_to_roots: defaultdict[str, set[str]] = defaultdict(set)
    segment_by_root: defaultdict[str, list[dict]] = defaultdict(list)
    segment_output = []
    for row in segments:
        root_id = row["proofread_root_id"]
        check(root_id in missing, "Segment contact refers to non-missing root")
        key = (row["pre_root_id"], row["post_root_id"], row["neuropil"])
        check(key not in seen_segment_keys, "Duplicate segment pair-region key")
        seen_segment_keys.add(key)
        check(row["unproofread_segment_id"] not in missing,
              "Unproofread segment coincides with missing proofread root")
        ids = point_ids(row)
        for synapse_id in ids:
            point = point_lookup.get(synapse_id)
            check(point is not None, "Segment group references unknown point")
            check((point["pre_root_id"], point["post_root_id"], point["neuropil"]) == key,
                  "Segment group disagrees with point pair/neuropil")
            expected_flags = ("True", "False") if row["direction"] == "proofread_to_segment" else ("False", "True")
            check((point["pre_root_proofread"], point["post_root_proofread"]) == expected_flags,
                  "Segment group disagrees with point proofreading flags")
        check(not (segment_ids & ids), "Synapse IDs overlap across segment groups")
        segment_ids.update(ids)
        segment_to_roots[row["unproofread_segment_id"]].add(root_id)
        segment_by_root[root_id].append(row)
        meta = missing[root_id]
        photo_gap = is_photoreceptor(meta["cell_type"]) and row["direction"] == "proofread_to_segment"
        segment_output.append({
            **row,
            "review_band": "B_repeated_points" if int(row["synapse_count"]) > 1 else "B_single_point",
            "cell_type": meta["cell_type"],
            "side": meta["side"],
            "repeated_support": "yes" if int(row["synapse_count"]) > 1 else "no",
            "side_relation": side_relation(meta["side"], row["neuropil"]),
            "root_dominant_neuropil": dominant.get(root_id, ""),
            "matches_root_dominant_neuropil": "yes" if row["neuropil"] == dominant.get(root_id) else "no",
            "photoreceptor_output_gap_flag": "yes" if photo_gap else "no",
            "review_action": "Inspect segment morphology and proofreading status in the same v783 coordinate frame",
            "interpretation": "Released directed contact to an unproofread segment, not an identified neuron-neuron edge",
        })
    check(not (raw_ids & segment_ids), "A-raw and B synapse IDs overlap")
    check(raw_ids | segment_ids == observed_ids, "Grouped synapses do not exhaust the 7,385 points")
    check(len(raw_ids) == 48 and len(segment_ids) == 7337, "A/B point totals changed")
    for row in segment_output:
        row["segment_seen_from_missing_roots"] = len(segment_to_roots[row["unproofread_segment_id"]])
    segment_output.sort(key=lambda r: (
        -(int(r["synapse_count"]) > 1),
        -int(r["synapse_count"]),
        -int(r["photoreceptor_output_gap_flag"] == "yes"),
        -float(r["cleft_score_min"]),
        -float(r["connection_score_mean"]),
        r["proofread_root_id"], r["unproofread_segment_id"], r["direction"], r["neuropil"],
    ))
    for rank, row in enumerate(segment_output, 1):
        row["review_rank"] = rank

    type_output = []
    seen_type_keys = set()
    type_by_root: defaultdict[str, list[dict]] = defaultdict(list)
    for row in type_rows:
        root_id = row["root_id"]
        check(root_id in missing, "Type hypothesis refers to non-missing root")
        if row["status"] != "type_level_hypothesis_only":
            check(not row["candidate_target_type"], "Unsupported row has a target type")
            continue
        check(bool(row["candidate_target_type"]), "Type hypothesis has no target type")
        type_key = (root_id, row["candidate_target_type"])
        check(type_key not in seen_type_keys, "Duplicate cell-type hypothesis")
        seen_type_keys.add(type_key)
        peer_count = int(row["connected_homologs_same_type_side"])
        supporting = int(row["homologs_with_target_type"])
        check(peer_count >= 10 and supporting >= 3 and supporting <= peer_count,
              "Type-peer support violates upstream selection rules")
        check(abs(supporting / peer_count - float(row["homolog_support_fraction"])) <= 0.00006,
              "Type-peer fraction disagrees with counts")
        photo_gap = is_photoreceptor(row["cell_type"])
        type_output.append({
            **row,
            "evidence_tier": "C_type_hypothesis",
            "photoreceptor_output_gap_flag": "yes" if photo_gap else "no",
            "review_action": "Use as a cell-type search term; require an observed exact pair before adding an edge",
            "interpretation": "Homolog incidence is not an edge probability or a named target neuron",
        })
        type_by_root[root_id].append(row)
    type_output.sort(key=lambda r: (
        -float(r["homolog_support_fraction"]),
        -int(r["homologs_with_target_type"]),
        -int(r["published_visual_type_connections"] or 0),
        r["root_id"], r["candidate_target_type"],
    ))
    for rank, row in enumerate(type_output, 1):
        row["review_rank"] = rank

    root_output = []
    for root_id, meta in missing.items():
        raw_rows = raw_by_root[root_id]
        segment_rows = segment_by_root[root_id]
        hypothesis_rows = type_by_root[root_id]
        raw_points = sum(int(r["synapse_count"]) for r in raw_rows)
        segment_points = sum(int(r["synapse_count"]) for r in segment_rows)
        released_pre = int(next((r["released_pre_points"] for r in type_rows if r["root_id"] == root_id), "0"))
        released_post = int(next((r["released_post_points"] for r in type_rows if r["root_id"] == root_id), "0"))
        check(raw_points + segment_points == points_by_root[root_id] == released_pre + released_post,
              f"Per-root released point mismatch: {root_id}")
        tier = ("A_raw_exception" if raw_rows else "B_segment_contact" if segment_rows
                else "C_type_only" if hypothesis_rows else "no_released_support")
        next_action = {
            "A_raw_exception": "Inspect 21 raw/published discrepancy keys and original contact sites",
            "B_segment_contact": "Review unproofread segment identity using v783 morphology/proofreading",
            "C_type_only": "Search same-type anatomy; no released contact for this root",
            "no_released_support": "Await new segmentation/synapse evidence; do not create an edge",
        }[tier]
        root_output.append({
            "root_id": root_id,
            "cell_type": meta["cell_type"],
            "side": meta["side"],
            "primary_review_tier": tier,
            "raw_proofread_pair_rows": len(raw_rows),
            "raw_proofread_points": raw_points,
            "segment_pair_region_rows": len(segment_rows),
            "segment_points": segment_points,
            "repeated_segment_rows": sum(int(r["synapse_count"]) > 1 for r in segment_rows),
            "unproofread_segment_ids": len({r["unproofread_segment_id"] for r in segment_rows}),
            "type_hypothesis_rows": len(hypothesis_rows),
            "best_homolog_support_fraction": max((float(r["homolog_support_fraction"]) for r in hypothesis_rows), default=0),
            "photoreceptor_output_gap_flag": "yes" if is_photoreceptor(meta["cell_type"]) else "no",
            "dominant_observed_neuropil": dominant.get(root_id, ""),
            "observed_neuropils": ";".join(f"{n}:{c}" for n, c in neuropils_by_root[root_id].most_common()),
            "all_released_pre_points": released_pre,
            "all_released_post_points": released_post,
            "next_review_action": next_action,
            "interpretation": "Inspection priority only; absence of released points does not prove biological disconnection",
        })
    tier_order = {"A_raw_exception": 0, "B_segment_contact": 1, "C_type_only": 2, "no_released_support": 3}
    root_output.sort(key=lambda r: (
        tier_order[r["primary_review_tier"]],
        -int(r["raw_proofread_points"]),
        -int(r["repeated_segment_rows"]),
        -int(r["segment_points"]),
        -int(r["photoreceptor_output_gap_flag"] == "yes"),
        -float(r["best_homolog_support_fraction"]),
        r["root_id"],
    ))
    for rank, row in enumerate(root_output, 1):
        row["review_rank"] = rank

    outputs = {
        "raw_proofread_exceptions_ranked.csv": (RAW_FIELDS, raw_output),
        "segment_contacts_ranked.csv": (SEGMENT_FIELDS, segment_output),
        "type_hypotheses_ranked.csv": (TYPE_FIELDS, type_output),
        "root_review_queue.csv": (ROOT_FIELDS, root_output),
    }
    for filename, (columns, rows) in outputs.items():
        write_csv(HERE / filename, columns, rows)
    audit = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "method_version": 1,
        "source_release": "FlyWire FAFB v783",
        "sources": {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
                    for path in (MISSING, POINTS, RAW, SEGMENTS, TYPES, RAW_AUDIT,
                                 SEGMENT_AUDIT, GLOBAL_AUDIT)},
        "counts": {
            "proofread_roots_without_aggregate_edges": len(missing),
            "released_point_ids": len(observed_ids),
            "A_raw_pair_region_rows": len(raw_output),
            "A_raw_points": len(raw_ids),
            "B_segment_pair_region_rows": len(segment_output),
            "B_segment_points": len(segment_ids),
            "B_distinct_unproofread_segments": len(segment_to_roots),
            "B_repeated_rows": sum(int(r["synapse_count"]) > 1 for r in segment_output),
            "B_rows_with_shared_unproofread_segment": sum(
                int(r["segment_seen_from_missing_roots"]) > 1 for r in segment_output),
            "C_supported_type_hypothesis_rows": len(type_output),
            "C_roots_with_hypotheses": sum(bool(rows) for rows in type_by_root.values()),
            "root_review_tiers": dict(Counter(r["primary_review_tier"] for r in root_output)),
            "roots_without_released_points": sum(
                int(r["all_released_pre_points"]) + int(r["all_released_post_points"]) == 0
                for r in root_output),
            "photoreceptor_roots": sum(is_photoreceptor(r["cell_type"]) for r in root_output),
        },
        "checks": {
            "all_grouped_synapse_ids_unique_and_exhaustive": raw_ids | segment_ids == observed_ids,
            "A_raw_global_reconciliation_verified": True,
            "B_opposing_partners_unproofread_verified_upstream": True,
            "616_root_counts_reconcile_with_released_points": True,
            "official_graph_unchanged": True,
        },
        "ranking": {
            "purpose": "manual inspection priority, not confidence or calibrated probability",
            "evidence_order": ["A_raw_exception", "B_segment_contact", "C_type_only", "no_released_support"],
            "A_order": "more repeated exact raw points; then cleft minimum/mean and connection mean as tie breakers",
            "B_order": "repeated point groups, number of points, photoreceptor-output gap flag, then detector-score tie breakers",
            "C_order": "same-type same-side peer incidence, then visual-matrix support; never exact target root",
            "site_context": "side_relation and dominant neuropil are review flags, not rejection criteria; contralateral contacts may be real",
            "score_caveat": "detector scores are neither physiological weights nor calibrated probabilities",
            "morphology": "No spatial score enters this raw-point ranking; verified skeleton checks are reported separately in morphology_priority_site_check.json",
        },
        "outputs": {filename: {"rows": len(rows), "sha256": sha256(HERE / filename)}
                    for filename, (_, rows) in outputs.items()},
        "source_urls": [
            "https://zenodo.org/records/10676866",
            "https://www.nature.com/articles/s41586-024-07558-y",
            "https://www.nature.com/articles/s41586-024-07981-1",
        ],
    }
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(audit["counts"], indent=2))


if __name__ == "__main__":
    main()
