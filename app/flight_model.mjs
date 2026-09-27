import { JointMotorBody, makeMotorPools, poolActivation } from './joint_motor_model.mjs';
import { localToWorld } from './body-kinematics.mjs';

export const FLIGHT_PARAMETERS = Object.freeze({
  dt: .00005, naturalFrequencyHz: 200, passiveDamping: 80, powerDampingGain: 350,
  amplitudeDamping: 650, mechanicalCoupling: 20000, couplingDamping: 20, aeroDrag: .02,
  powerActivationTau: .015, steeringActivationTau: .004, tonicPower: .7,
  steeringTransmissionGain: .45, steeringPolarity: 1, steeringBaseline: .5,
  pitchFrequencyHz: 600, pitchDampingRatio: .6, pitchFlowAngle: .7, pitchVelocityScale: 120,
  forceGain: .000001, leverArm: .08, rollInertia: .002, rollDamping: .005,
  sensorDelay: .003, sensorTau: .002, sensorRateScale: 1, feedbackGain: .6,
  haltereFrequencyHz: 220, haltereDampingRatio: .7, haltereTransmission: -.12,
  strokeMin: -1.5, strokeMax: 1.5, pitchMin: -1.27, pitchMax: 2.92,
  haltereLimit: .2, rollLimit: 1.2, initialPerturbation: .002,
});
const sourceXml = 'data/research_sources/other/autonomous_behavior/flybody/github/flybody/fruitfly/assets/fruitfly.xml';
export const FLIGHT_PARAMETER_PROVENANCE = Object.freeze(Object.fromEntries(Object.keys(FLIGHT_PARAMETERS).map((key) => [key,
  ['strokeMin', 'strokeMax', 'pitchMin', 'pitchMax', 'haltereLimit'].includes(key)
    ? { evidence: 'range copied from Flybody model XML; coordinate adapter is ours', source: sourceXml, biologicalCalibration: false }
    : { evidence: 'declared reduced-model assumption; not fitted to this animal', source: 'this experiment', biologicalCalibration: false }])));
export const FLIGHT_CONDITIONS = Object.freeze([
  { id: 'passive', label: 'Passiv · kein Leistungsantrieb' },
  { id: 'power', label: 'Tonischer DLM/DVM-Antrieb' },
  { id: 'power_off', label: 'Antrieb nach halber Zeit aus' },
  { id: 'power_pool_ablation', label: 'DVM-Pools ausgeschaltet' },
  { id: 'left_steering', label: 'Direkter b1-Test links' },
  { id: 'right_steering', label: 'Direkter b1-Test rechts' },
  { id: 'roll_open', label: 'Rollstörung · Rückmeldung offen' },
  { id: 'roll_feedback', label: 'Rollstörung · technische Rückmeldung' },
]);
const SIDES = ['left', 'right'];
const clamp = (v, lo = 0, hi = 1) => Math.max(lo, Math.min(hi, v));
const mean = (a) => a.length ? a.reduce((s, x) => s + x, 0) / a.length : 0;

export function buildFlightMotorPools(mapping) {
  if (mapping?.schema !== 'fly.flight-control-mapping.v1' || mapping.namespace !== 'BANC_v888') throw new Error('Expected exact BANC flight-control mapping');
  const pools = Object.fromEntries(SIDES.map((side) => [side, { DLM: [], DVM: [], b1: [] }]));
  const seen = new Map(); const selected = [];
  for (const motor of mapping.motors) {
    if (motor.eligibleForAnatomicalMotorPool !== true || motor.proofread !== true || !SIDES.includes(motor.effectorSide)) continue;
    if (typeof motor.id !== 'string' || !/^\d+$/.test(motor.id)) throw new Error('Motor root IDs must remain decimal strings');
    let pool = null;
    if (motor.mechanism === 'asynchronous_wing_power') pool = motor.targetMuscle === 'dorsal_longitudinal_muscle' ? 'DLM'
      : motor.targetMuscle === 'dorsoventral_muscle' ? 'DVM' : null;
    if (motor.mechanism === 'synchronous_wing_steering' && motor.targetMuscle === 'b1_muscle') pool = 'b1';
    if (!pool) continue;
    const role = `${motor.effectorSide}:${pool}`;
    if (seen.has(motor.id) && seen.get(motor.id) !== role) throw new Error(`Conflicting effector assignment ${motor.id}`);
    if (seen.has(motor.id)) continue;
    seen.set(motor.id, role); pools[motor.effectorSide][pool].push(motor.id); selected.push({ ...motor, modelPool: pool });
  }
  for (const side of SIDES) for (const name of ['DLM', 'DVM', 'b1']) if (!pools[side][name].length) throw new Error(`Missing annotated ${side} ${name} pool`);
  return { ...pools, selected, namespace: mapping.namespace,
    kinematicSignsValidated: false, forceGainsCalibrated: false,
    effectorRule: 'peripheral nerve prefix from effectorSide; never blindly soma/sourceSide' };
}

