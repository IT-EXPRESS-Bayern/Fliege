import { LEG_SPECS, solveLeg, localToWorld } from './body-kinematics.mjs';

export const MOTOR_PARAMETERS = Object.freeze({ schema: 'fly.antagonistic-joint-demo.v1',
  angleConvention: 'bend angle: straight=0; increasing=flexion; not anatomical inner angle',
  units: 'seconds/radians; torque, inertia, activation and stiffness are uncalibrated model units',
  biologicalCalibration: false, activationTau: .07, inertia: 1, torqueGain: 18,
  passiveStiffness: 7, coactivationStiffness: 45, passiveDamping: 5, coactivationDamping: 8,
  minAngle: 10 * Math.PI / 180, maxAngle: 165 * Math.PI / 180, fixedBodyHeight: 1.35 });
export const ACTIONS = Object.freeze({ flex_femur_tibia_joint: 'flexor', extend_femur_tibia_joint: 'extensor' });
const clamp = (n, a, b) => Math.max(a, Math.min(b, n));
const add = (a, b) => a.map((v, i) => v + b[i]);
const sub = (a, b) => a.map((v, i) => v - b[i]);
const mul = (a, n) => a.map((v) => v * n);
const dot = (a, b) => a.reduce((s, v, i) => s + v * b[i], 0);
const norm = (a) => Math.hypot(...a);
const unit = (a) => mul(a, 1 / (norm(a) || 1));
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const rotateAxis = (v, axis, angle) => add(add(mul(v, Math.cos(angle)), mul(cross(axis, v), Math.sin(angle))), mul(axis, dot(axis, v) * (1 - Math.cos(angle))));

export function makeMotorPools(motors) {
  const pools = Object.fromEntries(LEG_SPECS.map((s) => [s.id, { flexor: [], extensor: [] }]));
  const seen = new Map();
  for (const motor of motors) {
    const id = motor.banc_888_id || motor.id;
    if (typeof id !== 'string') throw new Error('Motor IDs must remain strings');
    const action = ACTIONS[motor.cell_function_detailed]; const leg = motor.candidate_model_leg;
    if (!action || !pools[leg]) continue;
    const role = `${leg}:${action}`;
    if (seen.has(id) && seen.get(id) !== role) throw new Error(`Conflicting motor assignment: ${id}`);
    if (seen.has(id)) continue;
    seen.set(id, role); pools[leg][action].push(id);
  }
  return pools;
}

/** Pool normalization is a demonstration assumption. Ablation never changes denominator. */
export function poolActivation(ids, input, ablated = new Set()) {
  const unique = [...new Set(ids)];
  if (!unique.length) return 0;
  return unique.reduce((sum, id) => sum + (ablated.has(id) ? 0 : clamp(Number(input[id]) || 0, 0, 1)), 0) / unique.length;
}

export class JointMotorBody {
  constructor(pools, parameters = {}) {
    this.parameters = { ...MOTOR_PARAMETERS, ...parameters }; this.pools = pools; this.time = 0;
    this.legs = LEG_SPECS.map((spec) => {
      // Only initialization uses the arena rest shape. Every motor update uses forward kinematics.
      const base = solveLeg(spec, [spec.foot[0], -.65, spec.foot[2]]);
      const femur = sub(base.points[2], base.points[1]); const tibia = sub(base.points[3], base.points[2]);
      return { spec, base, axis: unit(cross(femur, tibia)), q: base.angles.femurTibia,
        rest: base.angles.femurTibia, velocity: 0, flexor: 0, extensor: 0, coactivation: 0,
        driveTorque: 0, externalTorque: 0, stiffness: this.parameters.passiveStiffness, damping: this.parameters.passiveDamping };
    });
  }
  step(input = {}, dt = .002, ablated = new Set(), disturbance = {}) {
    if (!(dt > 0 && dt <= .01)) throw new Error('Motor integration requires 0 < dt <= 10ms');
    const p = this.parameters; this.time += dt;
    const blend = 1 - Math.exp(-dt / p.activationTau);
    for (const leg of this.legs) {
      const pools = this.pools[leg.spec.id] || { flexor: [], extensor: [] };
      leg.flexor += (poolActivation(pools.flexor, input, ablated) - leg.flexor) * blend;
      leg.extensor += (poolActivation(pools.extensor, input, ablated) - leg.extensor) * blend;
      leg.coactivation = Math.min(leg.flexor, leg.extensor);
      leg.stiffness = p.passiveStiffness + p.coactivationStiffness * leg.coactivation;
      leg.damping = p.passiveDamping + p.coactivationDamping * leg.coactivation;
      leg.driveTorque = p.torqueGain * (leg.flexor - leg.extensor);
      leg.externalTorque = Number(disturbance[leg.spec.id]) || 0;
      const net = leg.driveTorque + leg.externalTorque - leg.stiffness * (leg.q - leg.rest) - leg.damping * leg.velocity;
      leg.velocity += net / p.inertia * dt; leg.q += leg.velocity * dt;
      if (leg.q < p.minAngle) { leg.q = p.minAngle; leg.velocity = Math.max(0, leg.velocity); }
      if (leg.q > p.maxAngle) { leg.q = p.maxAngle; leg.velocity = Math.min(0, leg.velocity); }
    }
    return this.snapshot();
  }
  snapshot() {
    const pose = { x: 0, z: 0, yaw: 0, height: this.parameters.fixedBodyHeight, pitch: 0, roll: 0 };
    return { schema: 'fly.body-observation.v1', model: 'antagonistic-fixed-body-demo',
      timeSeconds: this.time, pose, velocity: { x: 0, z: 0, yaw: 0 }, gaitFrequencyHz: 0,
      contacts: 0, contactForces: null, biologicalCalibration: false,
      legs: this.legs.map((leg) => {
        const points = leg.base.points.map((p) => [...p]); const delta = leg.q - leg.rest;
        points[3] = add(points[2], rotateAxis(sub(leg.base.points[3], leg.base.points[2]), leg.axis, delta));
        points[4] = add(points[3], rotateAxis(sub(leg.base.points[4], leg.base.points[3]), leg.axis, delta));
        const foot = localToWorld(points[4], pose);
        return { id: leg.spec.id, pointsLocal: points, footWorld: foot, footTargetWorld: [...foot],
          phase: 'suspended', contact: false, reachError: 0,
          jointAngles: { ...leg.base.angles, femurTibia: leg.q },
          jointVelocity: { coxaAzimuth: 0, femurElevation: 0, femurTibia: leg.velocity, tibiaTarsus: 0 },
          motor: { flexor: leg.flexor, extensor: leg.extensor, coactivation: leg.coactivation,
            driveTorque: leg.driveTorque, externalTorque: leg.externalTorque, stiffness: leg.stiffness,
            damping: leg.damping, restAngle: leg.rest, limitContact: leg.q === this.parameters.minAngle || leg.q === this.parameters.maxAngle } };
      }) };
  }
}

