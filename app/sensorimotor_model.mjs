import { JointMotorBody, makeMotorPools, MOTOR_PARAMETERS } from './joint_motor_model.mjs';

/** All numbers below are declared demonstration assumptions, not fitted physiology. */
export const SENSORIMOTOR_PARAMETERS = Object.freeze({
  dt: .002, sensorTau: .01, neuronTau: .02, observationDelay: .008,
  baselineRate: .5, positionGain: 1, velocityGain: .1, graphGain: 4,
  motorGain: 1, tonicMotorActivation: .12,
  rateUnits: 'dimensionless activity, 0–1; not spikes or measured firing rates',
  operatingPoint: 'initial resting joint angle; explicit sensor-centering assumption',
  biologicalCalibration: false,
});
export const POLARITY_HYPOTHESES = Object.freeze([
  { id: 'claw_plus_hook_plus', claw: 1, hook: 1 },
  { id: 'claw_plus_hook_minus', claw: 1, hook: -1 },
  { id: 'claw_minus_hook_plus', claw: -1, hook: 1 },
  { id: 'claw_minus_hook_minus', claw: -1, hook: -1 },
]);
export const SENSORIMOTOR_CONDITIONS = Object.freeze([
  'closed', 'sensory_open', 'frozen', 'replay', 'sensory_edge_ablation',
]);
const clamp = (x, lo = 0, hi = 1) => Math.max(lo, Math.min(hi, x));
const mean = (xs) => xs.length ? xs.reduce((s, x) => s + x, 0) / xs.length : 0;
const idString = (id) => { if (typeof id !== 'string' || !/^\d+$/.test(id)) throw new Error('BANC root IDs must be decimal strings'); return id; };
const pairKey = (edge) => `${edge.pre}>${edge.post}`;
const finite = (x, label) => { if (!Number.isFinite(x)) throw new Error(`Non-finite ${label}`); return x; };

export function centralSign(node, policy = 'verified_only') {
  if (!['verified_only', 'verified_then_predicted'].includes(policy)) throw new Error('Unknown central sign policy');
  const verified = node.ntVerified || null;
  const nt = verified || (policy === 'verified_then_predicted' ? node.ntPredicted : null);
  const signs = { acetylcholine: 1, gaba: -1, glutamate: -1 };
  const sign = signs[String(nt || '').toLowerCase()] || 0;
  return { sign, transmitter: nt, transmitterEvidence: verified ? 'verified_identity' : nt ? 'prediction' : 'unknown',
    effectEvidence: 'assumed central receptor effect; no exact-synapse receptor validation',
    zeroReason: sign ? null : 'unknown, mixed or modulatory transmitter omitted from rate drive' };
}

