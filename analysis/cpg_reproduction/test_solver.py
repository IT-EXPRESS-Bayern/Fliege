"""Independent small-system controls for units, pulse segmentation and orientation."""
from pathlib import Path
import importlib.util
import json
import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("cpg_runner", HERE / "run.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

params = {"tau": np.array([0.02]), "a": np.array([1.0]), "threshold": np.array([7.5]), "fr_cap": np.array([200.0])}
cfg = {"excitatoryMultiplier": 0.03, "inhibitoryMultiplier": 0.03}
sim = {"T": 0.06, "dt": 0.001, "pulseStart": 0.02, "pulseEnd": 0.045, "rtol": 2e-6, "atol": 5e-9}
t, rates, numerical = runner.simulate(np.zeros((1, 1)), params, cfg, sim, np.array([50.0]), [])
activation = 200 * np.tanh((50 - 7.5) / 200)
expected = np.where(t <= 0.02, 0, activation * (1 - np.exp(-(np.minimum(t, 0.045) - 0.02) / 0.02)))
expected *= np.where(t > 0.045, np.exp(-(t - 0.045) / 0.02), 1)
error = float(np.max(np.abs(rates[0] - expected)))
assert error < 1e-4

# Raw W[pre,post] must excite the second cell from the first, never reverse it.
raw = np.array([[0.0, 10.0], [0.0, 0.0]])
p2 = {k: np.repeat(v, 2) for k, v in params.items()}
p2["threshold"][:] = 0
derivative = runner.rhs_port(raw.T * 0.03, p2, np.zeros(2))(0, np.array([5.0, 0.0]))
assert derivative[0] == -250 and derivative[1] > 0

# Masking the intermediate cell blocks transfer while leaving input external.
_, masked, _ = runner.simulate(raw, p2, cfg, sim, np.array([50.0, 0.0]), [1])
assert np.max(masked[1]) == 0 and np.max(masked[0]) > 0

audit = {"schema": "fly.cpg-solver-unit-controls.v1", "checks": [
    {"name": "isolated_cell_matches_analytic_pulse_response", "passed": True, "maximum_absolute_rate_error": error, "limit": 1e-4},
    {"name": "presynaptic_row_orientation", "passed": True, "derivative_fixture": derivative.tolist()},
    {"name": "row_column_removal_blocks_target_response", "passed": True},
], "scope": "Numerical implementation controls using synthetic small systems; no biological validation", "runner_sha256": runner.sha(HERE / "run.py")}
runner.save(HERE / "solver_unit_audit.json", audit)
print(json.dumps(audit, indent=2))
