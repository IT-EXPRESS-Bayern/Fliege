/**
 * Kinematic body, not a muscle/force simulator. Units are arbitrary model units.
 * Foot contacts are geometric constraints; joint angles are measured from the
 * rendered model and have no FlyWire root IDs or calibrated receptor gains.
 */
export const BODY_SCHEMA = 'fly.body-observation.v1';
export const LEG_SPECS = Object.freeze([-1, 1].flatMap((side) => [0, 1, 2].map((index) =>
  Object.freeze({ id: `${side === -1 ? 'L' : 'R'}${['F', 'M', 'H'][index]}`, side, index,
    hip: [side * 0.245, -0.105, 0.29 - index * 0.29],
    foot: [side * [0.71, 0.87, 0.76][index], 0, [0.76, -0.02, -0.91][index]],
    lengths: [0.17, [0.46, 0.49, 0.51][index], [0.49, 0.52, 0.55][index], 0.14],
    offset: (index + (side === -1 ? 0 : 1)) % 2 * 0.5 }))));

const clamp = (n, a, b) => Math.max(a, Math.min(b, n));
const add = (a, b) => a.map((v, i) => v + b[i]);
const sub = (a, b) => a.map((v, i) => v - b[i]);
const mul = (a, s) => a.map((v) => v * s);
const dot = (a, b) => a.reduce((s, v, i) => s + v * b[i], 0);
const norm = (a) => Math.hypot(...a);
const unit = (a) => mul(a, 1 / (norm(a) || 1));
const lerp = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
const smooth = (t) => t * t * t * (t * (t * 6 - 15) + 10);
const wrap = (a) => Math.atan2(Math.sin(a), Math.cos(a));
const angle = (a, b) => Math.acos(clamp(dot(unit(a), unit(b)), -1, 1));
const rotateX = ([x, y, z], a) => [x, y * Math.cos(a) - z * Math.sin(a), y * Math.sin(a) + z * Math.cos(a)];
const rotateY = ([x, y, z], a) => [x * Math.cos(a) + z * Math.sin(a), y, -x * Math.sin(a) + z * Math.cos(a)];
const rotateZ = ([x, y, z], a) => [x * Math.cos(a) - y * Math.sin(a), x * Math.sin(a) + y * Math.cos(a), z];

export function localToWorld(point, pose) {
  return add(rotateY(rotateX(rotateZ(point, pose.roll || 0), pose.pitch || 0), pose.yaw),
    [pose.x, pose.height || 0, pose.z]);
}
export function worldToLocal(point, pose) {
  return rotateZ(rotateX(rotateY(sub(point, [pose.x, pose.height || 0, pose.z]), -pose.yaw),
    -(pose.pitch || 0)), -(pose.roll || 0));
}

/** Two-bone inverse kinematics after the coxa, followed by a short tarsus. */
export function solveLeg(spec, footLocal) {
  const hip = [...spec.hip];
  const coxaDirection = unit([spec.side, -0.26, (1 - spec.index) * 0.24]);
  const shoulder = add(hip, mul(coxaDirection, spec.lengths[0]));
  const tarsusDirection = unit([spec.side * 0.12, -1, -0.27]);
  const desiredAnkle = sub(footLocal, mul(tarsusDirection, spec.lengths[3]));
  const delta = sub(desiredAnkle, shoulder);
  const direction = unit(delta);
  const [, femurLength, tibiaLength] = spec.lengths;
  const distance = clamp(norm(delta), Math.abs(femurLength - tibiaLength) + 1e-5, femurLength + tibiaLength - 1e-5);
  const ankle = add(shoulder, mul(direction, distance));
  const projection = (femurLength ** 2 - tibiaLength ** 2 + distance ** 2) / (2 * distance);
  const height = Math.sqrt(Math.max(0, femurLength ** 2 - projection ** 2));
  const preference = [spec.side, 0.65, (1 - spec.index) * 0.52];
  let bend = sub(preference, mul(direction, dot(preference, direction)));
  if (norm(bend) < 1e-6) bend = sub([0, 0, 1], mul(direction, direction[2]));
  const knee = add(add(shoulder, mul(direction, projection)), mul(unit(bend), height));
  const foot = add(ankle, mul(tarsusDirection, spec.lengths[3]));
  const femur = sub(knee, shoulder);
  const tibia = sub(ankle, knee);
  return { points: [hip, shoulder, knee, ankle, foot], reachError: norm(sub(foot, footLocal)),
    // Geometric observables in our coordinate convention, not FlyGym joint coordinates.
    angles: { coxaAzimuth: Math.atan2(femur[2], femur[0] * spec.side),
      femurElevation: Math.atan2(femur[1], Math.hypot(femur[0], femur[2])),
      femurTibia: Math.PI - angle(mul(femur, -1), tibia),
      tibiaTarsus: Math.PI - angle(mul(tibia, -1), tarsusDirection) } };
}

