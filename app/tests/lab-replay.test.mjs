import test from 'node:test';
import assert from 'node:assert/strict';
import { ArticulatedBody } from '../body-kinematics.mjs';
import { readoutRates, ratesToControl, buildBodyReplay, makeActuatorControl, frameAt } from '../lab-replay.mjs';

const scenario = { readouts: [{ id: 'exact-root-1', label: 'aDN1', bodyChannel: 'grooming' },
  { id: 'exact-root-2', label: 'aDN2', bodyChannel: 'grooming' },
  { id: 'interneuron', label: 'aBN1', bodyChannel: 'none' }] };
const makeTrial = (drive) => ({ durationMs: 600, samples: Array.from({ length: 600 }, (_, i) => ({ tMs: i + 1,
  spikesByReadout: { 'exact-root-1': drive && i >= 100 && i % 10 === 0 ? 1 : 0,
    'exact-root-2': 0, interneuron: i % 5 === 0 ? 1 : 0 } })) });

test('causal window does not anticipate later spikes or include expired bins', () => {
  const rates = readoutRates([{ tMs: 0, spikesByReadout: {} }, { tMs: 10, spikesByReadout: { x: 1 } },
    { tMs: 109, spikesByReadout: {} }, { tMs: 110, spikesByReadout: {} }], ['x'], 100);
  assert.deepEqual(rates.map((x) => x.x), [0, 10, 10, 0]);
});
test('no readout response remains exactly zero; interneuron does not drive body', () => {
  assert.equal(ratesToControl({ interneuron: 1000 }, scenario).groom, 0);
  const replay = buildBodyReplay(scenario, makeTrial(false));
  assert.equal(replay.jointMotion, 0);
  assert.equal(replay.movement, false);
  assert.equal(replay.frames.at(-1).body.contacts, 6);
});
test('aDN population average and gain are explicit, bounded and nonnegative', () => {
  assert.equal(ratesToControl({ 'exact-root-1': 50, 'exact-root-2': 0 }, scenario).groom, 0.5);
  assert.equal(ratesToControl({ 'exact-root-1': -100, 'exact-root-2': 0 }, scenario).groom, 0);
  assert.equal(ratesToControl({ 'exact-root-1': 10000 }, scenario).groom, 1);
  assert.equal(ratesToControl({ 'exact-root-1': 50 }, { readouts: [{ id: 'exact-root-1', label: 'aBN1', bodyChannel: 'grooming' }] }).groom, 0);
});
test('proboscis and steering readouts do not silently become grooming or locomotion', () => {
  const control = ratesToControl({ x: 1000 }, { readouts: [{ id: 'x', label: 'MN9', bodyChannel: 'proboscis' }] });
  assert.equal(control.groom, 0); assert.equal(control.forward, 0); assert.equal(control.turn, 0);
});
test('replay uses same kinematics as arena with identical body time', () => {
  const replay = buildBodyReplay(scenario, makeTrial(true));
  const body = new ArticulatedBody({ x: 0, z: 0, yaw: 0 });
  for (const frame of replay.frames.slice(1)) body.update({ x: 0, z: 0, yaw: 0 }, frame.control, .001);
  assert.deepEqual(replay.frames.at(-1).body, body.snapshot());
  assert.ok(replay.jointMotion > 0);
  assert.ok(Math.abs(replay.frames.at(-1).body.timeSeconds - 0.6) < 1e-10);
  assert.equal(replay.frames.at(-1).body.pose.x, 0); assert.equal(replay.frames.at(-1).body.pose.z, 0);
});
test('repeatability and arbitrary replay scrubbing do not recompute neural data', () => {
  const a = buildBodyReplay(scenario, makeTrial(true)); const b = buildBodyReplay(scenario, makeTrial(true));
  assert.deepEqual(a, b);
  assert.equal(frameAt(a, 99.9).tMs, 99); assert.equal(frameAt(a, 9000).tMs, 600);
  assert.equal(frameAt(a, 0).tMs, 0);
});
test('technical actuator control has no neural values and visibly moves joints', () => {
  const replay = makeActuatorControl(); assert.equal(replay.technicalControl, true);
  assert.equal(replay.totalReadoutSpikes, null); assert.deepEqual(replay.mappedIds, []);
  assert.ok(replay.jointMotion > 1); assert.ok(replay.frames.some((f) => f.body.legs.some((l) => l.phase === 'groom')));
});
test('out of order or excessively sparse samples fail closed', () => {
  assert.throws(() => readoutRates([{ tMs: 2 }, { tMs: 1 }], ['x']), /ordered/);
  assert.throws(() => buildBodyReplay(scenario, { samples: [{ tMs: 500 }] }), /100ms/);
});
