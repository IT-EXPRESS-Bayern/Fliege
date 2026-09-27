"""Inventory exact BANC-v888 motor identities and audit transmitter annotations.

Run with analysis/.venv/Scripts/python.exe analysis/motor_output_atlas/build.py.
Source fields are retained verbatim; this does not generate neural or muscle edges.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import json
import pyarrow.feather as feather
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "data/research_sources/other/banc_2026/banc_888_meta.feather"
FIELDS = ["banc_888_id", "super_class", "cell_class", "cell_type", "side", "nerve",
          "body_part_effector", "peripheral_target_type", "cell_function", "cell_function_detailed",
          "neurotransmitter_predicted", "neurotransmitter_score", "neurotransmitter_verified",
          "proofread", "fafb_match", "fafb_cell_type", "neuromere"]


def write_csv(name, rows):
    with (OUT / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    prior = json.loads((ROOT / "analysis/body_neural_interface/audit.json").read_text())
    assert source_sha == prior["inputs"][SOURCE.name]["sha256"]
    source_rows = feather.read_table(SOURCE, columns=FIELDS).to_pylist()
    motors = sorted((r for r in source_rows if r["super_class"] == "motor"), key=lambda r: r["banc_888_id"])
    assert len(motors) == len({r["banc_888_id"] for r in motors}) == 805
    assert all(isinstance(r["banc_888_id"], str) and r["banc_888_id"].isdigit() for r in motors)
    assert all(r["proofread"] == "TRUE" for r in motors)
    verified = [r for r in motors if r["neurotransmitter_verified"]]
    conflicts = [r for r in verified if r["neurotransmitter_predicted"] != r["neurotransmitter_verified"]]
    leg_rows = [r for r in motors if r["body_part_effector"] in ("front_leg", "middle_leg", "hind_leg")]
    assert len(leg_rows) == 391
    groups = []
    for target, count in Counter(r["body_part_effector"] for r in motors).most_common():
        rows = [r for r in motors if r["body_part_effector"] == target]
        groups.append({"body_part_effector": target, "motor_roots": count,
                       "detailed_action_present": sum(bool(r["cell_function_detailed"]) for r in rows),
                       "verified_transmitter_present": sum(bool(r["neurotransmitter_verified"]) for r in rows),
                       "predicted_verified_disagreements": sum(r in conflicts for r in rows)})
    assert sum(r["motor_roots"] for r in groups) == 805
    assert len(verified) == 30 and len(conflicts) == 28
    assert not any(r["neurotransmitter_verified"] for r in leg_rows)
    write_csv("banc_motor_neurons_805.csv", motors)
    pq.write_table(pa.Table.from_pylist(motors), OUT / "banc_motor_neurons_805.parquet", compression="zstd")
    write_csv("body_part_summary.csv", groups)
    write_csv("predicted_verified_transmitter_conflicts.csv", conflicts)
    audit = {
        "schema": "fly.motor-output-atlas.v1", "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": str(SOURCE.relative_to(ROOT)).replace("\\", "/"), "source_sha256": source_sha,
        "source_url": "https://doi.org/10.7910/DVN/7WTH1N", "license": "CC BY 4.0",
        "namespace": "BANC_v888", "motor_roots": len(motors), "all_unique_exact_ids": True,
        "all_proofread": True, "leg_motor_roots": len(leg_rows), "body_part_groups": groups,
        "predicted_transmitter_counts": dict(Counter(r["neurotransmitter_predicted"] or "missing" for r in motors)),
        "source_verified_transmitter_roots": len(verified),
        "verified_body_parts": dict(Counter(r["body_part_effector"] for r in verified)),
        "predicted_verified_disagreements": len(conflicts),
        "leg_verified_transmitter_roots": 0,
        "leg_predicted_transmitter_counts": dict(Counter(r["neurotransmitter_predicted"] or "missing" for r in leg_rows)),
        "interpretation": [
            "The verified field is the source annotation, not an independent experiment performed here.",
            "28/30 disagreement applies only to the annotated subset (neck and haltere); it is not a graph-wide classifier error estimate.",
            "Proofread identity does not validate predicted neurotransmitter, receptor response, muscle strength or motor dynamics.",
            "A transmitter label alone cannot set the sign of a neuron-to-muscle actuator.",
            "BANC is a different individual from FAFB; fafb_match remains a cross-animal homology field.",
            "Body-part groups use complete literal source labels, including antenna, scape; no multiple counting.",
            "Detailed-action presence is literal non-missingness, not evidence that an action is sufficiently specified for control."
        ]
    }
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: audit[k] for k in ("motor_roots", "leg_motor_roots", "source_verified_transmitter_roots", "predicted_verified_disagreements")}, indent=2))


if __name__ == "__main__":
    main()
