import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { buildSensorimotorCircuit, createSensorimotorModel, runSensorimotorTrial, sensorTargets,
  makePerturbationSequence, measureClampedTransfer, centralSign, SENSORIMOTOR_PARAMETERS } from '../sensorimotor_model.mjs';
import { LEG_SPECS } from '../body-kinematics.mjs';
import { MOTOR_PARAMETERS } from '../joint_motor_model.mjs';
const mapping = JSON.parse(await readFile(new URL('../data/sensorimotor_mapping.json', import.meta.url)));
const circuit = buildSensorimotorCircuit(mapping);
const polarity = { claw: 1, hook: 1 };
const options = { circuit, polarity, recordEvery: 10, recordNeurons: false };
const distance = (a, b) => Math.hypot(...a.map((v, i) => v - b[i]));

test('every retained edge keeps exact roots/count from one detector and full-graph normalization', () => {
  for (const detector of ['v2', 'v3']) {
    const c = buildSensorimotorCircuit(mapping, { detector });
    const source = new Map(mapping.detectors[detector].edges.map((e) => [`${e.pre}>${e.post}`, e.count]));
    assert.equal(c.statistics.sensors, 54); assert.equal(c.statistics.motors, 19);
    assert.equal(c.pools.LF.flexor.length, 17); assert.equal(c.pools.LF.extensor.length, 2);
    assert.ok(c.nodes.every((n) => typeof n.id === 'string' && n.proofread === true));
    assert.equal(c.statistics.predictedSignEdges, 0);
    assert.ok(c.sensors.every((s) => s.tuningPolarity === null));
    for (const edge of c.edges) {
      assert.equal(source.get(`${edge.pre}>${edge.post}`), edge.count);
      assert.ok(edge.count >= 5); assert.equal(edge.detector, detector);
      assert.equal(edge.biologicalSign, null);
      assert.equal(edge.normalizedWeight, edge.count / mapping.nodes[edge.post][detector === 'v2' ? 'inputCountV2' : 'inputCountV3']);
    }
    const fromSensors = new Set(c.edges.filter((e) => c.sensors.some((s) => s.id === e.pre)).map((e) => e.post));
    const toMotors = new Set(c.edges.filter((e) => c.motors.some((m) => m.id === e.post)).map((e) => e.pre));
    for (const n of c.nodes.filter((n) => n.role === 'interneuron')) assert.ok(fromSensors.has(n.id) && toMotors.has(n.id));
  }
});

test('unreviewed namespaces, other legs, conflicting counts and missing denominators fail clearly', () => {
  assert.throws(() => buildSensorimotorCircuit({ ...mapping, namespace: 'FAFB_v783' }), /BANC/);
  assert.throws(() => buildSensorimotorCircuit(mapping, { leg: 'RF' }), /reviewed LF/);
  assert.throws(() => buildSensorimotorCircuit(mapping, { detector: 'v2+v3' }), /one detector/);
  const copy = structuredClone(mapping); copy.detectors.v2.edges.push({ ...copy.detectors.v2.edges[0], count: 99 });
  assert.throws(() => buildSensorimotorCircuit(copy), /Conflicting/);
  const broken = structuredClone(mapping); broken.nodes[circuit.edges[0].post].inputCountV2 = null;
  assert.throws(() => buildSensorimotorCircuit(broken), /input count/);
});

test('proofread=false is excluded as a boolean and never accepted because a string is truthy', () => {
  const copy = structuredClone(mapping); const id = circuit.sensors[0].id;
  copy.sensors.find((s) => s.id === id).proofread = false; copy.nodes[id].proofread = false;
  const excluded = buildSensorimotorCircuit(copy);
  assert.ok(!excluded.sensors.some((s) => s.id === id)); assert.ok(!excluded.edges.some((e) => e.pre === id));
  assert.ok(buildSensorimotorCircuit(copy, { includeUnproofread: true }).sensors.some((s) => s.id === id));
  copy.sensors.find((s) => s.id === id).proofread = 'FALSE';
  assert.ok(!buildSensorimotorCircuit(copy).sensors.some((s) => s.id === id));
});