/** Build a bounded anatomy-backed subnetwork, never a homology merge or v2/v3 union. */
export function buildSensorimotorCircuit(mapping, { detector = 'v2', leg = 'LF', minContacts = 5,
  signPolicy = 'verified_only', includeUnproofread = false } = {}) {
  if (mapping.namespace !== 'BANC_v888') throw new Error('Only BANC_v888 is supported');
  if (!['v2', 'v3'].includes(detector) || !mapping.detectors[detector]) throw new Error('Select exactly one detector');
  if (leg !== 'LF') throw new Error('This experimental circuit only has reviewed LF paths');
  if (!Number.isInteger(minContacts) || minContacts < 1) throw new Error('minContacts must be a positive integer');
  const reviewed = (node) => includeUnproofread || node?.proofread === true;
  const sensors = mapping.sensors.filter((s) => s.leg === leg && ['claw', 'hook'].includes(s.subtype) && reviewed(s));
  const motors = mapping.motors.filter((m) => m.leg === leg && m.joint === 'femurTibia' && ['flex', 'extend'].includes(m.action) && reviewed(m));
  for (const n of [...sensors, ...motors]) idString(n.id);
  if (new Set(sensors.map((s) => s.id)).size !== sensors.length || new Set(motors.map((m) => m.id)).size !== motors.length) throw new Error('Duplicate sensor or motor root');
  const sensorIds = new Set(sensors.map((s) => s.id)); const motorIds = new Set(motors.map((s) => s.id));
  const allSensorIds = new Set(mapping.sensors.map((s) => s.id)); const allMotorIds = new Set(mapping.motors.map((s) => s.id));
  if (!sensors.length || !motors.some((m) => m.action === 'flex') || !motors.some((m) => m.action === 'extend')) throw new Error('Both annotated antagonistic pools and sensors are required');
  const allEdges = new Map();
  for (const edge of mapping.detectors[detector].edges) {
    idString(edge.pre); idString(edge.post);
    if (!Number.isInteger(edge.count) || edge.count < 1) throw new Error('Contact counts must be positive integers');
    const key = pairKey(edge);
    if (allEdges.has(key) && allEdges.get(key).count !== edge.count) throw new Error(`Conflicting duplicate count: ${key}`);
    allEdges.set(key, edge);
  }
  const edges = [...allEdges.values()].filter((e) => e.count >= minContacts && e.pre !== e.post);
  const incomingMotor = new Map();
  for (const edge of edges) if (motorIds.has(edge.post)) {
    if (!incomingMotor.has(edge.pre)) incomingMotor.set(edge.pre, []);
    incomingMotor.get(edge.pre).push(edge);
  }
  const selected = new Map();
  for (const first of edges) if (sensorIds.has(first.pre)) {
    if (motorIds.has(first.post)) selected.set(pairKey(first), first);
    else if (!allSensorIds.has(first.post) && !allMotorIds.has(first.post)
      && mapping.nodes[first.post]?.superClass === 'ventral_nerve_cord_intrinsic' && reviewed(mapping.nodes[first.post])) {
      for (const second of incomingMotor.get(first.post) || []) {
        selected.set(pairKey(first), first); selected.set(pairKey(second), second);
      }
    }
  }
  if (!selected.size) throw new Error('No reviewed sensory-to-MN paths survive the declared threshold');
  const nodeIds = [...new Set([...sensorIds, ...motorIds, ...[...selected.values()].flatMap((e) => [e.pre, e.post])])].sort();
  const nodes = nodeIds.map((id) => {
    const source = mapping.nodes[id] || sensors.find((s) => s.id === id) || motors.find((m) => m.id === id);
    if (!source) throw new Error(`Missing source node ${id}`);
    return { ...source, id, role: sensorIds.has(id) ? 'sensor' : motorIds.has(id) ? 'motor' : 'interneuron',
      signAssumption: centralSign(source, signPolicy) };
  });
  const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));
  const indexById = Object.fromEntries(nodes.map((n, i) => [n.id, i]));
  const totalKey = detector === 'v2' ? 'inputCountV2' : 'inputCountV3';
  const selectedInput = new Map();
  for (const e of selected.values()) selectedInput.set(e.post, (selectedInput.get(e.post) || 0) + e.count);
  const wired = [...selected.values()].sort((a, b) => pairKey(a).localeCompare(pairKey(b))).map((e) => {
    const denominator = byId[e.post][totalKey];
    if (!Number.isFinite(denominator) || denominator < selectedInput.get(e.post)) throw new Error(`Missing or inconsistent full-graph input count for ${e.post}`);
    return { pre: e.pre, post: e.post, count: e.count, detector,
      biologicalSign: null, assumedSign: byId[e.pre].signAssumption.sign,
      fullPostsynapticInputCount: denominator, normalizedWeight: e.count / denominator,
      sourceIndex: indexById[e.pre], targetIndex: indexById[e.post], sensoryEdge: sensorIds.has(e.pre) };
  });
  const pools = makeMotorPools(motors.map((m) => ({ id: m.id, candidate_model_leg: m.leg,
    cell_function_detailed: m.action === 'flex' ? 'flex_femur_tibia_joint' : 'extend_femur_tibia_joint' })));
  return { schema: 'fly.sensorimotor-circuit.v1', namespace: mapping.namespace, detector, leg, minContacts, signPolicy, includeUnproofread,
    sensors, motors, nodes, edges: wired, indexById, pools, anatomySupported: true, tuningValidated: false,
    biologicalReconstructionValidated: false, detectorsMixed: false,
    statistics: { sensors: sensors.length, claw: sensors.filter((s) => s.subtype === 'claw').length,
      hook: sensors.filter((s) => s.subtype === 'hook').length, motors: motors.length,
      interneurons: nodes.filter((n) => n.role === 'interneuron').length, edges: wired.length,
      zeroSignedEdges: wired.filter((e) => e.assumedSign === 0).length,
      predictedSignEdges: wired.filter((e) => byId[e.pre].signAssumption.transmitterEvidence === 'prediction' && e.assumedSign !== 0).length },
    assumptions: [
      'Only LF claw and hook; club and all other legs are outside the dynamic sensory circuit.',
      includeUnproofread ? 'Unproofread nodes explicitly included by caller.' : 'Only nodes explicitly proofread=true are included; other roots are excluded.',
      'All retained direct or one-interneuron routes have the selected minimum contact count on every edge.',
      'Weights use the entire postsynaptic input count from the same detector, not renormalized subgraph input.',
      'Nonselected upstream neurons remain at the centered model baseline; omitted recurrent routes are not reconstructed.',
      'Verified transmitter identity does not establish receptor-specific effect. ACh +1, GABA -1, central glutamate -1 are explicit assumptions.',
      'Central transmitter sign never sets the muscle action: annotated flexion or extension does.',
    ] };
}

