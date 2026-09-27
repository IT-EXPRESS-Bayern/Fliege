import { CONTROL_KIND } from './control.mjs';

// Research prototype: abstract activity populations, not FlyWire neurons.
// Parameters and the arena transduction below are hypotheses, not fitted physiology.
const clamp = (value, lo = 0, hi = 1) => Math.max(lo, Math.min(hi, value));
const sigmoid = (value) => 1 / (1 + Math.exp(-value));

function rayDistance(x, z, heading, radius) {
  const dx = Math.sin(heading);
  const dz = Math.cos(heading);
  const projection = x * dx + z * dz;
  const discriminant = projection * projection + radius * radius - x * x - z * z;
  return Math.max(0, -projection + Math.sqrt(Math.max(0, discriminant)));
}

/** Minimal closed-loop spontaneous-behavior model with no task or target position.
 *
 * Four interacting rate units represent locomotion, left and right steering,
 * and grooming. Seeded endogenous fluctuations enter each unit. Slow internal
 * states retain a history of activity. Three body-relative wall rays provide
 * feedback from the simple arena. None of these units map to specific neurons.
 */
export class AutonomousController {
  constructor(seed = 0x5eed1234) {
    if (!Number.isInteger(seed) || seed < 0 || seed > 0xffffffff) {
      throw new RangeError('Seed must be a uint32');
    }
    this.seed = seed >>> 0;
    this.randomState = this.seed || 1;
    this.time = 0;
    this.rates = { walk: 0.55, left: 0.12, right: 0.12, groom: 0.06 };
    this.noise = { walk: 0, left: 0, right: 0, groom: 0 };
    this.arousal = 0.57;
    this.fatigue = 0.12;
    this.groomNeed = 0.38;
    this.lastWall = { ahead: 0, left: 0, right: 0 };
    this.lastControl = null;
  }

  random() {
    let value = this.randomState;
    value ^= value << 13;
    value ^= value >>> 17;
    value ^= value << 5;
    this.randomState = value >>> 0;
    return (this.randomState + 1) / 4294967297;
  }

  gaussian() {
    return Math.sqrt(-2 * Math.log(this.random())) * Math.cos(2 * Math.PI * this.random());
  }

  wallSignals({ x, z, yaw, arenaRadius }) {
    const radius = arenaRadius - 0.32;
    const sense = (angle) => clamp((2.1 - rayDistance(x, z, yaw + angle, radius)) / 2.1);
    return { ahead: sense(0), left: sense(-0.72), right: sense(0.72) };
  }

  next(observation, dt, timestampMs) {
    if (!observation || !['x', 'z', 'yaw', 'arenaRadius'].every(
      key => Number.isFinite(observation[key])) || observation.arenaRadius <= 0.32 ||
      !Number.isFinite(dt) || dt < 0 || dt > 0.1 || !Number.isFinite(timestampMs)) {
      throw new RangeError('Invalid body observation, time step or timestamp');
    }

    const wall = this.wallSignals(observation);
    this.lastWall = wall;
    const count = Math.ceil(dt / 0.02);
    const h = count ? dt / count : 0;
    for (let step = 0; step < count; step++) {
      const old = { ...this.rates };
      // Colored spontaneous fluctuations persist beyond a single animation frame.
      for (const unit of Object.keys(this.noise)) {
        this.noise[unit] += -this.noise[unit] * h / 1.2 +
          0.68 * Math.sqrt(h) * this.gaussian();
      }
      this.arousal = clamp(this.arousal + h * (0.042 * (0.58 - this.arousal) -
        0.021 * old.walk + 0.012 * (old.groom - 0.1)));
      this.fatigue = clamp(this.fatigue + h * (0.025 * old.walk -
        0.048 * (1 - old.walk) * this.fatigue));
      this.groomNeed = clamp(this.groomNeed + h *
        (0.022 - 0.18 * Math.max(0, old.groom - 0.2)));

      const walkDrive = -0.52 + 2.5 * this.arousal - 1.75 * this.fatigue -
        1.25 * old.groom - 0.48 * wall.ahead + 0.4 * old.walk + this.noise.walk;
      const leftDrive = -1.25 + 2.7 * wall.right + 1.25 * wall.ahead +
        0.9 * old.left - 1.35 * old.right + this.noise.left;
      const rightDrive = -1.25 + 2.7 * wall.left + 1.25 * wall.ahead +
        0.9 * old.right - 1.35 * old.left + this.noise.right;
      const groomDrive = -4.0 + 5.0 * this.groomNeed + 2.0 * old.groom -
        0.8 * old.walk + this.noise.groom;
      const target = {
        walk: sigmoid(walkDrive), left: sigmoid(leftDrive),
        right: sigmoid(rightDrive), groom: sigmoid(groomDrive),
      };
      for (const unit of Object.keys(this.rates)) {
        const tau = unit === 'walk' ? 0.55 : unit === 'groom' ? 0.85 : 0.36;
        this.rates[unit] = clamp(old[unit] + (target[unit] - old[unit]) * h / tau);
      }
      this.time += h;
    }

    const groom = clamp((this.rates.groom - 0.12) * 1.55);
    const forward = clamp((this.rates.walk - 0.08) * 1.25 * (1 - 0.8 * groom), 0, 0.92);
    const turn = clamp((this.rates.right - this.rates.left) * 2.8, -1, 1);
    const activity = groom > 0.55 ? 'Putzen' : forward < 0.16 ? 'Ruhen' :
      Math.abs(turn) > 0.32 ? 'Wenden' : 'Laufen';
    this.lastControl = {
      kind: CONTROL_KIND, timestampMs, forward, turn,
      wing: 0.03 + 0.14 * forward, groom, activity,
    };
    return this.lastControl;
  }

  snapshot() {
    return {
      time: this.time, rates: { ...this.rates }, arousal: this.arousal,
      fatigue: this.fatigue, groomNeed: this.groomNeed,
      wall: { ...this.lastWall }, activity: this.lastControl?.activity ?? 'Laufen',
    };
  }
}
