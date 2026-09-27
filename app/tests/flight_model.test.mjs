import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { buildFlightMotorPools, FlightModel, runFlightTrial, FLIGHT_PARAMETERS } from '../flight_model.mjs';
const mapping = JSON.parse(await readFile(new URL('../data/flight_control_mapping.json', import.meta.url)));
const pools = buildFlightMotorPools(mapping);
const run = (options = {}) => runFlightTrial({ mapping, recordEvery: 20, ...options });

test('24 exact asynchronous power roots and 2 b1 roots use effector nerve side, including crossed DLM5', () => {
  for (const side of ['left', 'right']) {
    assert.equal(pools[side].DLM.length, 5); assert.equal(pools[side].DVM.length, 7); assert.equal(pools[side].b1.length, 1);
  }
  assert.equal(pools.selected.length, 26);
  assert.ok(pools.selected.every((m) => m.proofread === true && m.eligibleForAnatomicalMotorPool === true && m.kinematicSign === null && m.forceGain === null));
  const crossed = pools.selected.filter((m) => m.cellType === 'DLM5' && m.sourceSide !== m.effectorSide);
  assert.equal(crossed.length, 2);
  for (const m of crossed) { assert.ok(pools[m.effectorSide].DLM.includes(m.id)); assert.ok(!pools[m.sourceSide].DLM.includes(m.id)); }
  assert.throws(() => buildFlightMotorPools({ ...mapping, namespace: 'FAFB' }), /BANC/);
});

test('anatomy conflicts are never recruited and transmitter predictions do not set muscle sign', () => {
  const copy = structuredClone(mapping); const id = pools.left.DLM[0];
  copy.motors.find((m) => m.id === id).eligibleForAnatomicalMotorPool = false;
  assert.ok(!buildFlightMotorPools(copy).left.DLM.includes(id));
  for (const m of copy.motors) m.ntPredicted = 'glutamate';
  const original = run(); const changed = runFlightTrial({ mapping: { ...mapping, motors: mapping.motors.map((m) => ({ ...m, ntPredicted: 'gaba' })) }, recordEvery: 20 });
  assert.deepEqual(original.summary, changed.summary);
});

test('passive mechanical energy decays; constant power can sustain oscillation without periodic inputs', () => {
  const passive = run({ condition: 'passive' }); const active = run();
  let previous = passive.frames[0].mechanics.oscillatorEnergy;
  for (const f of passive.frames) { assert.ok(f.mechanics.oscillatorEnergy <= previous + 1e-12); previous = f.mechanics.oscillatorEnergy; }
  assert.ok(passive.summary.finalStrokeRms < 1e-10); assert.equal(passive.summary.cumulativePowerWork, 0);
  assert.ok(active.summary.finalStrokeRms > .4); assert.ok(active.summary.wingFrequencyHz.left > 150 && active.summary.wingFrequencyHz.left < 250);
  assert.equal(active.provenance.prescribedPeriodicInput, false); assert.equal(active.provenance.neuralPropagationSimulated, false);
  const id = pools.left.DLM[0]; assert.ok(active.frames.slice(1).every((f) => f.neural.motorCommandsById[id] === .7));
});

test('both power groups are required by the declared model; switch-off eliminates sustained motion', () => {
  const ablation = run({ condition: 'power_pool_ablation' }); const off = run({ condition: 'power_off' });
  assert.ok(ablation.summary.finalStrokeRms < 1e-10); assert.equal(ablation.summary.cumulativePowerWork, 0);
  assert.ok(off.summary.finalStrokeRms < 1e-3); assert.equal(off.summary.wingFrequencyHz.left, null);
  const last = ablation.frames.at(-1);
  assert.ok(last.neural.powerActivation.left.DLM > .69); assert.equal(last.neural.powerActivation.left.DVM, 0);
});

