import { ArticulatedBody } from './body-kinematics.mjs';

export const ADAPTER = Object.freeze({ schema: 'fly.assay-body-adapter.v1', rateWindowMs: 100,
  groomingFullScaleHz: 50, bodyTimeEqualsNeuralTime: true, biologicalCalibration: false });

export function groomingReadouts(scenario) {
  // Channel assignment comes from the assay manifest; only annotated aDNs qualify.
  return (scenario.readouts || []).filter((r) => ['groom', 'grooming'].includes(r.bodyChannel)
    && /aDN[12]/i.test(`${r.label || ''} ${r.role || ''}`));
}

/** Causal trailing mean per readout. The window includes silent pre-trial time. */
export function readoutRates(samples, ids, windowMs = ADAPTER.rateWindowMs) {
  if (!(windowMs > 0)) throw new Error('windowMs must be positive');
  const sums = Object.fromEntries(ids.map((id) => [id, 0]));
  let first = 0;
  let previousTime = -Infinity;
  return samples.map((sample, index) => {
    if (!Number.isFinite(sample.tMs) || sample.tMs < previousTime) throw new Error('Samples must have ordered finite tMs');
    previousTime = sample.tMs;
    for (const id of ids) sums[id] += Math.max(0, Number(sample.spikesByReadout?.[id]) || 0);
    while (first <= index && samples[first].tMs <= sample.tMs - windowMs) {
      for (const id of ids) sums[id] -= Math.max(0, Number(samples[first].spikesByReadout?.[id]) || 0);
      first++;
    }
    return Object.fromEntries(ids.map((id) => [id, sums[id] * 1000 / windowMs]));
  });
}

export function ratesToControl(rates, scenario) {
  const eligible = groomingReadouts(scenario);
  const meanHz = eligible.length ? eligible.reduce((s, r) => s + Math.max(0, Number(rates[r.id]) || 0), 0) / eligible.length : 0;
  return { forward: 0, turn: 0, wing: 0, groom: Math.max(0, Math.min(1, meanHz / ADAPTER.groomingFullScaleHz)),
    meanHz, channel: eligible.length ? 'grooming' : 'none', mappedIds: eligible.map((r) => r.id) };
}

function jointDifference(before, after) {
  let total = 0;
  for (let i = 0; i < after.legs.length; i++) for (const [key, value] of Object.entries(after.legs[i].jointAngles)) {
    const delta = value - before.legs[i].jointAngles[key];
    total += Math.abs(Math.atan2(Math.sin(delta), Math.cos(delta)));
  }
  return total;
}

/** Deterministic playback body simulation, independent of display frame rate. */
export function buildBodyReplay(scenario, trial) {
  const samples = trial.samples || [];
  const ids = (scenario.readouts || []).map((r) => r.id);
  const rates = readoutRates(samples, ids);
  const pose = { x: 0, z: 0, yaw: 0 };
  const body = new ArticulatedBody(pose);
  let prior = body.snapshot();
  let jointMotion = 0;
  let previousTimeMs = 0;
  const frames = [{ tMs: 0, body: prior, rates: Object.fromEntries(ids.map((id) => [id, 0])),
    control: ratesToControl({}, scenario), jointMotion: 0, totalReadoutSpikes: 0 }];
  let totalReadoutSpikes = 0;
  const perIdSpikes = Object.fromEntries(ids.map((id) => [id, 0]));
  for (let i = 0; i < samples.length; i++) {
    const sample = samples[i];
    const dt = (sample.tMs - previousTimeMs) / 1000;
    if (dt < 0 || dt > 0.1) throw new Error('Body replay requires ordered samples with gaps <=100ms');
    const control = ratesToControl(rates[i], scenario);
    for (const id of ids) {
      const count = Math.max(0, Number(sample.spikesByReadout?.[id]) || 0);
      perIdSpikes[id] += count; totalReadoutSpikes += count;
    }
    const snapshot = dt > 0 ? body.update(pose, control, dt) : body.snapshot();
    jointMotion += jointDifference(prior, snapshot);
    frames.push({ tMs: sample.tMs, body: snapshot, rates: rates[i], control, jointMotion, totalReadoutSpikes });
    prior = snapshot; previousTimeMs = sample.tMs;
  }
  const durationMs = trial.durationMs || samples.at(-1)?.tMs || 0;
  return { frames, durationMs, totalReadoutSpikes, perIdSpikes,
    meanReadoutHz: durationMs && ids.length ? totalReadoutSpikes / ids.length / (durationMs / 1000) : 0,
    jointMotion, mappedIds: groomingReadouts(scenario).map((r) => r.id),
    movement: jointMotion > 1e-8, adapter: ADAPTER };
}

export function makeActuatorControl() {
  const durationMs = 2400;
  const body = new ArticulatedBody({ x: 0, z: 0, yaw: 0 });
  let prior = body.snapshot(); let jointMotion = 0;
  const frames = [{ tMs: 0, body: prior, control: { groom: 0 }, rates: {}, jointMotion: 0 }];
  for (let tMs = 10; tMs <= durationMs; tMs += 10) {
    const control = { groom: tMs >= 300 && tMs <= 1700 ? 1 : 0, forward: 0, turn: 0, wing: 0 };
    const snapshot = body.update({ x: 0, z: 0, yaw: 0 }, control, 0.01);
    jointMotion += jointDifference(prior, snapshot);
    frames.push({ tMs, body: snapshot, control, rates: {}, jointMotion });
    prior = snapshot;
  }
  return { frames, durationMs, jointMotion, totalReadoutSpikes: null, meanReadoutHz: null,
    mappedIds: [], movement: true, technicalControl: true };
}

export function frameAt(replay, tMs) {
  let lo = 0; let hi = replay.frames.length - 1;
  while (lo < hi) { const mid = Math.ceil((lo + hi) / 2); if (replay.frames[mid].tMs <= tMs) lo = mid; else hi = mid - 1; }
  return replay.frames[lo];
}
