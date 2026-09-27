"""Export verified FAFB-v783 skeleton branches and R7 point calls for the browser.

Only selected neurons are read into memory. Coordinates are shifted to the R7
center and converted from source nanometres to micrometres for stable 3D drawing.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.dataset as ds


ROOT = Path(__file__).resolve().parents[2]
R7 = "720575940623940963"
SELECTED = [
    (R7, "R7", "#d5fc72"),
    ("720575940642650331", "Dm9", "#4ae7dc"),
    ("720575940629825027", "Dm8", "#75a7ff"),
    ("720575940628753128", "Dm11", "#b39cff"),
    ("720575940625217294", "L3", "#ffbd70"),
    ("720575940620875373", "Tm20", "#f277b8"),
]
SKELETON = ROOT / "data/flywire_morphology_v783/sk_lod1_783_healed_ds2.parquet"
OLD = ROOT / "data/research_sources/derived/points_for_616_ids_without_proofread_edges.csv"
NEW = ROOT / "analysis/reconstruction_candidates_v783/princeton_individual_points_for_616.csv"
OUTPUT = ROOT / "app/data/r7_skeleton.json"


def main() -> None:
    if not SKELETON.is_file():
        raise SystemExit("Verified final skeleton Parquet is not present")
    root_ids = [int(item[0]) for item in SELECTED]
    dataset = ds.dataset(SKELETON, format="parquet")
    table = dataset.to_table(
        columns=["neuron", "node_id", "parent_id", "x", "y", "z"],
        filter=ds.field("neuron").isin(root_ids),
    )
    columns = table.to_pydict()
    by_id = {item[0]: [] for item in SELECTED}
    for i in range(table.num_rows):
        root_id = str(columns["neuron"][i])
        by_id[root_id].append([
            int(columns["node_id"][i]), int(columns["parent_id"][i]),
            float(columns["x"][i]), float(columns["y"][i]), float(columns["z"][i]),
        ])
    assert all(by_id[root_id] for root_id, _, _ in SELECTED)
    r7_nodes = by_id[R7]
    center_nm = [
        (min(row[axis] for row in r7_nodes) + max(row[axis] for row in r7_nodes)) / 2
        for axis in (2, 3, 4)
    ]

    def rel(xyz: list[float]) -> list[float]:
        return [round((xyz[i] - center_nm[i]) / 1_000, 4) for i in range(3)]

    skeletons = []
    skeleton_audit = {}
    for root_id, label, color in SELECTED:
        rows = by_id[root_id]
        nodes = {row[0] for row in rows}
        segments = sum(row[1] in nodes and row[1] != row[0] for row in rows)
        skeleton_audit[root_id] = {"nodes": len(rows), "segments": segments,
                                   "root_nodes": sum(row[1] < 0 for row in rows),
                                   "unresolved_parent_refs": sum(row[1] >= 0 and row[1] not in nodes for row in rows)}
        skeletons.append({
            "rootId": root_id, "label": label, "color": color,
            "nodes": [[row[0], row[1], *rel(row[2:5])] for row in rows],
        })

    with OLD.open(newline="", encoding="utf-8") as handle:
        old_rows = [row for row in csv.DictReader(handle)
                    if R7 in (row["pre_root_id"], row["post_root_id"])
                    and row["pre_root_proofread"] == "True"
                    and row["post_root_proofread"] == "True"]
    with NEW.open(newline="", encoding="utf-8") as handle:
        new_rows = [row for row in csv.DictReader(handle)
                    if R7 in (row["pre_root_id"], row["post_root_id"])
                    and row["pre_root_id"] != row["post_root_id"]]

    def old_point(row: dict) -> dict:
        pre = [float(row[f"pre_{axis}_nm"]) for axis in "xyz"]
        post = [float(row[f"post_{axis}_nm"]) for axis in "xyz"]
        return {
            "id": row["synapse_id"], "pre": row["pre_root_id"], "post": row["post_root_id"],
            "region": row["neuropil"], "xyz": rel([(a + b) / 2 for a, b in zip(pre, post)]),
        }

    def new_point(row: dict) -> dict:
        return {
            "id": row["source_row_number"], "pre": row["pre_root_id"], "post": row["post_root_id"],
            "region": row["neuropil"] or "UNASGD", "xyz": rel([float(row[f"ctr_{axis}"]) for axis in "xyz"]),
        }

    payload = {
        "title": "FAFB v783 R7 720575940623940963: Skelett und Detektorpunkte",
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "coordinateFrame": "FAFB v783; source nm shifted by R7 bounding-box center and divided by 1000 to micrometres",
        "centerNm": center_nm,
        "skeletons": skeletons,
        "oldPoints": [old_point(row) for row in old_rows],
        "princetonPoints": [new_point(row) for row in new_rows],
        "caveat": "Both point sets are automated calls; a nearby skeleton branch does not validate synapse identity or physiology. Other Princeton self-contacts are excluded from this view.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    audit = {
        "generated_at_utc": payload["generatedAtUtc"],
        "skeleton_file": str(SKELETON.relative_to(ROOT)).replace("\\", "/"),
        "skeleton_total_rows": 268_281_651,
        "selected_neurons": skeleton_audit,
        "old_points": len(old_rows), "new_non_autapse_points": len(new_rows),
        "old_region_counts": dict(Counter(row["neuropil"] for row in old_rows)),
        "new_region_counts": dict(Counter(row["neuropil"] for row in new_rows)),
        "output": str(OUTPUT.relative_to(ROOT)).replace("\\", "/"),
        "output_bytes": OUTPUT.stat().st_size,
        "caveat": payload["caveat"],
    }
    (Path(__file__).resolve().parent / "skeleton_view_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