test('an exactly unperturbed equilibrium stays zero even under power, with no hidden movement injection', () => {
  const t = run({ parameters: { initialPerturbation: 0 } });
  assert.equal(t.summary.finalStrokeRms, 0); assert.equal(t.summary.cumulativePowerWork, 0); assert.equal(t.summary.meanForceLeft, 0);
});

test('bilateral geometry and direct steering controls are mirror symmetric', () => {
  const symmetric = run(); const left = run({ condition: 'left_steering' }); const right = run({ condition: 'right_steering' });
  assert.equal(symmetric.summary.peakRollRadians, 0); assert.equal(symmetric.summary.meanForceLeft, symmetric.summary.meanForceRight);
  assert.equal(left.summary.finalRollRadians, -right.summary.finalRollRadians);
  assert.equal(left.summary.meanForceLeft, right.summary.meanForceRight);
  assert.ok(left.summary.finalRollRadians < -.1); assert.ok(right.summary.finalRollRadians > .1);
});

test('roll feedback and open-loop control receive exactly the same disturbance; wrong gain sign is retained', () => {
  const open = run({ condition: 'roll_open' }); const closed = run({ condition: 'roll_feedback' });
  const inverted = run({ condition: 'roll_feedback', parameters: { steeringPolarity: -1 } });
  assert.deepEqual(open.frames.map((f) => f.forces.externalRollTorque), closed.frames.map((f) => f.forces.externalRollTorque));
  assert.deepEqual(open.frames.map((f) => f.forces.externalRollTorque), inverted.frames.map((f) => f.forces.externalRollTorque));
  assert.ok(open.summary.peakSensorSignal > .1); assert.equal(open.summary.maxSteeringActivationDifference, 0);
  assert.ok(closed.summary.rmsRollRate < open.summary.rmsRollRate);
  assert.ok(inverted.summary.rmsRollRate > open.summary.rmsRollRate);
  assert.equal(closed.provenance.sensoryEdgesSimulated, false); assert.equal(closed.provenance.freeFlight, false);
});

test('haltere and pitch are dynamic responses to stroke; all recorded DOFs obey finite joint limits', () => {
  const t = run({ condition: 'left_steering' });
  assert.ok(t.frames.some((f) => Math.abs(f.flightKinematics.halteres.left) > .03));
  assert.ok(t.frames.some((f) => Math.abs(f.flightKinematics.wings.left.pitch) > .2));
  for (const f of t.frames) for (const side of ['left', 'right']) {
    const w = f.flightKinematics.wings[side];
    assert.ok(Number.isFinite(w.stroke) && w.stroke >= FLIGHT_PARAMETERS.strokeMin && w.stroke <= FLIGHT_PARAMETERS.strokeMax);
    assert.ok(Number.isFinite(w.pitch) && w.pitch >= FLIGHT_PARAMETERS.pitchMin && w.pitch <= FLIGHT_PARAMETERS.pitchMax);
    assert.ok(Math.abs(f.flightKinematics.halteres[side]) <= FLIGHT_PARAMETERS.haltereLimit);
    assert.equal(w.elevation, 0); assert.equal(f.world.translationEnabled, false);
    assert.equal(f.body.pose.roll, f.mechanics.rollAngle); assert.equal(f.body.contacts, 0);
  }
});

test('seeded runs reproduce exactly; half timestep preserves frequency and amplitude', () => {
  const first = run({ seed: 5 }); const again = run({ seed: 5 });
  assert.deepEqual(first.summary, again.summary);
  const finer = run({ seed: 5, parameters: { dt: .000025 }, recordEvery: 40 });
  assert.ok(Math.abs(first.summary.finalStrokeRms / finer.summary.finalStrokeRms - 1) < .01);
  assert.ok(Math.abs(first.summary.wingFrequencyHz.left / finer.summary.wingFrequencyHz.left - 1) < .005);
  assert.throws(() => new FlightModel({ mapping, parameters: { dt: .001 } }), /integration/);
});
