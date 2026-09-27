"""Compare same-specimen Princeton synapse re-detections with original v783 gaps.

Streams the official Codex FAFB v783 CSV exports. Only ordered pairs touching
one of the 616 original proofread roots without an aggregate edge are retained.
The two detector releases are never summed. The filtered file has a >=5
synapses-per-ordered-pair export cutoff; the no-threshold file is preferred for
completeness once verified and downloaded.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CODEX = ROOT / "data/codex_fafb_v783"
MISSING = ROOT / "data/research_sources/derived/model_missing_fafb_ids.csv"
RAW = ROOT / "data/research_sources/derived/observed_raw_proofread_edge_exceptions_for_616.csv"
PROOFREAD = ROOT / "data/flywire_fafb_v783/proofread_root_ids_783.npy"
FILES = {
    "filtered_ge5_pair": CODEX / "connections_princeton.csv.gz",
    "unfiltered": CODEX / "connections_princeton_no_threshold.csv.gz",
}
GCS_BASE = "https://storage.googleapis.com/flywire-data/codex/data/fafb/783/"
PINNED_MD5 = {
    "filtered_ge5_pair": "5e5101c6ffc17d7e300541d8f71842c1",
    "unfiltered": "694f7e5bd018b83c71eeb0ba55b50e7e",
}
CONNECTION_FIELDS = (
    "detector_release", "export_filter", "evidence_tier", "selected_root_id",
    "selected_cell_type", "selected_side", "pre_root_id", "post_root_id",
    "partner_root_id", "partner_in_official_proofread_array", "neuropil",
    "synapse_count", "source_rows_combined", "nt_type_labels", "same_pair_region_as_Buhmann_raw_A",
    "same_directed_pair_as_Buhmann_raw_A", "Buhmann_raw_A_points_same_pair_region",
    "interpretation",
)
ROOT_FIELDS = (
    "root_id", "cell_type", "side", "Buhmann_original_aggregate_edges",
    "Buhmann_raw_A_pair_region_rows", "Buhmann_raw_A_points",
    "Princeton_filtered_pair_region_rows", "Princeton_filtered_directed_pairs",
    "Princeton_filtered_synapse_count", "Princeton_unfiltered_pair_region_rows",
    "Princeton_unfiltered_directed_pairs", "Princeton_unfiltered_synapse_count",
    "interpretation",
)
RAW_FIELDS = (
    "pre_root_id", "post_root_id", "neuropil", "Buhmann_raw_A_points",
    "Princeton_filtered_synapse_count", "Princeton_unfiltered_synapse_count",
    "filtered_same_pair_region", "unfiltered_same_pair_region",
    "interpretation",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def hash_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def scan(path: Path, missing: dict[str, dict], proofread: set[str]) -> tuple[dict, dict]:
    aggregates: dict[tuple[str, str, str], dict] = {}
    all_rows = 0
    all_synapses = 0
    touching_rows = 0
    touching_synapses = 0
    outside_official_proofread = 0
    touching_rows_with_two_selected_roots = 0
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        check(set(reader.fieldnames or []) == {"pre_root_id", "post_root_id", "neuropil", "syn_count", "nt_type"},
              f"Unexpected schema in {path.name}")
        for row in reader:
            all_rows += 1
            count = int(row["syn_count"])
            check(count > 0, f"Nonpositive synapse count in {path.name}")
            all_synapses += count
            pre, post = row["pre_root_id"], row["post_root_id"]
            if pre not in missing and post not in missing:
                continue
            touching_rows += 1
            touching_synapses += count
            touching_rows_with_two_selected_roots += int(pre in missing and post in missing)
            if pre not in proofread or post not in proofread:
                outside_official_proofread += 1
            key = pre, post, row["neuropil"]
            item = aggregates.setdefault(key, {"synapse_count": 0, "source_rows_combined": 0, "nt_labels": Counter()})
            item["synapse_count"] += count
            item["source_rows_combined"] += 1
            item["nt_labels"][row["nt_type"] or "(blank)"] += count
    summary = {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "gcs_url": GCS_BASE + path.name,
        "file_bytes": path.stat().st_size,
        "md5": hash_file(path, "md5"),
        "sha256": hash_file(path, "sha256"),
        "all_source_rows": all_rows,
        "all_source_synapse_count": all_synapses,
        "source_rows_touching_616": touching_rows,
        "source_synapses_touching_616": touching_synapses,
        "pair_region_keys_touching_616": len(aggregates),
        "directed_pairs_touching_616": len({key[:2] for key in aggregates}),
        "partner_rows_outside_official_proofread_ids": outside_official_proofread,
        "source_rows_with_both_partners_among_616": touching_rows_with_two_selected_roots,
    }
    return aggregates, summary


def main() -> None:
    missing_rows = read_csv(MISSING)
    missing = {row["root_id"]: row for row in missing_rows}
    check(len(missing_rows) == len(missing) == 616, "Expected 616 distinct original missing roots")
    proofread = set(map(str, np.load(PROOFREAD, allow_pickle=False).tolist()))
    check(missing.keys() <= proofread, "616 IDs are not all in the original official proofread array")
    raw_rows = read_csv(RAW)
    raw_map = {(r["pre_root_id"], r["post_root_id"], r["neuropil"]): int(r["synapse_count"])
               for r in raw_rows}
    check(len(raw_rows) == len(raw_map) == 21 and sum(raw_map.values()) == 48,
          "Original 21/48 A-raw exception set changed")
    raw_pairs = {key[:2] for key in raw_map}
    aggregate_by_file = {}
    source_summary = {}
    for label, path in FILES.items():
        if path.is_file():
            aggregate_by_file[label], source_summary[label] = scan(path, missing, proofread)
        else:
            source_summary[label] = {"status": "pending", "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                                     "gcs_url": GCS_BASE + path.name}
    check("filtered_ge5_pair" in aggregate_by_file, "Filtered official Codex file is required")
    check(source_summary["filtered_ge5_pair"]["md5"] == "5e5101c6ffc17d7e300541d8f71842c1",
          "Filtered Codex file does not match the independently pinned GCS MD5")
    if "unfiltered" in aggregate_by_file:
        check(source_summary["unfiltered"]["md5"] == PINNED_MD5["unfiltered"],
              "Unfiltered Codex file does not match the GCS MD5")
    if "unfiltered" in aggregate_by_file:
        filtered = aggregate_by_file["filtered_ge5_pair"]
        unfiltered = aggregate_by_file["unfiltered"]
        check(filtered.keys() <= unfiltered.keys(), "Unfiltered file lacks keys from filtered Codex export")
        check(all(unfiltered[k]["synapse_count"] == v["synapse_count"] for k, v in filtered.items()),
              "Filtered and unfiltered counts disagree at a shared pair-region key")
        unfiltered_pair_counts = Counter()
        for (pre, post, _region), item in unfiltered.items():
            unfiltered_pair_counts[(pre, post)] += item["synapse_count"]
        check({pair for pair, n in unfiltered_pair_counts.items() if n >= 5}
              == {key[:2] for key in filtered},
              "Filtered ordered pairs do not exactly equal unfiltered pairs with >=5 synapses")

    connection_outputs = {}
    for label, aggregates in aggregate_by_file.items():
        rows = []
        for (pre, post, neuropil), item in aggregates.items():
          for root_id in ({pre, post} & missing.keys()):
            partner = post if root_id == pre else pre
            rows.append({
                "detector_release": "Princeton_2025_same_FAFB_v783_roots",
                "export_filter": label,
                "evidence_tier": "P_alternative_automated_detector",
                "selected_root_id": root_id,
                "selected_cell_type": missing[root_id]["cell_type"],
                "selected_side": missing[root_id]["side"],
                "pre_root_id": pre,
                "post_root_id": post,
                "partner_root_id": partner,
                "partner_in_official_proofread_array": "yes" if partner in proofread else "no",
                "neuropil": neuropil,
                "synapse_count": item["synapse_count"],
                "source_rows_combined": item["source_rows_combined"],
                "nt_type_labels": ";".join(f"{n}:{c}" for n, c in sorted(item["nt_labels"].items())),
                "same_pair_region_as_Buhmann_raw_A": "yes" if (pre, post, neuropil) in raw_map else "no",
                "same_directed_pair_as_Buhmann_raw_A": "yes" if (pre, post) in raw_pairs else "no",
                "Buhmann_raw_A_points_same_pair_region": raw_map.get((pre, post, neuropil), 0),
                "interpretation": "Alternative automated synapse calls in the same specimen; not original v783 measured graph or physiological validation",
            })
        rows.sort(key=lambda r: (-int(r["synapse_count"]), r["selected_root_id"],
                                 r["pre_root_id"], r["post_root_id"], r["neuropil"]))
        filename = f"princeton_{label}_for_616.csv"
        write_csv(HERE / filename, CONNECTION_FIELDS, rows)
        connection_outputs[label] = {"file": filename, "rows": len(rows), "sha256": hash_file(HERE / filename, "sha256")}

    per_root = {}
    for label, aggregates in aggregate_by_file.items():
        per_root[label] = defaultdict(lambda: {"pair_region_rows": 0, "directed_pair_keys": set(), "synapses": 0})
        for key, val in aggregates.items():
            for root_id in (set(key[:2]) & missing.keys()):
                item = per_root[label][root_id]
                item["pair_region_rows"] += 1
                item["directed_pair_keys"].add(key[:2])
                item["synapses"] += val["synapse_count"]
    root_output = []
    for root_id, meta in missing.items():
        counts = {}
        for label, root_counts in per_root.items():
            relevant = root_counts[root_id]
            counts[label] = {
                "pair_region_rows": relevant["pair_region_rows"],
                "directed_pairs": len(relevant["directed_pair_keys"]),
                "synapses": relevant["synapses"],
            }
        a_raw = [(key, n) for key, n in raw_map.items() if root_id in key[:2]]
        root_output.append({
            "root_id": root_id, "cell_type": meta["cell_type"], "side": meta["side"],
            "Buhmann_original_aggregate_edges": 0,
            "Buhmann_raw_A_pair_region_rows": len(a_raw),
            "Buhmann_raw_A_points": sum(n for _, n in a_raw),
            "Princeton_filtered_pair_region_rows": counts.get("filtered_ge5_pair", {}).get("pair_region_rows", ""),
            "Princeton_filtered_directed_pairs": counts.get("filtered_ge5_pair", {}).get("directed_pairs", ""),
            "Princeton_filtered_synapse_count": counts.get("filtered_ge5_pair", {}).get("synapses", ""),
            "Princeton_unfiltered_pair_region_rows": counts.get("unfiltered", {}).get("pair_region_rows", ""),
            "Princeton_unfiltered_directed_pairs": counts.get("unfiltered", {}).get("directed_pairs", ""),
            "Princeton_unfiltered_synapse_count": counts.get("unfiltered", {}).get("synapses", ""),
            "interpretation": "Counts from two alternative Codex exports are compared, never added to each other or original v783",
        })
    root_output.sort(key=lambda r: (
        -int(r["Princeton_unfiltered_synapse_count"] or r["Princeton_filtered_synapse_count"] or 0),
        r["root_id"],
    ))
    write_csv(HERE / "princeton_root_coverage_616.csv", ROOT_FIELDS, root_output)

    overlap_output = []
    for key, original_count in sorted(raw_map.items()):
        filtered_count = aggregate_by_file["filtered_ge5_pair"].get(key, {}).get("synapse_count", 0)
        unfiltered_count = (aggregate_by_file["unfiltered"].get(key, {}).get("synapse_count", 0)
                            if "unfiltered" in aggregate_by_file else "")
        overlap_output.append({
            "pre_root_id": key[0], "post_root_id": key[1], "neuropil": key[2],
            "Buhmann_raw_A_points": original_count,
            "Princeton_filtered_synapse_count": filtered_count,
            "Princeton_unfiltered_synapse_count": unfiltered_count,
            "filtered_same_pair_region": "yes" if filtered_count else "no",
            "unfiltered_same_pair_region": "yes" if unfiltered_count else "no" if unfiltered_count == 0 else "pending",
            "interpretation": "Same directed pair and neuropil only; no point-level equivalence or combined weight implied",
        })
    write_csv(HERE / "princeton_overlap_with_21_Buhmann_raw_pairs.csv", RAW_FIELDS, overlap_output)

    audit = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_release": "FlyWire FAFB root IDs v783, Princeton 2025 alternate synapse detector",
        "source_docs": [
            "https://codex.flywire.ai/faq",
            "https://natverse.org/fafbseg/reference/flywire_connectome_data.html",
            "https://zenodo.org/records/17918331",
        ],
        "original_v783_source": "https://zenodo.org/records/10676866",
        "source_files": source_summary,
        "input_sha256": {
            str(p.relative_to(ROOT)).replace("\\", "/"): hash_file(p, "sha256")
            for p in (MISSING, RAW, PROOFREAD)
        },
        "counts": {
            "missing_original_roots": len(missing),
            "Buhmann_A_raw_pair_region_rows": len(raw_map),
            "Buhmann_A_raw_points": sum(raw_map.values()),
            **{
                f"{label}_roots_with_any_connection": sum(
                    counts["pair_region_rows"] > 0 for counts in per_root[label].values()
                ) for label in aggregate_by_file
            },
            **{
                f"{label}_same_pair_region_as_Buhmann_A_raw": sum(key in agg for key in raw_map)
                for label, agg in aggregate_by_file.items()
            },
        },
        "checks": {
            "all_616_original_ids_officially_proofread": True,
            "filtered_gcs_md5_matches_pinned_value": True,
            "filtered_subset_of_unfiltered_where_available": "unfiltered" in aggregate_by_file,
            "filtered_pairs_equal_unfiltered_pairs_with_total_ge5": "unfiltered" in aggregate_by_file,
            "unfiltered_gcs_md5_matches_pinned_value": "unfiltered" in aggregate_by_file,
            "original_graph_left_unchanged": True,
        },
        "outputs": {
            **connection_outputs,
            "root_coverage": {"file": "princeton_root_coverage_616.csv", "rows": len(root_output),
                              "sha256": hash_file(HERE / "princeton_root_coverage_616.csv", "sha256")},
            "R7_raw_overlap": {"file": "princeton_overlap_with_21_Buhmann_raw_pairs.csv", "rows": len(overlap_output),
                               "sha256": hash_file(HERE / "princeton_overlap_with_21_Buhmann_raw_pairs.csv", "sha256")},
        },
        "limitation": "These are alternative automated synapse detections on the same FAFB segmentation, not newly proofread point-level connections or physiological measurements. The >=5 filtered export omits weaker ordered pairs. Counts from detector releases must not be summed.",
    }
    (HERE / "princeton_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"sources": source_summary, "counts": audit["counts"]}, indent=2))


if __name__ == "__main__":
    main()
