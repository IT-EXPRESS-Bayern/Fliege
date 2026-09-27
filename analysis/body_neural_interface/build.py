"""Export BANC leg motor evidence and an explicit, uncalibrated body-channel proposal.

Run: analysis/.venv/Scripts/python.exe analysis/body_neural_interface/build.py
All neuron IDs remain strings. No FAFB graph or motor controller is changed.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import json

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as feather
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "data/research_sources/other/banc_2026"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def write_csv(name, rows):
    with (OUT / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def proposal(action):
    if action in ("flex_femur_tibia_joint", "extend_femur_tibia_joint"):
        return "femurTibia", "geometric_joint_candidate"
    if action in ("flex_tibia_tarsus_joint", "extend_tibia_tarsus_joint"):
        return "tibiaTarsus", "geometric_joint_candidate"
    if action in ("flex_coxa_trochanter_joint", "extend_coxa_trochanter_joint"):
        return "femurElevation", "reduced_joint_candidate"
    if action and action.startswith("move_coxa_"):
        return "coxaAzimuth", "axis_calibration_required"
    if action == "pull_long_tendon":
        return None, "tendon_model_missing"
    return None, "function_unresolved"


def main():
    provenance = json.loads((SOURCE / "provenance.json").read_text(encoding="utf-8-sig"))
    inputs = {}
    for name in ["banc_888_meta.feather", "banc_888_edgelist_simple_v2.feather", "banc_888_edgelist_simple_v3.feather"]:
        path = SOURCE / name
        published = next(f for f in provenance["files"] if f["path"].endswith("/" + name))
        checksum = sha(path)
        assert checksum == published["sha256"]
        inputs[name] = {"sha256": checksum, "source_url": published["source_url"], "bytes": path.stat().st_size}
    cols = ["banc_888_id", "super_class", "cell_class", "cell_type", "side", "nerve", "body_part_effector", "body_part_sensory", "cell_function_detailed", "peripheral_target_type", "proofread", "roughly_proofread"]
    meta = feather.read_table(SOURCE / "banc_888_meta.feather", columns=cols)
    selected = pc.and_(pc.equal(meta["super_class"], "motor"), pc.is_in(meta["body_part_effector"], value_set=pa.array(["front_leg", "middle_leg", "hind_leg"])))
    motors = meta.filter(selected).to_pylist()
    rows = []
    for motor in sorted(motors, key=lambda r: r["banc_888_id"]):
        assert motor["side"] in ("left", "right")
        assert motor["nerve"].startswith(motor["side"] + "_")
        leg = motor["side"][0].upper() + {"front_leg": "F", "middle_leg": "M", "hind_leg": "H"}[motor["body_part_effector"]]
        channel, status = proposal(motor["cell_function_detailed"])
        rows.append({**motor, "namespace": "BANC_v888", "candidate_model_leg": leg,
                     "candidate_observation_channel": channel, "mapping_status": status,
                     "actuator_sign": None, "force_gain": None,
                     "enabled_for_control": False})
    assert len(rows) == len({r["banc_888_id"] for r in rows}) == 391
    write_csv("banc_leg_motor_channels_391.csv", rows)
    by_id = {r["banc_888_id"]: r for r in rows}
    motor_ids = pa.array(sorted(by_id), type=pa.string())
    maps = {}
    graph_stats = {}
    for version in ("v2", "v3"):
        graph = feather.read_table(SOURCE / f"banc_888_edgelist_simple_{version}.feather", columns=["pre", "post", "count"])
        incoming = graph.filter(pc.and_(pc.is_in(graph["post"], value_set=motor_ids), pc.not_equal(graph["pre"], graph["post"])))
        pq.write_table(incoming, OUT / f"banc_motor_incoming_{version}.parquet", compression="zstd")
        records = incoming.to_pylist()
        maps[version] = {(r["pre"], r["post"]): r["count"] for r in records}
        assert len(maps[version]) == len(records)
        graph_stats[version] = {"nonself_directed_pairs": len(records), "sum_count": sum(r["count"] for r in records), "upstream_roots": len({r["pre"] for r in records}), "motor_roots_with_input": len({r["post"] for r in records})}
    upstream_ids = sorted({pre for m in maps.values() for pre, post in m})
    upstream = meta.filter(pc.is_in(meta["banc_888_id"], value_set=pa.array(upstream_ids)))
    pq.write_table(upstream, OUT / "banc_motor_upstream_metadata.parquet", compression="zstd")
    comparison = []
    for pre, post in sorted(maps["v2"].keys() | maps["v3"].keys()):
        a, b = maps["v2"].get((pre, post)), maps["v3"].get((pre, post))
        comparison.append({"pre_banc_id": pre, "post_banc_motor_id": post, "v2_count": a, "v3_count": b, "present_both": a is not None and b is not None, "at_least_5_both": a is not None and b is not None and min(a, b) >= 5, "candidate_model_leg": by_id[post]["candidate_model_leg"], "source_action": by_id[post]["cell_function_detailed"]})
    pq.write_table(pa.Table.from_pylist(comparison), OUT / "banc_motor_input_detector_comparison.parquet", compression="zstd")
    audit = {
        "created_utc": datetime.now(timezone.utc).isoformat(), "namespace": "BANC_v888",
        "dataset_doi": "https://doi.org/10.7910/DVN/7WTH1N", "paper": "https://doi.org/10.1038/s41586-026-10735-w", "license": "CC BY 4.0", "inputs": inputs,
        "source_metadata_rows": meta.num_rows, "leg_motor_roots": len(rows),
        "leg_counts": dict(Counter(r["candidate_model_leg"] for r in rows)),
        "source_action_counts": dict(Counter(r["cell_function_detailed"] for r in rows)),
        "mapping_status_counts": dict(Counter(r["mapping_status"] for r in rows)),
        "proofread_counts": dict(Counter(r["proofread"] for r in rows)),
        "nerve_side_mismatches": 0, "incoming_graphs": graph_stats,
        "incoming_union_pairs": len(comparison), "incoming_pairs_both_versions": sum(r["present_both"] for r in comparison),
        "incoming_pairs_at_least_5_both": sum(r["at_least_5_both"] for r in comparison),
        "upstream_roots_union": len(upstream_ids), "upstream_metadata_rows": upstream.num_rows,
        "body_observation_schema": "fly.body-observation.v1", "calibrated_actuator_channels": 0,
        "limits": ["BANC is a different individual from FAFB; no direct FAFB motor IDs are inferred.", "Model leg assignment uses effector body part and side, not soma neuromere.", "Joint channels are proposals for comparing geometric observations, not executable muscle mappings.", "Angle signs, force gains, muscle dynamics and receptor encodings are uncalibrated.", "Detector agreement is robustness evidence, not independent biological validation.", "Missing v2/v3 edge counts are null; graphs must not be summed."]
    }
    assert upstream.num_rows == len(upstream_ids)
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    reference = {"schema": "fly.banc-leg-motor-reference.v1", "namespace": "BANC_v888", "motor_count": len(rows), "body_observation_schema": audit["body_observation_schema"], "enabled_for_control": False, "source": audit["dataset_doi"], "license": audit["license"], "mapping_status_counts": audit["mapping_status_counts"], "limits": audit["limits"], "motors": rows}
    (ROOT / "app/data/banc_leg_motor_reference.json").write_text(json.dumps(reference, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in audit.items() if k not in ("inputs", "limits")}, indent=2))


if __name__ == "__main__":
    main()