export class ArticulatedBody {
  constructor(pose = { x: 0, z: 0, yaw: 0 }) { this.reset(pose); }
  reset(pose) {
    this.time = 0;
    this.cycle = 0;
    this.previous = { ...pose };
    this.velocity = { x: 0, z: 0, yaw: 0 };
    this.pose = { ...pose, height: 0.65, pitch: 0, roll: 0 };
    this.frequency = 0;
    this.groom = 0;
    this.legs = LEG_SPECS.map((spec) => ({ spec, mode: 'stance',
      target: localToWorld(spec.foot, { ...pose, height: 0 }), progress: 0,
      solution: null, angularVelocity: {}, lastAngles: null, contact: true }));
    this.resolve(1 / 60);
  }
  nominalFoot(spec, ahead = 0) {
    return localToWorld(spec.foot, { x: this.pose.x + this.velocity.x * ahead,
      z: this.pose.z + this.velocity.z * ahead, yaw: this.pose.yaw + this.velocity.yaw * ahead, height: 0 });
  }
  beginSwing(leg, duration, target, lift = 0.16) {
    leg.mode = 'swing';
    leg.start = [...leg.target];
    leg.landing = target;
    leg.progress = 0;
    leg.duration = duration;
    leg.lift = lift;
  }
  update(pose, control, dt) {
    if (!(dt > 0 && dt <= 0.1)) return this.snapshot();
    this.time += dt;
    const measured = { x: (pose.x - this.previous.x) / dt,
      z: (pose.z - this.previous.z) / dt, yaw: wrap(pose.yaw - this.previous.yaw) / dt };
    for (const key of ['x', 'z', 'yaw']) this.velocity[key] += (measured[key] - this.velocity[key]) * (1 - Math.exp(-dt * 16));
    this.previous = { ...pose };
    const speed = Math.hypot(this.velocity.x, this.velocity.z);
    const locomotion = Math.hypot(speed, this.velocity.yaw * 0.62);
    const moving = locomotion > 0.035;
    const frequency = moving ? clamp(1.35 + locomotion * 2.2, 1.35, 5.5) : 0;
    this.frequency = frequency;
    this.groom += ((control.groom || 0) * (moving ? 0 : 1) - this.groom) * (1 - Math.exp(-dt * 6));
    const previousCycle = this.cycle;
    if (moving) this.cycle += frequency * dt;
    const phase = this.cycle * Math.PI * 2;
    const activity = clamp(locomotion, 0, 1);
    const targetPitch = -speed * 0.018 + Math.sin(phase * 2) * activity * 0.012;
    const targetRoll = -this.velocity.yaw * 0.025 + Math.sin(phase) * activity * 0.025;
    this.pose = { ...pose, height: 0.65 + Math.cos(phase * 2) * 0.012 * activity,
      pitch: this.pose.pitch + (targetPitch - this.pose.pitch) * (1 - Math.exp(-dt * 12)),
      roll: this.pose.roll + (targetRoll - this.pose.roll) * (1 - Math.exp(-dt * 12)) };
    const duty = 0.64;
    const supportReady = this.legs.filter((leg) => leg.spec.index !== 0).every((leg) => leg.mode === 'stance');
    const frontRecovery = this.legs.some((leg) => leg.spec.index === 0 && (leg.mode === 'groom' || leg.returningFromGroom));
    for (const leg of this.legs) {
      const { spec } = leg;
      const localPhase = (this.cycle + spec.offset) % 1;
      const priorPhase = (previousCycle + spec.offset) % 1;
      if (spec.index === 0 && this.groom > 0.07 && !moving && supportReady) {
        const wipe = Math.sin(this.time * 16 + spec.side * 0.4);
        const groomingTarget = localToWorld([spec.side * (0.22 + wipe * 0.05),
          -0.025 + Math.cos(this.time * 16) * 0.07, 0.72 + wipe * 0.065], this.pose);
        leg.mode = 'groom';
        leg.target = lerp(leg.target, groomingTarget, 1 - Math.exp(-dt * 14));
      } else {
        if (leg.mode === 'groom') {
          this.beginSwing(leg, 0.24, this.nominalFoot(spec), 0.05);
          leg.returningFromGroom = true;
        }
        if (leg.mode === 'stance' && moving && !frontRecovery && localPhase >= duty && priorPhase < duty) {
          const duration = (1 - duty) / frequency;
          this.beginSwing(leg, duration, this.nominalFoot(spec, duration + duty / frequency * 0.48),
            0.13 + speed * 0.035);
        }
        if (leg.mode === 'swing') {
          leg.progress = clamp(leg.progress + dt / leg.duration, 0, 1);
          const u = leg.progress;
          leg.target = lerp(leg.start, leg.landing, smooth(u));
          leg.target[1] += leg.lift * 16 * u * u * (1 - u) * (1 - u);
          if (u >= 1) { leg.mode = 'stance'; leg.target = [...leg.landing]; leg.returningFromGroom = false; }
        }
      }
    }
    // Resume the tripod whose rear foot would otherwise remain too far behind.
    // Gait phases skipped while the front feet returned must not delay liftoff
    // for a whole extra cycle.
    if (frontRecovery && this.legs.every((leg) => leg.mode !== 'groom' && !leg.returningFromGroom)) {
      this.cycle = Math.ceil(this.cycle) + duty - 1e-6;
    }
    this.resolve(dt);
    return this.snapshot();
  }
  resolve(dt) {
    for (const leg of this.legs) {
      leg.solution = solveLeg(leg.spec, worldToLocal(leg.target, this.pose));
      leg.contact = leg.mode === 'stance' && leg.solution.reachError < 0.01 && Math.abs(leg.target[1]) < 1e-6;
      for (const [name, value] of Object.entries(leg.solution.angles)) {
        leg.angularVelocity[name] = leg.lastAngles ? wrap(value - leg.lastAngles[name]) / dt : 0;
      }
      leg.lastAngles = { ...leg.solution.angles };
    }
  }
  snapshot() {
    return { schema: BODY_SCHEMA, timeSeconds: this.time,
      model: 'kinematic-articulated-v1', units: { length: 'model-unit', angle: 'radian', time: 'second' },
      pose: { ...this.pose }, velocity: { ...this.velocity }, gaitFrequencyHz: this.frequency,
      contacts: this.legs.filter((leg) => leg.contact).length,
      contactForces: null, biologicalCalibration: false,
      legs: this.legs.map((leg) => ({ id: leg.spec.id, phase: leg.mode, contact: leg.contact,
        footWorld: localToWorld(leg.solution.points[4], this.pose),
        footTargetWorld: [...leg.target], jointAngles: { ...leg.solution.angles },
        jointVelocity: { ...leg.angularVelocity }, reachError: leg.solution.reachError,
        pointsLocal: leg.solution.points.map((point) => [...point]) })) };
  }
}
