"""Auditable CPU port of the pinned Pugliese rate equations, never a paper-run claim.

All scientific inputs must already be downloaded. This runner has no network code.
Uses original JAX sampling/scoring, with a sparse SciPy Dormand-Prince CPU solver.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import time

# Keep CPU memory use bounded. These are implementation choices, not model gains.
os.environ.setdefault("JAX_PLATFORMS", "cpu")
os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "data/research_sources/other/pugliese_cpg_2026"
PIN = "10e7661bf414ba7b4c2edf795cd36d0f878c17c0"
EXPECTED = {
    "W_20260217.npz": "83197529fa336b5f9ce400cf689f299fa3e8f6f5379947ae7df5ec004869141f",
    "wTable_20260217_fullData_consistentColumns.csv": "6f87bf62227e160754523418bfbac35fc8971a90e4ed54574bf769b08332e285",
    "configs/neuron_params/default.yaml": "b63a37b84e056035d638bb8a36baf53e199d37feb4ddca9d044af3c521247298",
    "configs/sim/default.yaml": "29ed6f0d860276a1ff5136cf798b31997f8ec388dabf5a268ef566ae25c1b02a",
    "src/utils/sim_utils.py": "c8f58e2d77c50325d785c6d707ddba6608e774cbfd10203ed3488ea3320b6653",
    "src/simulation/vnc_sim.py": "58518185d43cd1a723f4ad1278753bc6e54fc5c086575206e82e493e9d960a5c",
}
CELLS = {
    "DNg100_target_left": (1605, "720575941500851362", "DNg100"),
    "DNg100_target_right": (4284, "720575941626500746", "DNg100"),
    "E1": (1689, "720575941504247575", "IN17A001"),
    "E2": (910, "720575941469024064", "INXXX466"),
    "I2": (3334, "720575941569601650", "IN19A007"),
    "I1": (2708, "720575941544954556", "IN16B036"),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def clean(value):
    return None if pd.isna(value) else str(value)


def load_original_utils():
    p = SOURCE / "src/utils/sim_utils.py"
    spec = importlib.util.spec_from_file_location("pugliese_original_sim_utils", p)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit_inputs():
    checks = []
    files = {}
    for name, expected in EXPECTED.items():
        p = SOURCE / name
        actual = sha(p)
        assert actual == expected, f"Source hash changed: {name}"
        files[name] = {"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": actual, "bytes": p.stat().st_size}
        checks.append({"name": "sha256:" + name, "pass": True})
    for name in ["src/utils/sim_utils.py", "src/simulation/vnc_sim.py"]:
        p = SOURCE / name
        if p.exists():
            files[name] = {"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(p), "bytes": p.stat().st_size}
    b = (SOURCE / "W_20260217.npz").read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()
    assert blob == "5b7f6392cd8029786f92b663cfee3a19fba16097"
    archive = np.load(SOURCE / "W_20260217.npz", allow_pickle=False)
    assert archive.files == ["arr_0"]
    W = archive["arr_0"]
    t = pd.read_csv(SOURCE / "wTable_20260217_fullData_consistentColumns.csv", index_col=0, dtype={"pt_root_id": str})
    assert W.shape == (4963, 4963) and len(t) == 4963
    assert np.array_equal(t.index, np.arange(len(t))) and t.pt_root_id.is_unique
    assert np.isfinite(W).all() and np.equal(W, np.rint(W)).all()
    assert not np.any((W.min(axis=1) < 0) & (W.max(axis=1) > 0))
    original_table_path = SOURCE / "wTable_20260217_fullData.csv"
    table_comparison = {"status": "original_run_table_not_locally_available"}
    if original_table_path.exists():
        original_table = pd.read_csv(original_table_path, index_col=0, dtype={"pt_root_id": str})
        comparable = [c for c in original_table.columns if c in t.columns]
        unequal = [c for c in comparable if not original_table[c].equals(t[c])]
        assert len(original_table) == len(t) and np.array_equal(original_table.index, t.index)
        assert not unequal, f"Original run table differs in shared columns: {unequal}"
        table_comparison = {"status": "all_shared_columns_exactly_equal", "original_sha256": sha(original_table_path), "shared_columns": len(comparable), "additional_consistent_columns": [c for c in t.columns if c not in original_table.columns], "rows": len(t)}
        files[original_table_path.name] = {"path": str(original_table_path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(original_table_path), "bytes": original_table_path.stat().st_size}
    exact_cells = {}
    for label, (i, root_id, cell_type) in CELLS.items():
        row = t.loc[i]
        assert row.pt_root_id == root_id and row.cell_type == cell_type
        exact_cells[label] = {"index": i, "rootId": root_id, "cellType": cell_type, "somaSide": clean(row.side)}
        checks.append({"name": "exact_identity:" + label, "pass": True})
    effective_nt = t.neurotransmitter_verified.fillna(t.neurotransmitter_predicted)
    expected_sign = np.where(effective_nt == "acetylcholine", 1, np.where(effective_nt.isin(["gaba", "glutamate"]), -1, 0))
    observed_sign = np.sign(W.sum(axis=1))
    evaluable = (observed_sign != 0) & (expected_sign != 0)
    mismatches = evaluable & (observed_sign != expected_sign)
    assert not mismatches.any(), "Canonical verified-first NT disagrees with stored W"
    checks.append({"name": "verified_first_canonical_nt_matches_stored_signs", "pass": True, "rows": int(evaluable.sum())})
    module_mask = t["motor module"].notna().to_numpy()
    strict_motor_mask = module_mask & t.super_class.eq("motor").to_numpy()
    conflicts = t.loc[module_mask & ~strict_motor_mask].copy()
    # Preserve source module labels, but never treat nonmotor rows as body actuators.
    audit = {
        "schema": "fly.cpg-input-audit.v1", "repository_commit": PIN, "source_files": files,
        "matrix_git_blob_sha1": blob, "n_neurons": len(t), "positive_edges": int(np.count_nonzero(W > 0)),
        "original_run_table_comparison": table_comparison,
        "negative_edges": int(np.count_nonzero(W < 0)), "matrix_orientation": "stored rows=presynaptic; columns=postsynaptic; ODE uses W.T",
        "matrix_signs": "Preserved from original signed matrix. Canonical ACh/GABA/Glu agree with verified-first source NT; no new NT inference.",
        "exact_cells": exact_cells, "original_notebook_module_mask_count": int(module_mask.sum()),
        "conservative_motor_module_count": int(strict_motor_mask.sum()), "module_annotation_conflicts": len(conflicts),
        "size_missing_count": int(t.surf_area_um2.isna().sum()),
        "size_zero_count": int(t.surf_area_um2.eq(0).sum()), "size_median_um2": float(t.surf_area_um2.median()),
        "core_motif_signed_counts": [{"preRole": pre, "preRootId": value[1], "postRole": post, "postRootId": target[1], "signedCount": float(W[value[0], target[0]])} for pre, value in CELLS.items() if pre != "DNg100_target_right" for post, target in CELLS.items() if post != "DNg100_target_right" and W[value[0], target[0]] != 0],
        "checks": checks,
    }
    return W, t, module_mask, strict_motor_mask, conflicts, audit


def sample_parameters(original, cfg, table, seed):
    # Exact original random-key splitting and truncated-normal sampler; only one
    # local replicate. Shape (1,N) is NOT the published 1024-replicate random array.
    keys = jax.random.split(jax.random.PRNGKey(seed), 5)
    result = {}
    for k, name, prefix in [(0, "tau", "tau"), (1, "a", "a"), (2, "threshold", "threshold"), (3, "fr_cap", "frcap")]:
        result[name] = original.sample_trunc_normal(keys[k], cfg[prefix + "Mean"], cfg[prefix + "Stdv"], (1, len(table)))
    result["a"], result["threshold"] = original.set_sizes(table.surf_area_um2.to_numpy(), result["a"], result["threshold"])
    return {k: np.asarray(v[0], dtype=np.float32) for k, v in result.items()}


def rhs_port(weights, params, current):
    tau, a, theta, cap = [np.asarray(params[k], dtype=np.float64) for k in ["tau", "a", "threshold", "fr_cap"]]

    def derivative(_time, rates):
        drive = current + weights @ rates
        activation = np.maximum(cap * np.tanh((a / cap) * (drive - theta)), 0)
        return (activation - rates) / tau

    return derivative


def compare_original_rhs(W, params, cfg, input_amplitude):
    path = SOURCE / "src/simulation/vnc_sim.py"
    if not path.exists():
        return {"status": "not_run_source_file_missing"}
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ["rate_equation_half_tanh", "reweight_connectivity"]]
    assert len(functions) == 2
    # Execute precisely the two original function definitions, not a handwritten
    # imitation, without importing HPC/memory/orchestrator dependencies.
    namespace = {"jit": jax.jit, "jnp": jnp}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), "exec"), namespace)
    scale_exc = cfg["excitatoryMultiplier"]
    scale_inh = cfg["inhibitoryMultiplier"]
    original_weight = namespace["reweight_connectivity"](jnp.asarray(W, dtype=jnp.float32), scale_exc, scale_inh)
    sparse_weight = csr_matrix(np.where(W.T > 0, np.float32(scale_exc) * W.T, np.float32(scale_inh) * W.T))
    rates = np.random.default_rng(8128).uniform(0, 0.5, len(W)).astype(np.float32)
    current = np.zeros(len(W), np.float32)
    current[1605] = input_amplitude
    par = [jnp.asarray(params[k]) for k in ["tau", "threshold", "a", "fr_cap"]]
    args = (jnp.asarray(current), 0.02, 1.999, par[0], original_weight, par[1], par[2], par[3], jax.random.PRNGKey(1), 0.0)
    expected = np.asarray(namespace["rate_equation_half_tanh"](0.5, jnp.asarray(rates), args))
    actual = rhs_port(sparse_weight, params, current)(0.5, rates)
    error = np.abs(actual - expected)
    relative = error / np.maximum(1, np.abs(expected))
    ok = bool(np.allclose(actual, expected, rtol=1e-4, atol=0.005))
    assert ok, "Sparse CPU equation disagrees with original JAX RHS"
    return {"status": "passed", "max_abs_derivative_error": float(error.max()), "max_relative_error_denominator_floor1": float(relative.max()), "tolerance_rtol": 1e-4, "tolerance_atol": 0.005, "original_dtype": "float32", "port_dtype": "float64", "time_point_seconds": 0.5, "input_amplitude": input_amplitude}


def simulate(W, params, cfg, sim_cfg, current, removed, rtol_scale=1):
    from scipy.sparse import csr_matrix
    from scipy.integrate import solve_ivp
    # Original removeNeurons removes both rows and columns. Keep the source intact.
    weights = csr_matrix(np.where(W.T > 0, np.float32(cfg["excitatoryMultiplier"]) * W.T, np.float32(cfg["inhibitoryMultiplier"]) * W.T))
    if removed:
        mask = np.ones(W.shape[0])
        mask[removed] = 0
        weights = weights.multiply(mask[:, None]).multiply(mask[None, :]).tocsr()
    duration = float(sim_cfg["T"])
    dt = float(sim_cfg["dt"])
    start = float(sim_cfg["pulseStart"])
    end = float(sim_cfg["pulseEnd"])
    times = np.arange(round(duration / dt) + 1, dtype=np.float64) * dt
    boundaries = sorted(set([0.0, duration] + [x for x in [start, end] if 0 < x < duration]))
    rates = np.zeros((len(W), len(times)), dtype=np.float64)
    state = np.zeros(len(W), dtype=np.float64)
    nfev = 0
    wall_start = time.perf_counter()
    for left, right in zip(boundaries[:-1], boundaries[1:]):
        midpoint = (left + right) / 2
        active_current = current if start <= midpoint <= end else np.zeros_like(current)
        result = solve_ivp(rhs_port(weights, params, active_current), (left, right), state,
                           method="RK45", rtol=float(sim_cfg["rtol"]) * rtol_scale,
                           atol=float(sim_cfg["atol"]) * rtol_scale, first_step=min(dt, right-left), dense_output=True)
        assert result.success and np.isfinite(result.y).all(), result.message
        use = (times >= left) & (times <= right)
        rates[:, use] = result.sol(times[use])
        state = result.y[:, -1]
        nfev += result.nfev
    assert np.isfinite(rates).all(), "Nonfinite values are failure, never replaced by zero"
    return times, rates, {"function_evaluations": nfev, "wall_seconds": time.perf_counter() - wall_start,
                          "minimum_rate": float(rates.min()), "maximum_rate": float(rates.max()),
                          "finite": True, "clip_or_nonfinite_replacement_applied": False}


def summarize(original, rates, times, table, module_mask, strict_mask):
    # This is the original notebook's 250 ms transient exclusion at 1 ms samples.
    use = times >= 0.250 - 1e-10
    indices = np.where(module_mask)[0]
    traces = rates[indices][:, use].astype(np.float32)
    scores, frequency_per_sample = jax.vmap(original.neuron_oscillation_score)(jnp.asarray(traces))
    scores = np.asarray(scores)
    frequencies = np.asarray(frequency_per_sample) / (times[1] - times[0])
    active = np.max(traces, axis=1) > 0.01
    conservative = strict_mask[indices]
    rhythmic = active & conservative & (scores > 0.5)
    result = {
        "active_neurons_any_time": int(np.sum(np.max(rates, axis=1) > 0.01)),
        "original_module_mask": {"total": len(indices), "active_post_transient": int(active.sum()), "mean_rhythmicity": float(scores[active].mean()) if active.any() else 0.0},
        "conservative_motor_mask": {"total": int(conservative.sum()), "active_post_transient": int((active & conservative).sum()), "mean_rhythmicity": float(scores[active & conservative].mean()) if (active & conservative).any() else 0.0, "rhythmic_cells_score_above_0_5": int(rhythmic.sum()), "median_autocorrelation_frequency_hz_for_rhythmic_cells": float(np.median(frequencies[rhythmic])) if rhythmic.any() else None},
        "readouts": {},
    }
    for label, (idx, root_id, cell_type) in CELLS.items():
        trace = rates[idx, use]
        peaks, _ = find_peaks(trace, prominence=max(0.01, float(np.ptp(trace)) * 0.05))
        periods = np.diff(times[use][peaks])
        result["readouts"][label] = {"rootId": root_id, "cellType": cell_type, "maxRate": float(trace.max()), "meanRate": float(trace.mean()), "amplitude": float(np.ptp(trace)), "peaks": len(peaks), "meanInterpeakHz": float(1 / periods.mean()) if len(periods) else None}
    rows = []
    for pos, idx in enumerate(indices):
        trace = rates[idx, use]
        rows.append({"index": int(idx), "root_id": table.loc[idx, "pt_root_id"], "cell_type": clean(table.loc[idx, "cell_type"]), "side": clean(table.loc[idx, "side"]), "module": clean(table.loc[idx, "motor module"]), "conservative_motor": bool(strict_mask[idx]), "active_post_transient": bool(active[pos]), "max_rate": float(trace.max()), "mean_rate": float(trace.mean()), "amplitude": float(np.ptp(trace)), "original_rhythmicity_score": float(scores[pos]), "original_autocorrelation_frequency_hz": float(frequencies[pos])})
    return result, rows


def main():
    global scipy, solve_ivp, csr_matrix, find_peaks, yaml, jax, jnp
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-amplitude", type=float, required=True, help="Explicit arbitrary-unit constant current; never silently infer paper amplitude")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--label", default="repo_defaults_seed1")
    ap.add_argument("--run-config", type=Path, help="Optional real source run config; table and matrix still strictly pinned to this task")
    ap.add_argument("--parameter-file", type=Path, help="Original archived replicate slice; tau/a/threshold/fr_cap already size-scaled, never rescale")
    ap.add_argument("--conditions", default="zero,dng100,e1_removed,e2_removed,i2_removed,dnb08_pair,dng100_repeat,dng100_tighter")
    ap.add_argument("--audit-only", action="store_true", help="Verify scientific files with NumPy/Pandas only, without simulation")
    args = ap.parse_args()
    out = HERE / args.label
    out.mkdir(parents=True, exist_ok=True)
    W, table, module_mask, strict_mask, conflicts, audit = audit_inputs()
    conflicts.to_csv(out / "original_module_annotation_conflicts.csv", index_label="matrix_index")
    if args.audit_only:
        save(out / "input_audit.json", audit)
        print(json.dumps({k: v for k, v in audit.items() if k not in ["source_files", "checks", "exact_cells"]}, indent=2))
        return
    import scipy
    from scipy.integrate import solve_ivp
    from scipy.sparse import csr_matrix
    from scipy.signal import find_peaks
    import yaml
    import jax
    import jax.numpy as jnp
    jax.config.update("jax_enable_x64", False)
    original = load_original_utils()
    cfg = yaml.safe_load((SOURCE / "configs/neuron_params/default.yaml").read_text())
    sim_cfg = yaml.safe_load((SOURCE / "configs/sim/default.yaml").read_text())
    run_config_status = "missing; using pinned repository defaults and explicit local protocol"
    input_source = "Explicit CLI choice. 250 is present in pinned MANC DNg100_Stim example, not verified as BANC paper-run current."
    if args.run_config:
        run_cfg = yaml.safe_load(args.run_config.read_text())
        cfg.update(run_cfg["neuron_params"])
        sim_cfg.update(run_cfg["sim"])
        run_config_status = {"path": str(args.run_config), "sha256": sha(args.run_config), "status": "configuration applied; independent one-replicate sampling and current original table, not exact stored paper replicate", "experiment": run_cfg.get("experiment")}
        configured_stimulus = run_cfg.get("experiment", {}).get("stimI")
        input_source = f"Explicit CLI current {args.input_amplitude:g}; actual source run_config experiment.stimI={configured_stimulus!r}. Compare before claiming matching drive."
    assert not sim_cfg.get("shuffle") and not sim_cfg.get("noise")
    assert not sim_cfg.get("prune_network"), "Iterative network pruning is outside this frozen protocol"
    if cfg.get("glutamateMultiplier") is not None:
        # Same optional preprocessing as original prepare_neuron_params: source
        # predictedNt selects glutamate rows before subsequent inhibitory scaling.
        assert cfg["inhibitoryMultiplier"] != 0
        ratio = cfg["glutamateMultiplier"] / cfg["inhibitoryMultiplier"]
        W = W.copy()
        W[table.predictedNt.eq("glutamate").to_numpy()] *= ratio
        audit["optional_glutamate_preprocessing"] = {"configured_multiplier": cfg["glutamateMultiplier"], "row_scale_before_reweighting": ratio, "selector": "source predictedNt == glutamate, as original code"}
    assert float(sim_cfg["dt"]) == 0.001, "Transient convention must be reviewed if output sampling changes"
    sampling_description = "Original JAX PRNG split and original truncated sampler, shape (1,4963). Same arrays in every condition."
    if args.parameter_file:
        with np.load(args.parameter_file, allow_pickle=False) as stored:
            params = {k: np.asarray(stored[k]).reshape(-1).copy() for k in ["tau", "a", "threshold", "fr_cap"]}
            for k, values in params.items():
                assert values.shape == (len(W),) and np.isfinite(values).all() and (values >= 0).all(), k
            assert (params["tau"] > 0).all() and (params["fr_cap"] > 0).all()
            input_key = "inputs" if "inputs" in stored else "input_currents" if "input_currents" in stored else None
            if input_key:
                reference_input = np.asarray(stored[input_key]).reshape(-1)
                assert reference_input.shape == (len(W),)
                assert np.flatnonzero(reference_input).tolist() == [1605]
                assert reference_input[1605] == args.input_amplitude
        sampling_description = "Original archived replicate slice, already size-scaled; no random resampling or second size correction. Same arrays in every condition."
        audit["archived_parameters"] = {"path": str(args.parameter_file), "sha256": sha(args.parameter_file), "keys_used": list(params), "second_size_correction_applied": False, "source_input_nonzero_index": 1605 if input_key else None, "source_input_matches_requested_amplitude": True if input_key else None}
        if isinstance(run_config_status, dict):
            run_config_status["status"] = "Actual run configuration plus archived parameters; sparse CPU equation recomputation, not equality to the original saved trajectory"
    else:
        params = sample_parameters(original, cfg, table, args.seed)
    np.savez_compressed(out / "sampled_parameters.npz", **params)
    audit["original_rhs_comparison"] = compare_original_rhs(W, params, cfg, args.input_amplitude)
    test_time = jnp.arange(1751, dtype=jnp.float32) * 0.001
    sine_score, sine_frequency = original.neuron_oscillation_score(jnp.sin(2 * jnp.pi * 12 * test_time))
    zero_score, zero_frequency = original.neuron_oscillation_score(jnp.zeros(1751))
    assert float(sine_score) > 0.99 and abs(float(sine_frequency) / 0.001 - 12) < 0.1
    assert float(zero_score) == 0 and float(zero_frequency) == 0
    audit["rhythmicity_unit_controls"] = {"sine_input_hz": 12, "sine_score": float(sine_score), "sine_estimated_hz": float(sine_frequency) / 0.001, "zero_score": float(zero_score), "passed": True}
    dn = CELLS["DNg100_target_left"][0]
    # These two DNb08 somas are on the right; do not call them target-left
    # without an independent axon-side audit. This is a cell-identity control.
    dnb_indices = table.index[(table.cell_type == "DNb08") & (table.side == "right")].tolist()
    assert dnb_indices == [208, 2722]
    scenarios = {
        "zero": {"stim": [], "removed": []},
        "dng100": {"stim": [dn], "removed": []},
        "e1_removed": {"stim": [dn], "removed": [1689]},
        "e2_removed": {"stim": [dn], "removed": [910]},
        "i2_removed": {"stim": [dn], "removed": [3334]},
        "dnb08_pair": {"stim": dnb_indices, "removed": []},
        "dng100_repeat": {"stim": [dn], "removed": []},
        "dng100_tighter": {"stim": [dn], "removed": [], "rtol_scale": 0.1},
    }
    order = args.conditions.split(",")
    assert all(x in scenarios for x in order)
    protocol = {
        "schema": "fly.cpg-reproduction-protocol.v1", "paper_run_replicated": False,
        "original_repository_commit": PIN, "run_config_status": run_config_status,
        "input_amplitude_each_cell_arbitrary_units": args.input_amplitude,
        "input_amplitude_source": input_source,
        "seed": args.seed, "replicates": 1, "parameter_sampling": sampling_description,
        "neuron_params": cfg, "sim_params": sim_cfg,
        "solver": "SciPy RK45 Dormand-Prince with sparse transposed signed matrix, float64 states, original float32 sampled parameters",
        "differences_from_original_runner": ["SciPy RK45 adaptive step controller instead of Diffrax Dopri5", "float64 state arithmetic instead of original float32", "Exact integration segment boundaries at pulse onset and offset", "NPZ arr_0 loaded explicitly; original load_W supports only NPY and CSV", "No NaN replacement or clipping: solver failure is explicit", "One replicate only; exact archived trace comparison not performed" if args.parameter_file else "One new replicate, no paper stored random parameter arrays"],
        "readout_masks": {"original_notebook": "motor module is non-null; 156 rows including 27 nonmotor or unclassified rows", "conservative": "motor module non-null AND source super_class=motor; 129 rows"},
        "conditions": {k: scenarios[k] for k in order},
        "claim_limit": "Conditioned VNC rate-model dynamics; not spontaneous motivation, autonomous navigation, spikes, a whole brain or biological validation.",
    }
    save(out / "protocol.json", protocol)
    save(out / "input_audit.json", audit)
    results = {}
    replay_conditions = []
    all_motor_rows = []
    baseline_rates = None
    for name in order:
        scenario = scenarios[name]
        print("Running", name, flush=True)
        current = np.zeros(len(W))
        current[scenario["stim"]] = args.input_amplitude
        times, rates, numerical = simulate(W, params, cfg, sim_cfg, current, scenario["removed"], scenario.get("rtol_scale", 1))
        stats, motor_rows = summarize(original, rates, times, table, module_mask, strict_mask)
        for row in motor_rows:
            row["condition"] = name
        all_motor_rows.extend(motor_rows)
        stats["numerical"] = numerical
        stats["source_neurons"] = [str(table.loc[i, "pt_root_id"]) for i in scenario["stim"]]
        stats["removed_neurons"] = [str(table.loc[i, "pt_root_id"]) for i in scenario["removed"]]
        path = out / f"{name}_rates.npz"
        np.savez_compressed(path, time_seconds=times, rates=rates.astype(np.float32), root_ids=table.pt_root_id.to_numpy(dtype="U18"))
        stats["trajectory_file"] = path.name
        stats["trajectory_sha256"] = sha(path)
        stats["rates_raw_float64_sha256"] = hashlib.sha256(rates.tobytes()).hexdigest()
        if name == "zero":
            assert np.max(np.abs(rates)) == 0
        if scenario["removed"]:
            assert np.max(np.abs(rates[scenario["removed"]])) == 0
        if name == "dng100":
            baseline_rates = rates.copy()
        if name == "dng100_repeat" and baseline_rates is not None:
            stats["exact_repeat_equal"] = bool(np.array_equal(rates, baseline_rates))
            assert stats["exact_repeat_equal"]
        if name == "dng100_tighter" and baseline_rates is not None:
            delta = np.abs(rates - baseline_rates)
            stats["tolerance_comparison"] = {"max_absolute_rate_difference": float(delta.max()), "rms_rate_difference": float(np.sqrt(np.mean(delta**2))), "interpretation": "Numerical sensitivity, not biological variability"}
        chosen_indices = list(dict.fromkeys([x[0] for x in CELLS.values()] + list(np.where(strict_mask)[0])))
        stride = 2
        replay_conditions.append({"id": name, "timeSeconds": times[::stride].tolist(), "ratesByRootId": {str(table.loc[i, "pt_root_id"]): rates[i, ::stride].round(6).tolist() for i in chosen_indices}, "summary": stats})
        results[name] = stats
        save(out / "summary.json", {"schema": "fly.cpg-summary.v1", "protocol": protocol, "conditions": results})
        print(name, json.dumps(stats["conservative_motor_mask"]), "wall", round(numerical["wall_seconds"], 2), flush=True)
    pd.DataFrame(all_motor_rows).to_csv(out / "motor_readout_statistics.csv", index=False)
    motor_metadata = [{"rootId": str(table.loc[i, "pt_root_id"]), "matrixIndex": int(i), "cellType": clean(table.loc[i, "cell_type"]), "somaSide": clean(table.loc[i, "side"]), "motorModule": clean(table.loc[i, "motor module"]), "bodyPartEffector": clean(table.loc[i, "body_part_effector"]), "peripheralTargetType": clean(table.loc[i, "peripheral_target_type"]), "stepContribution": clean(table.loc[i, "step contribution"]), "sourceSuperClass": "motor"} for i in np.where(strict_mask)[0]]
    save(out / "replay.json", {"schema": "fly.cpg-rate-replay.v1", "rateUnits": "Hz (abstract continuous rate, no simulated spikes)", "timeUnits": "seconds", "noPeriodicDrive": True, "requiresTonicInput": True, "paperRunReplicated": False, "motorMetadata": motor_metadata, "readouts": audit["exact_cells"], "conditions": replay_conditions, "protocolPath": str((out / "protocol.json").relative_to(ROOT)).replace("\\", "/"), "limitations": [protocol["claim_limit"], "Only front-leg subnetwork; no all-six-leg whole-body controller", "Body gain/force must be separately calibrated; neural rates are not muscle force", "27 invalid or unclassified original module rows excluded from body outputs"]})
    audit["completed_conditions"] = list(results)
    audit["runtime_versions"] = {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__, "jax": jax.__version__, "platform": platform.platform()}
    audit["runner_sha256"] = sha(__file__)
    audit["outputs"] = {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name != "audit.json"}
    save(out / "audit.json", audit)
    print("Completed", out, flush=True)


if __name__ == "__main__":
    main()