test('unknown tuning is explicit; uniform population hypotheses invert responses without inventing classes', () => {
  assert.throws(() => createSensorimotorModel({ circuit }), /polarities/);
  const plus = sensorTargets(circuit, { angle: 1.7, velocity: .2 }, 1.6, polarity);
  const minus = sensorTargets(circuit, { angle: 1.7, velocity: .2 }, 1.6, { claw: -1, hook: -1 });
  for (const sensor of circuit.sensors) {
    assert.ok(Math.abs(plus[sensor.id] + minus[sensor.id] - 1) < 1e-12);
    assert.equal(plus[sensor.id], sensor.subtype === 'claw' ? .5 + (1.7 - 1.6) : .52);
  }
  assert.equal(centralSign({ ntVerified: null, ntPredicted: 'gaba' }).sign, 0);
  assert.equal(centralSign({ ntVerified: null, ntPredicted: 'gaba' }, 'verified_then_predicted').sign, -1);
  // Motor predicted GABA is never the muscle-action sign.
  assert.ok(circuit.motors.some((m) => m.action === 'flex' && m.ntPredicted === 'gaba'));
  assert.ok(circuit.motors.filter((m) => m.action === 'flex').every((m) => circuit.pools.LF.flexor.includes(m.id)));
});

test('zero perturbation has no gait or net active torque; tonic coactivation remains visible', () => {
  const t = runSensorimotorTrial({ ...options, perturbations: new Array(2000).fill(0) });
  assert.ok(t.summary.peakDeviationRadians < 1e-12);
  assert.ok(t.frames.at(-1).coactivation > .119);
  assert.ok(t.frames.every((f) => Math.abs(f.activeTorque) < 1e-12));
  assert.equal(t.biologicalReconstructionValidated, false);
});

test('genuine perturbation traverses observed sensory/neural/MN states with causal delay', () => {
  const fast = runSensorimotorTrial({ ...options, parameters: { observationDelay: 0 } });
  const slow = runSensorimotorTrial({ ...options, parameters: { observationDelay: .04 } });
  assert.ok(fast.summary.maxSensorRateDeviation > .01); assert.ok(fast.summary.maxMotorCommandDifference > .001);
  assert.ok(fast.summary.firstMotorResponseMs > fast.summary.firstSensorResponseMs);
  assert.equal(slow.summary.firstSensorResponseMs - fast.summary.firstSensorResponseMs, 40);
  assert.equal(slow.summary.firstMotorResponseMs - fast.summary.firstMotorResponseMs, 40);
});

test('open feedback, zero graph gain and sensory-edge ablation share mechanical response, while sensors still respond after edge ablation', () => {
  const open = runSensorimotorTrial({ ...options, condition: 'sensory_open' });
  const off = runSensorimotorTrial({ ...options, condition: 'sensory_edge_ablation' });
  const zero = runSensorimotorTrial({ ...options, parameters: { graphGain: 0 } });
  assert.deepEqual(open.frames.map((f) => f.angle), off.frames.map((f) => f.angle));
  assert.deepEqual(open.frames.map((f) => f.angle), zero.frames.map((f) => f.angle));
  assert.equal(open.summary.maxSensorRateDeviation, 0);
  assert.ok(off.summary.maxSensorRateDeviation > .01);
  assert.equal(off.summary.maxMotorCommandDifference, open.summary.maxMotorCommandDifference);
  assert.ok(open.summary.peakDeviationRadians > .1); // Mechanical spring return is present without neural feedback.
});

test('seeded disturbances are paired exactly and altered seeds change the independent perturbation', () => {
  const a = makePerturbationSequence({ seed: 1 }); const b = makePerturbationSequence({ seed: 1 }); const c = makePerturbationSequence({ seed: 2 });
  assert.deepEqual(a, b); assert.notDeepEqual(a, c);
  const first = runSensorimotorTrial({ ...options, seed: 1 }); const second = runSensorimotorTrial({ ...options, seed: 1 });
  assert.deepEqual(first.frames, second.frames);
});