export class FlightModel {
  constructor({ mapping, pools = null, parameters = {}, seed = 260927 } = {}) {
    this.pools = pools || buildFlightMotorPools(mapping); this.parameters = { ...FLIGHT_PARAMETERS, ...parameters };
    const p = this.parameters;
    for (const [name, v] of Object.entries(p)) if (!Number.isFinite(v)) throw new Error(`Invalid ${name}`);
    if (!(p.dt > 0 && p.dt <= .0001)) throw new Error('Flight mechanical integration requires 0 < dt <= 100µs');
    if (![1, -1].includes(p.steeringPolarity)) throw new Error('Steering effect requires an explicit tested polarity hypothesis');
    for (const name of ['naturalFrequencyHz', 'pitchFrequencyHz', 'haltereFrequencyHz', 'powerActivationTau', 'steeringActivationTau', 'sensorTau', 'sensorRateScale', 'rollInertia']) if (p[name] <= 0) throw new Error(`Invalid ${name}`);
    this.seed = seed; this.time = 0; this.stepIndex = 0;
    const random = (((seed >>> 0) * 1664525 + 1013904223) >>> 0) / 4294967296;
    const displacement = p.initialPerturbation * (.8 + .4 * random);
    // Same initial microscopic perturbation on both sides: no hidden lateral bias or periodic forcing.
    this.state = new Float64Array([displacement, 0, 0, 0, 0, 0, displacement, 0, 0, 0, 0, 0, 0, 0]);
    this.activation = Object.fromEntries(SIDES.map((s) => [s, { DLM: 0, DVM: 0, b1: p.steeringBaseline }]));
    this.sensor = 0; this.delayQueue = []; this.delaySteps = Math.round(p.sensorDelay / p.dt);
    this.commands = {}; this.externalRollTorque = 0; this.limitContacts = 0;
    this.cumulativePowerWork = 0; this.cumulativeDissipation = 0;
    this.baseBody = new JointMotorBody(makeMotorPools([])).snapshot();
  }
  forces(state = this.state) {
    const p = this.parameters;
    // Signed lift surrogate from actual stroke speed and passive pitch, not a prescribed wingbeat phase.
    const left = p.forceGain * state[1] * Math.abs(state[1]) * Math.sin(2 * state[2]);
    const right = p.forceGain * state[7] * Math.abs(state[7]) * Math.sin(2 * state[8]);
    const rollTorque = p.leverArm * (right - left);
    return { left, right, verticalSum: left + right, rollTorque, externalRollTorque: this.externalRollTorque,
      rollDampingTorque: -p.rollDamping * state[13], netRollTorque: rollTorque + this.externalRollTorque - p.rollDamping * state[13],
      units: 'arbitrary model force and moment units; no Newton or body-weight support claim' };
  }
  derivatives(state) {
    const p = this.parameters; const out = new Float64Array(14); const w = 2 * Math.PI * p.naturalFrequencyHz;
    const wp = 2 * Math.PI * p.pitchFrequencyHz; const wh = 2 * Math.PI * p.haltereFrequencyHz;
    for (const [sideIndex, side] of SIDES.entries()) {
      const i = sideIndex * 6; const other = (1 - sideIndex) * 6; const a = this.activation[side];
      const power = Math.min(a.DLM, a.DVM); // Explicit reduced-model requirement for both antagonistic power groups.
      const transmission = Math.max(0, 1 + p.steeringPolarity * p.steeringTransmissionGain * (a.b1 - p.steeringBaseline));
      const drive = p.powerDampingGain * power * transmission;
      out[i] = state[i + 1];
      out[i + 1] = -w * w * state[i] + (drive - p.passiveDamping - p.amplitudeDamping * state[i] ** 2) * state[i + 1]
        - p.aeroDrag * state[i + 1] * Math.abs(state[i + 1]) + p.mechanicalCoupling * (state[other] - state[i])
        + p.couplingDamping * (state[other + 1] - state[i + 1]);
      const pitchTarget = p.pitchFlowAngle * Math.tanh(state[i + 1] / p.pitchVelocityScale);
      out[i + 2] = state[i + 3]; out[i + 3] = wp * wp * (pitchTarget - state[i + 2]) - 2 * p.pitchDampingRatio * wp * state[i + 3];
      out[i + 4] = state[i + 5]; out[i + 5] = wh * wh * (p.haltereTransmission * state[i] - state[i + 4])
        - 2 * p.haltereDampingRatio * wh * state[i + 5];
    }
    out[12] = state[13]; out[13] = this.forces(state).netRollTorque / p.rollInertia;
    return out;
  }
  /** Direct normalized MN commands are a test intervention, not inferred brain activity. */
  step({ motorCommandsById = {}, externalRollTorque = 0 } = {}) {
    const p = this.parameters; const dt = p.dt;
    if (!Number.isFinite(externalRollTorque)) throw new Error('Nonfinite external roll torque');
    this.commands = { ...motorCommandsById }; this.externalRollTorque = externalRollTorque;
    this.delayQueue.push(this.state[13]);
    const delayed = this.delayQueue.length > this.delaySteps ? this.delayQueue.shift() : 0;
    const sensorTarget = clamp(delayed / p.sensorRateScale, -1, 1);
    this.sensor += (sensorTarget - this.sensor) * (1 - Math.exp(-dt / p.sensorTau));
    for (const side of SIDES) for (const group of ['DLM', 'DVM', 'b1']) {
      const target = poolActivation(this.pools[side][group], motorCommandsById);
      const tau = group === 'b1' ? p.steeringActivationTau : p.powerActivationTau;
      this.activation[side][group] += (target - this.activation[side][group]) * (1 - Math.exp(-dt / tau));
    }
    const x = this.state; const k1 = this.derivatives(x);
    const stage = (k, fraction) => Float64Array.from(x, (v, i) => v + dt * fraction * k[i]);
    const k2 = this.derivatives(stage(k1, .5)); const k3 = this.derivatives(stage(k2, .5)); const k4 = this.derivatives(stage(k3, 1));
    for (let i = 0; i < x.length; i++) x[i] += dt / 6 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]);
    const constrain = (angleIndex, lo, hi) => {
      if (x[angleIndex] < lo) { x[angleIndex] = lo; x[angleIndex + 1] = Math.max(0, x[angleIndex + 1]); this.limitContacts++; }
      if (x[angleIndex] > hi) { x[angleIndex] = hi; x[angleIndex + 1] = Math.min(0, x[angleIndex + 1]); this.limitContacts++; }
    };
    for (const [index, side] of SIDES.entries()) {
      const i = index * 6; constrain(i, p.strokeMin, p.strokeMax); constrain(i + 2, p.pitchMin, p.pitchMax); constrain(i + 4, -p.haltereLimit, p.haltereLimit);
      const a = this.activation[side]; const trans = Math.max(0, 1 + p.steeringPolarity * p.steeringTransmissionGain * (a.b1 - p.steeringBaseline));
      this.cumulativePowerWork += p.powerDampingGain * Math.min(a.DLM, a.DVM) * trans * x[i + 1] ** 2 * dt;
      this.cumulativeDissipation += ((p.passiveDamping + p.amplitudeDamping * x[i] ** 2) * x[i + 1] ** 2 + p.aeroDrag * Math.abs(x[i + 1]) ** 3) * dt;
    }
    this.cumulativeDissipation += p.couplingDamping * (x[1] - x[7]) ** 2 * dt;
    constrain(12, -p.rollLimit, p.rollLimit);
    if (!x.every(Number.isFinite)) throw new Error('Nonfinite flight dynamics');
    this.stepIndex++; this.time = this.stepIndex * dt;
  }
  snapshot() {
    const p = this.parameters; const x = this.state; const pose = { ...this.baseBody.pose, roll: x[12] };
    const body = { ...this.baseBody, model: 'tethered-wing-and-roll-test', timeSeconds: this.time, pose,
      legs: this.baseBody.legs.map((l) => ({ ...l, footWorld: localToWorld(l.pointsLocal.at(-1), pose), footTargetWorld: localToWorld(l.pointsLocal.at(-1), pose) })) };
    const wings = {}; const halteres = {};
    for (const [index, side] of SIDES.entries()) {
      const i = index * 6; wings[side] = { stroke: x[i], elevation: 0, pitch: x[i + 2] }; halteres[side] = x[i + 4];
    }
    const w = 2 * Math.PI * p.naturalFrequencyHz;
    const oscillatorEnergy = .5 * (x[1] ** 2 + x[7] ** 2) + .5 * w ** 2 * (x[0] ** 2 + x[6] ** 2)
      + .5 * p.mechanicalCoupling * (x[0] - x[6]) ** 2;
    return { tMs: this.time * 1000, body, world: { position: { x: 0, y: pose.height, z: 0 }, roll: x[12], rollRate: x[13], translationEnabled: false },
      flightKinematics: { wings, halteres }, forces: this.forces(),
      mechanics: { rollAngle: x[12], rollRate: x[13], leftStrokeVelocity: x[1], rightStrokeVelocity: x[7],
        leftPitchVelocity: x[3], rightPitchVelocity: x[9], oscillatorEnergy,
        cumulativePowerWork: this.cumulativePowerWork, cumulativeDissipation: this.cumulativeDissipation, limitContacts: this.limitContacts },
      neural: { motorCommandsById: { ...this.commands }, powerActivation: { left: { DLM: this.activation.left.DLM, DVM: this.activation.left.DVM },
        right: { DLM: this.activation.right.DLM, DVM: this.activation.right.DVM } },
        effectivePower: { left: Math.min(this.activation.left.DLM, this.activation.left.DVM), right: Math.min(this.activation.right.DLM, this.activation.right.DVM) },
        steeringActivation: { left: this.activation.left.b1, right: this.activation.right.b1 }, rollSensorSignal: this.sensor,
        signalUnits: 'dimensionless direct-MN interventions and idealized roll-rate measurement; not spikes',
        neuralPropagationSimulated: false, exactSensorRootTuningValidated: false } };
  }
}

