"""Bounded-memory skeleton proximity check for two concrete priority cases.

Distance to a skeleton centreline is an anatomical consistency indicator only.
It cannot verify an EM synapse, a segmentation merge, or functional signaling.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SKELETON = ROOT / "data/flywire_morphology_v783/sk_lod1_783_healed_ds2.parquet"
PRINCETON = HERE / "princeton_individual_points_for_616.csv"
BUHMANN = ROOT / "data/research_sources/derived/points_for_616_ids_without_proofread_edges.csv"
CASES = (
    ("P_same_specimen_photoreceptor_to_proofread_partner", "Princeton_2025",
     "720575940631647173", "720575940626013112", "LA_R"),
    ("B_old_photoreceptor_to_unproofread_segment", "Buhmann_2024",
     "720575940638820442", "720575940622062913", "LA_L"),
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def nearest_nm(site: tuple[float, float, float], xyz: np.ndarray) -> float | None:
    if not len(xyz):
        return None
    point = np.array(site, dtype=np.float64)
    best_sq = float("inf")
    for start in range(0, len(xyz), 50000):
        delta = xyz[start:start + 50000].astype(np.float64, copy=False) - point
        best_sq = min(best_sq, float(np.min(np.einsum("ij,ij->i", delta, delta))))
    return float(np.sqrt(best_sq))


def describe_distances(distances: list[float | None]) -> dict:
    valid = np.array([d for d in distances if d is not None], dtype=np.float64)
    if not len(valid):
        return {"sites_with_skeleton": 0, "sites_without_skeleton": len(distances)}
    return {
        "sites_with_skeleton": len(valid),
        "sites_without_skeleton": len(distances) - len(valid),
        "minimum_nm": round(float(np.min(valid)), 3),
        "median_nm": round(float(np.median(valid)), 3),
        "p90_nm": round(float(np.quantile(valid, 0.9)), 3),
        "maximum_nm": round(float(np.max(valid)), 3),
    }


def main() -> None:
    if not SKELETON.is_file():
        raise FileNotFoundError("Verified final skeleton parquet pending")
    expected_ids = {int(pre) for _, _, pre, _, _ in CASES} | {int(post) for _, _, _, post, _ in CASES}
    selected: defaultdict[int, list[np.ndarray]] = defaultdict(list)
    file = pq.ParquetFile(SKELETON)
    scanned = 0
    for batch in file.iter_batches(batch_size=500000, columns=["neuron", "x", "y", "z"]):
        neurons = batch.column(0).to_numpy(zero_copy_only=False)
        scanned += len(neurons)
        keep = np.isin(neurons, list(expected_ids))
        if not np.any(keep):
            continue
        x = batch.column(1).to_numpy(zero_copy_only=False)
        y = batch.column(2).to_numpy(zero_copy_only=False)
        z = batch.column(3).to_numpy(zero_copy_only=False)
        for rid in expected_ids:
            own = keep & (neurons == rid)
            if np.any(own):
                selected[rid].append(np.column_stack((x[own], y[own], z[own])))
    skeletons = {rid: np.concatenate(parts) if parts else np.empty((0, 3), dtype=np.float32)
                 for rid, parts in ((rid, selected.get(rid, [])) for rid in expected_ids)}
    old_rows = read_csv(BUHMANN)
    new_rows = read_csv(PRINCETON)
    findings = []
    for label, detector, pre, post, neuropil in CASES:
        source = new_rows if detector == "Princeton_2025" else old_rows
        pair = [r for r in source if r["pre_root_id"] == pre and r["post_root_id"] == post
                and r["neuropil"] == neuropil]
        pre_dist = []
        post_dist = []
        for row in pair:
            suffix = "" if detector == "Princeton_2025" else "_nm"
            pre_site = tuple(float(row[f"pre_{axis}{suffix}"]) for axis in "xyz")
            post_site = tuple(float(row[f"post_{axis}{suffix}"]) for axis in "xyz")
            pre_dist.append(nearest_nm(pre_site, skeletons[int(pre)]))
            post_dist.append(nearest_nm(post_site, skeletons[int(post)]))
        findings.append({
            "case": label,
            "detector": detector,
            "pre_root_id": pre,
            "post_root_or_segment_id": post,
            "neuropil": neuropil,
            "point_calls": len(pair),
            "pre_skeleton_nodes": len(skeletons[int(pre)]),
            "post_skeleton_nodes": len(skeletons[int(post)]),
            "pre_site_to_nearest_pre_skeleton_node": describe_distances(pre_dist),
            "post_site_to_nearest_post_skeleton_node": describe_distances(post_dist),
            "interpretation": "Proximity to released skeleton centreline supports coordinate/anatomy consistency only; no functional or segmentation identity claim",
        })
    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(SKELETON.relative_to(ROOT)).replace("\\", "/"),
        "source_url": "https://zenodo.org/records/10877326",
        "skeleton_rows_scanned": scanned,
        "skeleton_nodes_by_selected_id": {str(rid): len(xyz) for rid, xyz in skeletons.items()},
        "findings": findings,
        "limitations": "Nearest centreline distance ignores local neurite radius and skeleton downsampling. A missing skeleton for an unproofread segment is expected and does not prove absence of the segment. Positive proximity is not evidence that an automated synapse call is correct.",
    }
    (HERE / "morphology_priority_site_check.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
