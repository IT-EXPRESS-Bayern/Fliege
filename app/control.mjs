/**
 * Small, deliberately non-biological control boundary for the 3D demonstrator.
 * A later connectome worker may submit the same fly.control.v1 frames.
 */
export const CONTROL_KIND = 'fly.control.v1';

const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
const wrap = (angle) => Math.atan2(Math.sin(angle), Math.cos(angle));

export function normalizeControlFrame(input) {
  if (!input || input.kind !== CONTROL_KIND || typeof input !== 'object') {
    throw new TypeError(`Expected a ${CONTROL_KIND} object`);
  }

  const channels = ['forward', 'turn', 'wing', 'groom'];
  for (const channel of channels) {
    if (!Number.isFinite(input[channel])) {
      throw new TypeError(`${channel} must be a finite number`);
    }
  }
  if (!Number.isFinite(input.timestampMs)) {
    throw new TypeError('timestampMs must be a finite number');
  }

  return {
    kind: CONTROL_KIND,
    timestampMs: input.timestampMs,
    forward: clamp(input.forward, 0, 1),
    turn: clamp(input.turn, -1, 1),
    wing: clamp(input.wing, 0, 1),
    groom: clamp(input.groom, 0, 1),
  };
}

export class ExternalControlInbox {
  constructor(maxAgeMs = 350) {
    this.maxAgeMs = maxAgeMs;
    this.frame = null;
  }

  receive(input) {
    this.frame = normalizeControlFrame(input);
  }

  sample(nowMs) {
    if (!this.frame || Math.abs(nowMs - this.frame.timestampMs) > this.maxAgeMs) {
      return null;
    }
    return this.frame;
  }

  clear() {
    this.frame = null;
  }
}

export class DemoController {
  constructor(seed = 0x5eed1234) {
    this.seed = seed >>> 0;
    this.state = this.seed || 1;
    this.time = 0;
    this.nextChoice = 0;
    this.activity = 'Erkundung';
    this.turnBias = 0;
  }

  random() {
    // Xorshift32 keeps autonomous choices reproducible for a given reset.
    let value = this.state;
    value ^= value << 13;
    value ^= value >>> 17;
    value ^= value << 5;
    this.state = value >>> 0;
    return this.state / 4294967296;
  }

  next(observation, dt, timestampMs) {
    this.time += dt;
    if (this.time >= this.nextChoice) {
      const draw = this.random();
      this.activity = draw < 0.12 ? 'Putzen' : draw < 0.24 ? 'Innehalten' : 'Erkundung';
      this.turnBias = (this.random() * 2 - 1) * 0.5;
      this.nextChoice = this.time + 1.4 + this.random() * 2.8;
    }

    const { x, z, yaw, arenaRadius } = observation;
    const distance = Math.hypot(x, z);
    const edgeStart = arenaRadius - 1.8;
    let edgeTurn = 0;
    if (distance > edgeStart) {
      const homeHeading = Math.atan2(-x, -z);
      const strength = clamp((distance - edgeStart) / 0.9, 0, 1);
      edgeTurn = clamp(wrap(homeHeading - yaw) * 1.5, -1, 1) * strength;
    }

    const gentleWander = Math.sin(this.time * 0.57) * 0.22 + this.turnBias;
    const turn = clamp(gentleWander * (1 - Math.abs(edgeTurn)) + edgeTurn, -1, 1);
    const forward = this.activity === 'Erkundung' ? 0.66 : this.activity === 'Putzen' ? 0.05 : 0.02;
    return {
      kind: CONTROL_KIND,
      timestampMs,
      forward,
      turn,
      wing: this.activity === 'Erkundung' ? 0.3 : 0.08,
      groom: this.activity === 'Putzen' ? 1 : 0,
      activity: this.activity,
    };
  }
}