export function runFlightTrial({ mapping, pools = null, condition = 'power', seed = 260927, duration = .8,
  recordEvery = 5, parameters = {} } = {}) {
  if (!FLIGHT_CONDITIONS.some((c) => c.id === condition)) throw new Error('Unknown flight-test condition');
  if (!(duration > 0) || !Number.isInteger(recordEvery) || recordEvery < 1) throw new Error('Invalid trial timing');
  const model = new FlightModel({ mapping, pools, parameters, seed }); const p = model.parameters;
  const steps = Math.round(duration / p.dt); const frames = [model.snapshot()];
  const strokes = { left: [], right: [] }; const crossings = { left: [], right: [] };
  let peakRoll = 0; let sumRollRateSquared = 0; let sumForceLeft = 0; let sumForceRight = 0; let measuredSteps = 0;
  let finalWindowStrokeSquared = 0; let finalWindowCount = 0; let peakSensor = 0; let peakDifferential = 0;
  const lastStroke = { left: model.state[0], right: model.state[6] };
  for (let i = 0; i < steps; i++) {
    const time = i * p.dt; const commands = {};
    const powerOn = condition !== 'passive' && !(condition === 'power_off' && time >= duration / 2);
    const steering = { left: p.steeringBaseline, right: p.steeringBaseline };
    if (time >= duration * .3) {
      if (condition === 'left_steering') steering.left = .85;
      if (condition === 'right_steering') steering.right = .85;
    }
    if (condition === 'roll_feedback') {
      steering.left = clamp(p.steeringBaseline + p.feedbackGain * model.sensor);
      steering.right = clamp(p.steeringBaseline - p.feedbackGain * model.sensor);
    }
    for (const side of SIDES) {
      for (const id of model.pools[side].DLM) commands[id] = powerOn ? p.tonicPower : 0;
      for (const id of model.pools[side].DVM) commands[id] = powerOn && condition !== 'power_pool_ablation' ? p.tonicPower : 0;
      for (const id of model.pools[side].b1) commands[id] = steering[side];
    }
    const disturbed = ['roll_open', 'roll_feedback'].includes(condition);
    const external = disturbed && time >= duration * .5 && time < duration * .5 + .012 ? .08 : 0;
    model.step({ motorCommandsById: commands, externalRollTorque: external });
    const force = model.forces(); peakRoll = Math.max(peakRoll, Math.abs(model.state[12]));
    peakSensor = Math.max(peakSensor, Math.abs(model.sensor));
    peakDifferential = Math.max(peakDifferential, Math.abs(model.activation.left.b1 - model.activation.right.b1));
    if (time >= duration * .5) { sumRollRateSquared += model.state[13] ** 2; sumForceLeft += force.left; sumForceRight += force.right; measuredSteps++; }
    if (time >= duration * .8) { finalWindowStrokeSquared += model.state[0] ** 2 + model.state[6] ** 2; finalWindowCount += 2; }
    for (const [index, side] of SIDES.entries()) {
      const stroke = model.state[index * 6];
      if (time >= duration * .5) {
        strokes[side].push(stroke);
        if (stroke >= 0 && lastStroke[side] < 0) crossings[side].push(model.time);
      }
      lastStroke[side] = stroke;
    }
    if ((i + 1) % recordEvery === 0 || i === steps - 1) frames.push(model.snapshot());
  }
  const frequency = (side) => {
    const c = crossings[side]; const rms = Math.sqrt(mean(strokes[side].map((x) => x * x)));
    return c.length >= 3 && rms > .01 && Math.sqrt(finalWindowStrokeSquared / finalWindowCount) > .01
      ? (c.length - 1) / (c.at(-1) - c[0]) : null;
  };
  return { schema: 'fly.flight-roll-trial.v1', condition, seed, duration, parameters: p,
    parameterProvenance: FLIGHT_PARAMETER_PROVENANCE, pools: model.pools, frames,
    recordingSampleRateHz: 1 / (p.dt * recordEvery), integrationSteps: steps,
    summary: { peakRollRadians: peakRoll, finalRollRadians: model.state[12], rmsRollRate: Math.sqrt(sumRollRateSquared / measuredSteps),
      meanForceLeft: sumForceLeft / measuredSteps, meanForceRight: sumForceRight / measuredSteps,
      finalStrokeRms: Math.sqrt(finalWindowStrokeSquared / finalWindowCount),
      wingFrequencyHz: { left: frequency('left'), right: frequency('right') }, peakSensorSignal: peakSensor,
      maxSteeringActivationDifference: peakDifferential, finalOscillatorEnergy: frames.at(-1).mechanics.oscillatorEnergy,
      limitContacts: model.limitContacts, cumulativePowerWork: model.cumulativePowerWork, cumulativeDissipation: model.cumulativeDissipation },
    provenance: { sourceNamespace: model.pools.namespace, exactAnatomicalMotorIds: true,
      dynamics: 'coupled second-order mechanical oscillators; tonic power reduces damping, nonlinear damping limits amplitude',
      drive: 'direct imposed normalized motor commands, no neural spike or full-brain simulation',
      steering: 'b1 target identity is sourced; signed effect on transmission gain is an explicit ± hypothesis',
      feedback: 'idealized delayed roll-rate sensor drives direct b1 commands; no claimed biological sensor-to-MN synaptic reconstruction',
      halteres: 'passive mechanical coupling to stroke; exact sensor tuning and haltere motor activation are not modeled',
      forceUnits: 'arbitrary model units; no SI mass/force conversion or weight-support validation',
      prescribedPeriodicInput: false, sensoryEdgesSimulated: false, neuralPropagationSimulated: false,
      freeFlight: false, biologicalCalibration: false, originalGraphModified: false,
      references: ['https://www.nature.com/articles/s41586-023-06099-0', 'https://www.nature.com/articles/s41586-023-06606-3',
        'https://github.com/TuragaLab/flybody/blob/main/flybody/fruitfly/assets/fruitfly.xml'] } };
}