export const MOTOR_TESTS = Object.freeze([
  { id: 'baseline', label: 'Nullkontrolle', description: 'Keine Motoraktivierung, kein Störmoment.' },
  { id: 'flexor', label: 'Beuger aktivieren', description: 'Direkte Aktivierung der ausgewählten Beuger-Motorneuronen.' },
  { id: 'extensor', label: 'Strecker aktivieren', description: 'Direkte Aktivierung der ausgewählten Strecker-Motorneuronen.' },
  { id: 'ablation', label: 'Beuger aktivieren + ausschalten', description: 'Gleicher Eingriff wie Beuger; diese Motorneuronen werden auf null gesetzt.' },
  { id: 'sham', label: 'Beuger + Schein-Ausschaltung', description: 'Beuger aktiv; gleich viele andere Motor-IDs werden ausgeschaltet.' },
  { id: 'coactivation', label: 'Beuger und Strecker gemeinsam', description: 'Gleiche Poolaktivierung; Nettomoment null, Aktivität und Steifigkeit bleiben messbar.' },
  { id: 'passive_disturbance', label: 'Störmoment · passives Gelenk', description: 'Kurzes definiertes Störmoment ohne Muskelaktivierung.' },
  { id: 'coactivation_disturbance', label: 'Störmoment · Gegenspieler aktiv', description: 'Dasselbe Störmoment bei gemeinsamer Aktivierung beider Gegenspieler.' },
]);

export function motorTrial(pools, { leg = 'LF', condition = 'flexor', amplitude = .65, selection = 'pool', duration = 3, dt = .002 } = {}) {
  if (!pools[leg]) throw new Error('Unknown leg');
  if (!MOTOR_TESTS.some((t) => t.id === condition)) throw new Error('Unknown condition');
  const body = new JointMotorBody(pools); const baseline = body.snapshot();
  const choose = (ids) => selection === 'pool' ? ids : ids.filter((id) => id === selection);
  const flexors = choose(pools[leg].flexor); const extensors = choose(pools[leg].extensor);
  const coactivation = condition.startsWith('coactivation');
  // Coactivation tests use both complete pools, since a single ID cannot be both antagonists.
  const driveFlexors = coactivation ? pools[leg].flexor : flexors;
  const driveExtensors = coactivation ? pools[leg].extensor : extensors;
  const selectedIds = condition === 'extensor' ? driveExtensors : driveFlexors;
  const allIds = [...new Set(Object.values(pools).flatMap((p) => [...p.flexor, ...p.extensor]))].sort();
  const sham = allIds.filter((id) => !selectedIds.includes(id)).slice(0, selectedIds.length);
  const ablated = new Set(condition === 'ablation' ? selectedIds : condition === 'sham' ? sham : []);
  const frames = [{ tMs: 0, body: baseline }]; let peakDeviation = 0; let angleTravel = 0;
  let previousAngle = baseline.legs.find((l) => l.id === leg).jointAngles.femurTibia;
  const rest = previousAngle;
  for (let step = 1; step <= Math.round(duration / dt); step++) {
    const time = step * dt; const on = time >= .4 && time <= 2.4;
    const input = {};
    if (on && (['flexor', 'ablation', 'sham'].includes(condition) || coactivation)) for (const id of driveFlexors) input[id] = amplitude;
    if (on && (condition === 'extensor' || coactivation)) for (const id of driveExtensors) input[id] = amplitude;
    const disturb = condition.endsWith('_disturbance') && time >= 1.2 && time < 1.3 ? { [leg]: 12 } : {};
    const snapshot = body.step(input, dt, ablated, disturb);
    const angle = snapshot.legs.find((l) => l.id === leg).jointAngles.femurTibia;
    peakDeviation = Math.max(peakDeviation, Math.abs(angle - rest)); angleTravel += Math.abs(angle - previousAngle); previousAngle = angle;
    frames.push({ tMs: time * 1000, body: snapshot });
  }
  return { frames, durationMs: duration * 1000, leg, condition, amplitude, selection,
    directlyDrivenIds: [...new Set([...(condition === 'extensor' || coactivation ? driveExtensors : []),
      ...(['flexor', 'ablation', 'sham'].includes(condition) || coactivation ? driveFlexors : [])])],
    ablatedIds: [...ablated], peakDeviationRadians: peakDeviation, cumulativeAngleTravelRadians: angleTravel,
    bodyTimeSeconds: body.time, parameters: { ...MOTOR_PARAMETERS },
    neuralPropagationSimulated: false, clinicalOrBiologicalValidation: false };
}