export function sensorTargets(circuit, observation, referenceAngle, polarity, parameters = SENSORIMOTOR_PARAMETERS) {
  if (![1, -1].includes(polarity?.claw) || ![1, -1].includes(polarity?.hook)) throw new Error('Both unknown population polarities require explicit +1 or -1 hypotheses');
  finite(observation.angle, 'observed angle'); finite(observation.velocity, 'observed angular velocity');
  return Object.fromEntries(circuit.sensors.map((sensor) => [sensor.id, clamp(parameters.baselineRate +
    (sensor.subtype === 'claw' ? polarity.claw * parameters.positionGain * (observation.angle - referenceAngle)
      : polarity.hook * parameters.velocityGain * observation.velocity))]));
}

export class SensorimotorModel {
  constructor({ circuit, polarity, parameters = {}, bodyParameters = {} }) {
    if (circuit?.schema !== 'fly.sensorimotor-circuit.v1') throw new Error('Build a provenance-checked circuit first');
    this.circuit = circuit; this.parameters = { ...SENSORIMOTOR_PARAMETERS, ...parameters };
    const p = this.parameters;
    for (const name of ['dt', 'sensorTau', 'neuronTau']) if (!(Number.isFinite(p[name]) && p[name] > 0)) throw new Error(`Invalid ${name}`);
    if (p.dt > .01 || !Number.isFinite(p.observationDelay) || p.observationDelay < 0) throw new Error('Invalid integration step or delay');
    for (const name of ['positionGain', 'velocityGain', 'graphGain', 'motorGain']) if (!(Number.isFinite(p[name]) && p[name] >= 0)) throw new Error(`Invalid ${name}`);
    for (const name of ['baselineRate', 'tonicMotorActivation']) if (!(p[name] >= 0 && p[name] <= 1)) throw new Error(`Invalid ${name}`);
    this.polarity = { ...polarity }; this.body = new JointMotorBody(circuit.pools, bodyParameters);
    this.leg = this.body.legs.find((l) => l.spec.id === circuit.leg); this.referenceAngle = this.leg.rest;
    // Validates missing polarity even before any physical perturbation.
    sensorTargets(circuit, { angle: this.referenceAngle, velocity: 0 }, this.referenceAngle, polarity, p);
    this.rates = new Float64Array(circuit.nodes.length).fill(p.baselineRate);
    this.inputs = new Float64Array(circuit.nodes.length); this.targets = new Float64Array(circuit.nodes.length);
    this.sensorSet = new Set(circuit.sensors.map((s) => circuit.indexById[s.id]));
    this.delaySteps = Math.round(p.observationDelay / p.dt); this.delayQueue = [];
    this.frozenTargets = null; this.stepIndex = 0;
    this.last = { observation: { angle: this.referenceAngle, velocity: 0 }, sensorTargets: {}, motorCommands: {}, sensoryMode: 'closed', externalTorque: 0 };
  }
  /** Optional observationClamp is a diagnostic instrument, never an autonomous policy. */
  step({ externalTorque = 0, sensoryMode = 'closed', replayTargets = null,
    freezeAtSeconds = 1.12, observationClamp = null, includeBody = true } = {}) {
    if (!SENSORIMOTOR_CONDITIONS.includes(sensoryMode)) throw new Error('Unknown sensory condition');
    const p = this.parameters; const c = this.circuit;
    const currentObservation = observationClamp || { angle: this.leg.q, velocity: this.leg.velocity };
    this.delayQueue.push({ ...currentObservation });
    const observation = this.delayQueue.length > this.delaySteps ? this.delayQueue.shift() : { angle: this.referenceAngle, velocity: 0 };
    let targets = sensorTargets(c, observation, this.referenceAngle, this.polarity, p);
    if (sensoryMode === 'sensory_open') targets = Object.fromEntries(c.sensors.map((s) => [s.id, p.baselineRate]));
    if (sensoryMode === 'frozen') {
      if (this.stepIndex * p.dt >= freezeAtSeconds && !this.frozenTargets) this.frozenTargets = { ...targets };
      if (this.frozenTargets) targets = this.frozenTargets;
    }
    if (sensoryMode === 'replay') {
      if (!replayTargets) throw new Error('Replay requires the complete recorded sensor-target vector at every step');
      targets = {};
      for (const s of c.sensors) {
        const value = replayTargets[s.id];
        if (!Number.isFinite(value) || value < 0 || value > 1) throw new Error(`Missing or invalid replay sensor ${s.id}`);
        targets[s.id] = value;
      }
    }
    this.inputs.fill(0);
    // Synchronous update: motor responses cannot bypass their real intermediate nodes.
    for (const edge of c.edges) {
      if (sensoryMode === 'sensory_edge_ablation' && edge.sensoryEdge) continue;
      this.inputs[edge.targetIndex] += edge.assumedSign * edge.normalizedWeight * (this.rates[edge.sourceIndex] - p.baselineRate);
    }
    const sensorBlend = 1 - Math.exp(-p.dt / p.sensorTau); const neuralBlend = 1 - Math.exp(-p.dt / p.neuronTau);
    for (let i = 0; i < c.nodes.length; i++) {
      const sensory = this.sensorSet.has(i);
      const target = sensory ? targets[c.nodes[i].id] : clamp(p.baselineRate + p.graphGain * this.inputs[i]);
      this.targets[i] = target;
      this.rates[i] += (target - this.rates[i]) * (sensory ? sensorBlend : neuralBlend);
    }
    const motorCommands = Object.fromEntries(c.motors.map((motor) => [motor.id,
      clamp(p.tonicMotorActivation + p.motorGain * (this.rates[c.indexById[motor.id]] - p.baselineRate))]));
    finite(externalTorque, 'external torque');
    const body = this.body.step(motorCommands, p.dt, new Set(), { [c.leg]: externalTorque });
    this.stepIndex++;
    this.last = { observation: { ...observation }, currentObservation: { ...currentObservation },
      sensorTargets: { ...targets }, motorCommands, sensoryMode, externalTorque };
    return this.snapshot(includeBody ? body : null, includeBody);
  }
  snapshot(body = null, includeBody = true) {
    const c = this.circuit; const p = this.parameters;
    const poolMean = (pool) => mean(c.pools[c.leg][pool].map((id) => this.last.motorCommands[id] ?? p.tonicMotorActivation));
    const rateMean = (subtype) => mean(c.sensors.filter((s) => s.subtype === subtype).map((s) => this.rates[c.indexById[s.id]]));
    return { tMs: this.stepIndex * p.dt * 1000, angle: this.leg.q, velocity: this.leg.velocity,
      deviation: this.leg.q - this.referenceAngle, externalTorque: this.last.externalTorque,
      activeTorque: this.leg.driveTorque, flexor: this.leg.flexor, extensor: this.leg.extensor,
      flexorCommand: poolMean('flexor'), extensorCommand: poolMean('extensor'), coactivation: this.leg.coactivation,
      stiffness: this.leg.stiffness, damping: this.leg.damping, clawRate: rateMean('claw'), hookRate: rateMean('hook'),
      observation: { ...this.last.observation }, sensorTargets: { ...this.last.sensorTargets },
      neuralRates: Object.fromEntries(c.nodes.map((n, i) => [n.id, this.rates[i]])), motorCommands: { ...this.last.motorCommands },
      limitContact: this.leg.q === this.body.parameters.minAngle || this.leg.q === this.body.parameters.maxAngle,
      ...(includeBody ? { body: body || this.body.snapshot() } : {}) };
  }
}
export const createSensorimotorModel = (options) => new SensorimotorModel(options);