test('replay reproduces donor but cannot adapt motor commands to an unseen counterfactual disturbance', () => {
  const donor = runSensorimotorTrial(options);
  const replay = runSensorimotorTrial({ ...options, condition: 'replay', replay: donor.sensorRecording });
  assert.deepEqual(donor.frames.map((f) => f.angle), replay.frames.map((f) => f.angle));
  const changed = makePerturbationSequence({ counterfactual: true });
  const blind = runSensorimotorTrial({ ...options, condition: 'replay', perturbations: changed, replay: donor.sensorRecording });
  const adaptive = runSensorimotorTrial({ ...options, perturbations: changed });
  assert.deepEqual(blind.activeTorques, donor.activeTorques);
  assert.notDeepEqual(adaptive.activeTorques, donor.activeTorques);
  assert.notDeepEqual(blind.frames.map((f) => f.angle), donor.frames.map((f) => f.angle));
  assert.throws(() => runSensorimotorTrial({ ...options, condition: 'replay' }), /Replay/);
});

test('frozen control retains nonzero recorded receptor input while physical joint continues to change', () => {
  const t = runSensorimotorTrial({ ...options, condition: 'frozen' });
  const ix = Math.round(1.12 / SENSORIMOTOR_PARAMETERS.dt);
  assert.deepEqual(t.sensorRecording[ix], t.sensorRecording.at(-1));
  assert.ok(Object.values(t.sensorRecording[ix]).some((v) => Math.abs(v - .5) > .001));
  assert.notEqual(t.frames.find((f) => f.tMs >= 1300).angle, t.frames.at(-1).angle);
});

test('clamped transfer diagnostic has explicit phase and gain, and delay produces the predicted phase shift', () => {
  const a = measureClampedTransfer({ circuit, polarity, parameters: { observationDelay: 0 }, frequencyHz: 2 });
  const b = measureClampedTransfer({ circuit, polarity, parameters: { observationDelay: .02 }, frequencyHz: 2 });
  assert.ok(a.torqueGainPerRadian > 0);
  const phaseDifference = ((b.torquePhaseDegrees - a.torquePhaseDegrees + 540) % 360) - 180;
  assert.ok(Math.abs(phaseDifference - (-360 * 2 * .02)) < .1);
  assert.ok(Math.abs(b.torqueGainPerRadian / a.torqueGainPerRadian - 1) < .002);
  const off = measureClampedTransfer({ circuit, polarity, parameters: { graphGain: 0 }, frequencyHz: 2 });
  assert.ok(off.torqueGainPerRadian < 1e-12); assert.equal(off.torquePhaseDegrees, null);
});

test('closed-loop samples use the existing bounded forward geometry; the other five legs stay unchanged', () => {
  const t = runSensorimotorTrial({ ...options, includeBody: true, parameters: { graphGain: 16 },
    polarity: { claw: -1, hook: -1 } });
  for (const frame of t.frames) {
    assert.equal(frame.body.contacts, 0); assert.equal(frame.body.gaitFrequencyHz, 0);
    for (const [i, leg] of frame.body.legs.entries()) {
      assert.ok(leg.pointsLocal.flat().every(Number.isFinite));
      assert.ok(leg.jointAngles.femurTibia >= MOTOR_PARAMETERS.minAngle && leg.jointAngles.femurTibia <= MOTOR_PARAMETERS.maxAngle);
      for (let j = 0; j < 4; j++) assert.ok(Math.abs(distance(leg.pointsLocal[j], leg.pointsLocal[j + 1]) - LEG_SPECS[i].lengths[j]) < 1e-10);
      if (leg.id !== 'LF') assert.deepEqual(leg.pointsLocal, t.frames[0].body.legs[i].pointsLocal);
    }
  }
});
