/** Contract for an explicitly hypothetical arena-to-neuron transduction. */
export const SENSOR_ADAPTER_SCHEMA = 'fly.sensor-adapter.v1';

export function validateSensorAdapterSpec(spec) {
  if (!spec || spec.schema !== SENSOR_ADAPTER_SCHEMA || typeof spec.dataset !== 'string' ||
      !spec.dataset.trim() || !spec.channels || typeof spec.channels !== 'object' ||
      typeof spec.encode !== 'function') {
    throw new TypeError(`Expected ${SENSOR_ADAPTER_SCHEMA} with dataset, channels and encode`);
  }
  const allowedIds = new Set();
  const provenance = {};
  for (const [channel, entry] of Object.entries(spec.channels)) {
    if (!channel.trim() || !entry || !Array.isArray(entry.rootIds) || !entry.rootIds.length ||
        !entry.rootIds.every((id) => typeof id === 'string' && /^[1-9]\d*$/.test(id))) {
      throw new TypeError(`Invalid sensor channel: ${channel}`);
    }
    let url;
    try { url = new URL(entry.evidenceUrl); } catch { throw new TypeError(`${channel} needs an evidence URL`); }
    if (url.protocol !== 'https:' || typeof entry.hypothesis !== 'string' ||
        entry.hypothesis.trim().length < 20) {
      throw new TypeError(`${channel} needs an HTTPS source and an explicit transduction hypothesis`);
    }
    for (const id of entry.rootIds) allowedIds.add(id);
    provenance[channel] = { evidenceUrl: entry.evidenceUrl,
      hypothesis: entry.hypothesis.trim(), rootIds: [...entry.rootIds] };
  }
  if (!allowedIds.size) throw new TypeError('At least one sensory root ID is required');
  return { dataset: spec.dataset, allowedIds, provenance, encode: spec.encode };
}

export function encodeSensoryInput(adapter, observation) {
  const output = adapter.encode({ ...observation });
  if (!output || typeof output !== 'object') throw new TypeError('Sensor adapter must return an input object');
  const stimuli = output.stimuli ?? {};
  const forceSpikes = output.forceSpikes ?? [];
  if (!stimuli || typeof stimuli !== 'object' || Array.isArray(stimuli) || !Array.isArray(forceSpikes)) {
    throw new TypeError('Expected stimuli object and forceSpikes array');
  }
  for (const [id, current] of Object.entries(stimuli)) {
    if (!adapter.allowedIds.has(id) || !Number.isFinite(current) || Math.abs(current) > 10) {
      throw new TypeError(`Unsupported sensory input: ${id}`);
    }
  }
  if (!forceSpikes.every((id) => adapter.allowedIds.has(id))) {
    throw new TypeError('forceSpikes contains an undeclared root ID');
  }
  return { stimuli, forceSpikes };
}