function randomGenerator(seed) {
  let s = seed >>> 0;
  return () => { s += 0x6D2B79F5; let t = s; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}

/** A recorded external torque sequence, not a desired route or desired joint trajectory. */
export function makePerturbationSequence({ seed = 260927, duration = 4, dt = .002, counterfactual = false } = {}) {
  if (!(duration > 0 && dt > 0 && dt <= .01)) throw new Error('Invalid perturbation timing');
  const rand = randomGenerator(seed);
  const pulses = [{ at: 1, width: .1, amplitude: 12 * (.9 + .2 * rand()) },
    { at: 2.2, width: .12, amplitude: -10 * (.9 + .2 * rand()) }];
  if (counterfactual) pulses.push({ at: 2.8, width: .1, amplitude: 9 });
  const count = Math.round(duration / dt);
  return Array.from({ length: count }, (_, i) => pulses.reduce((sum, pulse) => {
    const t = i * dt; return sum + (t >= pulse.at && t < pulse.at + pulse.width ? pulse.amplitude : 0);
  }, 0));
}

export function runSensorimotorTrial({ circuit, polarity, parameters = {}, bodyParameters = {},
  condition = 'closed', seed = 260927, duration = 4, perturbations = null, replay = null,
  freezeAtSeconds = 1.12, recordEvery = 1, includeBody = false, recordNeurons = true } = {}) {
  if (!SENSORIMOTOR_CONDITIONS.includes(condition)) throw new Error('Unknown sensory condition');
  if (!Number.isInteger(recordEvery) || recordEvery < 1) throw new Error('Invalid recording interval');
  const model = new SensorimotorModel({ circuit, polarity, parameters, bodyParameters }); const p = model.parameters;
  const torques = perturbations || makePerturbationSequence({ seed, duration, dt: p.dt });
  if (torques.length !== Math.round(duration / p.dt)) throw new Error('Perturbation length must cover each integration step');
  if (condition === 'replay' && replay?.length !== torques.length) throw new Error('Replay must cover each integration step');
  const frames = []; const sensorRecording = []; const activeTorques = [];
  let peak = 0; let squared = 0; let maxMotorDelta = 0; let saturated = 0; let limits = 0; let sensorDeviation = 0;
  let firstSensorResponseMs = null; let firstMotorResponseMs = null;
  for (let i = 0; i < torques.length; i++) {
    const frame = model.step({ externalTorque: torques[i], sensoryMode: condition,
      replayTargets: replay?.[i], freezeAtSeconds, includeBody });
    peak = Math.max(peak, Math.abs(frame.deviation)); squared += frame.deviation ** 2;
    maxMotorDelta = Math.max(maxMotorDelta, Math.abs(frame.flexorCommand - frame.extensorCommand));
    const sensoryDelta = Math.max(Math.abs(frame.clawRate - p.baselineRate), Math.abs(frame.hookRate - p.baselineRate));
    sensorDeviation = Math.max(sensorDeviation, sensoryDelta);
    if (sensoryDelta > 1e-10 && firstSensorResponseMs === null) firstSensorResponseMs = frame.tMs;
    if (Math.abs(frame.activeTorque) > 1e-10 && firstMotorResponseMs === null) firstMotorResponseMs = frame.tMs;
    saturated += Object.values(frame.neuralRates).filter((x) => x < 1e-6 || x > 1 - 1e-6).length;
    limits += frame.limitContact ? 1 : 0;
    sensorRecording.push(frame.sensorTargets); activeTorques.push(frame.activeTorque);
    if (i % recordEvery === 0 || i === torques.length - 1) {
      if (!recordNeurons) { delete frame.neuralRates; delete frame.sensorTargets; delete frame.motorCommands; }
      frames.push(frame);
    }
  }
  return { schema: 'fly.sensorimotor-trial.v1', namespace: circuit.namespace, detector: circuit.detector, leg: circuit.leg,
    condition, polarity: { ...polarity }, seed, duration, parameters: p, bodyParameters: model.body.parameters,
    circuitStatistics: circuit.statistics, neuralPropagationSimulated: true, neuralModel: 'centered low-pass rate network',
    closedLoop: condition === 'closed',
    sensorObservationUsesJoint: ['closed', 'sensory_edge_ablation', 'frozen'].includes(condition),
    feedbackIntact: condition === 'closed', frozenAfterSeconds: condition === 'frozen' ? freezeAtSeconds : null,
    biologicalReconstructionValidated: false, originalGraphModified: false,
    frames, sensorRecording, perturbations: [...torques], activeTorques,
    summary: { peakDeviationRadians: peak, rmsDeviationRadians: Math.sqrt(squared / torques.length),
      finalDeviationRadians: model.leg.q - model.referenceAngle, maxMotorCommandDifference: maxMotorDelta,
      maxSensorRateDeviation: sensorDeviation, saturatedNodeSteps: saturated, jointLimitSteps: limits,
      firstSensorResponseMs, firstMotorResponseMs, integrationSteps: torques.length } };
}

/** Sinusoidal clamp is ONLY an externally prescribed system-identification probe, never a gait driver. */
export function measureClampedTransfer({ circuit, polarity, parameters = {}, frequencyHz = 2, amplitudeRadians = .005,
  cycles = 8, discardCycles = 3 } = {}) {
  if (!(frequencyHz > 0 && amplitudeRadians > 0 && cycles > discardCycles && discardCycles >= 1)) throw new Error('Invalid transfer probe');
  const model = new SensorimotorModel({ circuit, polarity, parameters }); const dt = model.parameters.dt;
  const steps = Math.round(cycles / frequencyHz / dt); const discard = Math.round(discardCycles / frequencyHz / dt);
  let sine = 0; let cosine = 0; let n = 0; const w = 2 * Math.PI * frequencyHz;
  for (let i = 0; i < steps; i++) {
    const t = i * dt;
    const sample = model.step({ observationClamp: { angle: model.referenceAngle + amplitudeRadians * Math.sin(w * t),
      velocity: amplitudeRadians * w * Math.cos(w * t) }, includeBody: false });
    if (i >= discard) { sine += sample.activeTorque * Math.sin(w * t); cosine += sample.activeTorque * Math.cos(w * t); n++; }
  }
  const gain = 2 * Math.hypot(sine, cosine) / n / amplitudeRadians;
  return { frequencyHz, amplitudeRadians, cycles, discardedCycles: discardCycles,
    torqueGainPerRadian: gain, torquePhaseDegrees: gain > 1e-12 ? Math.atan2(cosine, sine) * 180 / Math.PI : null,
    output: 'active muscle torque, including activation filter; no passive spring torque',
    input: 'externally clamped sensor observation, body angle is not used for this diagnostic',
    interpretation: 'computed linear-neighborhood transfer under declared assumptions; not measured neural physiology or autonomous gait' };
}

export const sensorimotorProvenance = Object.freeze({
  structure: 'exact BANC v888 IDs and one detector at a time; muscle actions are curated annotations',
  modalities: 'claw position and hook direction/velocity are population-level literature roles',
  unknown: 'exact-root tuning polarity, thresholds, gains, intrinsic dynamics, receptor effects, recruitment, force and inertia are uncalibrated',
  model: 'uniform population polarity hypotheses, centered rate states, tonic muscle drive and joint mechanics are declared choices',
  scope: 'one suspended LF femur–tibia joint; not whole-brain autonomy, gait, balance or locomotion',
  references: [
    'https://www.nature.com/articles/s41467-025-59302-3',
    'https://pmc.ncbi.nlm.nih.gov/articles/PMC6481666/',
    'https://pmc.ncbi.nlm.nih.gov/articles/PMC7347388/',
  ],
  bodyDefaults: MOTOR_PARAMETERS,
});
