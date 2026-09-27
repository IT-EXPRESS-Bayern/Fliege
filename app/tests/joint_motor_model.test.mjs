import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { LEG_SPECS } from '../body-kinematics.mjs';
import { makeMotorPools, poolActivation, JointMotorBody, motorTrial, MOTOR_PARAMETERS } from '../joint_motor_model.mjs';
const motors = JSON.parse(await readFile(new URL('../data/banc_leg_motor_reference.json', import.meta.url))).motors;
const pools = makeMotorPools(motors);
const distance = (a, b) => Math.hypot(...a.map((v, i) => v - b[i]));

test('exact source functions map 113 unique motor IDs to six antagonistic leg pools', () => {
  assert.equal(Object.values(pools).flatMap((p) => [...p.flexor, ...p.extensor]).length, 113);
  assert.equal(Object.values(pools).reduce((n, p) => n + p.flexor.length, 0), 101);
  assert.equal(Object.values(pools).reduce((n, p) => n + p.extensor.length, 0), 12);
  assert.ok(Object.values(pools).every((p) => p.flexor.length > 0 && p.extensor.length === 2));
});
test('duplicate pools do not double count; conflicting source assignments fail closed', () => {
  assert.deepEqual(makeMotorPools([...motors, ...motors]), pools);
  const chosen = motors.find((m) => m.cell_function_detailed === 'flex_femur_tibia_joint');
  assert.throws(() => makeMotorPools([...motors, { ...chosen, cell_function_detailed: 'extend_femur_tibia_joint' }]), /Conflicting/);
  assert.equal(poolActivation(['a', 'a', 'b'], { a: 1, b: 1 }), 1);
  assert.equal(poolActivation(['a', 'b'], { a: 1, b: 1 }, new Set(['a'])), .5);
});
test('null input is exactly stationary and no decorative gait/contact signal is injected', () => {
  const trial = motorTrial(pools, { condition: 'baseline' });
  assert.equal(trial.peakDeviationRadians, 0); assert.equal(trial.cumulativeAngleTravelRadians, 0);
  assert.equal(trial.neuralPropagationSimulated, false);
  assert.ok(trial.frames.every((f) => f.body.contacts === 0 && f.body.gaitFrequencyHz === 0));
});
test('flexor and extensor act oppositely on each of six identified legs', () => {
  for (const spec of LEG_SPECS) {
    const flex = motorTrial(pools, { leg: spec.id, condition: 'flexor' });
    const extend = motorTrial(pools, { leg: spec.id, condition: 'extensor' });
    const index = LEG_SPECS.indexOf(spec); const initial = flex.frames[0].body.legs[index].jointAngles.femurTibia;
    const at = (trial) => trial.frames.find((f) => f.tMs >= 1800).body.legs[index].jointAngles.femurTibia;
    assert.ok(at(flex) > initial + .2); assert.ok(at(extend) < initial - .2);
    for (const [i] of LEG_SPECS.entries()) if (i !== index) assert.equal(flex.frames.at(-1).body.legs[i].jointAngles.femurTibia, flex.frames[0].body.legs[i].jointAngles.femurTibia);
  }
});
test('true ablation removes movement; sham preserves direct flexor trial', () => {
  const flex = motorTrial(pools); const ablation = motorTrial(pools, { condition: 'ablation' }); const sham = motorTrial(pools, { condition: 'sham' });
  assert.equal(ablation.peakDeviationRadians, 0); assert.equal(sham.peakDeviationRadians, flex.peakDeviationRadians);
  assert.ok(sham.ablatedIds.every((id) => !sham.directlyDrivenIds.includes(id)));
});
test('one exact motor ID produces a smaller response; ablating that ID removes it', () => {
  const id = pools.LF.flexor[0]; const one = motorTrial(pools, { selection: id }); const all = motorTrial(pools);
  const ablated = motorTrial(pools, { selection: id, condition: 'ablation' });
  assert.deepEqual(one.directlyDrivenIds, [id]); assert.ok(one.peakDeviationRadians > 0 && one.peakDeviationRadians < all.peakDeviationRadians);
  assert.equal(ablated.peakDeviationRadians, 0);
});
test('balanced antagonists retain activity and stiffness although active net torque is zero', () => {
  const trial = motorTrial(pools, { condition: 'coactivation' });
  assert.equal(trial.peakDeviationRadians, 0);
  const leg = trial.frames.find((f) => f.tMs >= 1400).body.legs.find((l) => l.id === 'LF');
  assert.ok(leg.motor.flexor > .6 && leg.motor.extensor > .6);
  assert.ok(Math.abs(leg.motor.driveTorque) < 1e-12); assert.ok(leg.motor.stiffness > MOTOR_PARAMETERS.passiveStiffness * 4);
});
test('same perturbation displaces coactivated joint less than passive joint', () => {
  const passive = motorTrial(pools, { condition: 'passive_disturbance' });
  const active = motorTrial(pools, { condition: 'coactivation_disturbance' });
  assert.ok(passive.peakDeviationRadians > active.peakDeviationRadians * 1.5);
});
test('forward kinematics conserves all segment lengths and hinge angle under bounded dynamics', () => {
  const body = new JointMotorBody(pools); const inputs = Object.fromEntries(Object.values(pools).flatMap((p) => p.flexor.map((id) => [id, 1])));
  for (let t = 0; t < 1600; t++) {
    const frame = body.step(inputs, .002);
    for (const [i, leg] of frame.legs.entries()) {
      for (let j = 0; j < 4; j++) assert.ok(Math.abs(distance(leg.pointsLocal[j], leg.pointsLocal[j + 1]) - LEG_SPECS[i].lengths[j]) < 1e-10);
      assert.ok(leg.jointAngles.femurTibia >= MOTOR_PARAMETERS.minAngle && leg.jointAngles.femurTibia <= MOTOR_PARAMETERS.maxAngle);
      assert.ok(leg.pointsLocal.flat().every(Number.isFinite)); assert.ok(leg.footWorld[1] > 0);
      const p = leg.pointsLocal; const f = p[2].map((v, k) => v - p[1][k]); const tib = p[3].map((v, k) => v - p[2][k]);
      const angle = Math.acos(Math.max(-1, Math.min(1, f.reduce((s, v, k) => s + v * tib[k], 0) / Math.hypot(...f) / Math.hypot(...tib))));
      assert.ok(Math.abs(angle - leg.jointAngles.femurTibia) < 1e-10);
    }
  }
});
