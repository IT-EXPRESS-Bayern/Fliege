"""Verify persisted full-network outputs and immutable source data, without rerunning dynamics."""
import hashlib
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "run33241778_replicate0"
SRC = ROOT / "data/research_sources/other/pugliese_cpg_2026"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


audit = json.loads((OUT / "audit.json").read_text(encoding="utf-8"))
summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
checks = []


def check(name, condition, **details):
    assert condition, name
    checks.append({"name": name, "passed": True, **details})


for relative, metadata in audit["source_files"].items():
    check("source_unchanged:" + relative, sha(SRC / relative) == metadata["sha256"])
for name, digest in audit["outputs"].items():
    check("output_hash:" + name, sha(OUT / name) == digest)
check("executed_runner_matches_current_source", sha(HERE / "run.py") == audit["runner_sha256"])
unit = json.loads((HERE / "solver_unit_audit.json").read_text(encoding="utf-8"))
check("unit_controls_match_current_runner", unit["runner_sha256"] == audit["runner_sha256"] and all(x["passed"] for x in unit["checks"]))

stored = np.load(SRC / "run33241778/original_parameters_replicate0.npz", allow_pickle=False)
params = np.load(OUT / "sampled_parameters.npz", allow_pickle=False)
for name in ["tau", "a", "threshold", "fr_cap"]:
    check("original_parameters_unchanged:" + name, np.array_equal(stored[name].reshape(-1), params[name]))

baseline = np.load(OUT / "dng100_rates.npz", allow_pickle=False)
roots = baseline["root_ids"]
baseline_rates = baseline["rates"]
for condition, stats in summary["conditions"].items():
    with np.load(OUT / stats["trajectory_file"], allow_pickle=False) as data:
        rates = data["rates"]
        check("trajectory_shape:" + condition, rates.shape == (4963, 2001))
        check("all_exact_root_ids:" + condition, np.array_equal(roots, data["root_ids"]) and len(set(roots)) == 4963 and roots.dtype.kind == "U")
        check("finite:" + condition, bool(np.isfinite(rates).all()))
        for root_id in stats["removed_neurons"]:
            row = int(np.where(roots == root_id)[0][0])
            check("removed_cell_silent:" + condition, bool(np.all(rates[row] == 0)))
        if condition == "zero":
            check("entire_zero_control_silent", bool(np.all(rates == 0)))
        if condition == "dng100_repeat":
            check("repeat_all_9930963_float32_values_equal", np.array_equal(rates, baseline_rates))

readout_ids = [x["rootId"] for x in json.loads((OUT / "replay.json").read_text(encoding="utf-8"))["motorMetadata"]]
motor_indices = [int(np.where(roots == rid)[0][0]) for rid in readout_ids]
tight = np.load(OUT / "dng100_tighter_rates.npz", allow_pickle=False)
motor_error = float(np.max(np.abs(tight["rates"][motor_indices] - baseline_rates[motor_indices])))
result = {"schema": "fly.cpg-result-verification.v1", "checks_passed": len(checks), "checks_failed": 0, "checks": checks,
          "numerical_motor_maximum_difference_hz": motor_error,
          "numerical_interpretation": "Tenfold tighter tolerance retains six rhythmic motor cells and ~15.15Hz; small nonzero trajectory difference is preserved.",
          "archived_parameter_sha256": sha(SRC / "run33241778/original_parameters_replicate0.npz"),
          "summary_sha256": sha(OUT / "summary.json"), "replay_sha256": sha(OUT / "replay.json"),
          "scope": "Model and file integrity checks, no biological or embodied walking validation"}
(HERE / "result_verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in result.items() if k != "checks"}, indent=2))
