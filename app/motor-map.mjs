/** App-side evidence requirement for an explicitly hypothetical motor mapping. */
export const MOTOR_MAP_SCHEMA = 'fly.motor-map.v1';
export const MOTOR_CHANNELS = ['forward', 'turnLeft', 'turnRight', 'wing', 'groom'];

export function validateMotorMapSpec(spec) {
  if (!spec || spec.schema !== MOTOR_MAP_SCHEMA || typeof spec.dataset !== 'string' ||
      !spec.dataset.trim() || !spec.channels || typeof spec.channels !== 'object') {
    throw new TypeError(`Expected ${MOTOR_MAP_SCHEMA} with dataset and channels`);
  }
  const workerMap = Object.fromEntries(MOTOR_CHANNELS.map((channel) => [channel, []]));
  let mapped = 0;
  for (const [channel, entry] of Object.entries(spec.channels)) {
    if (!MOTOR_CHANNELS.includes(channel) || !entry || !Array.isArray(entry.rootIds) ||
        !entry.rootIds.length) {
      throw new TypeError(`Invalid motor channel: ${channel}`);
    }
    if (!entry.rootIds.every((id) => typeof id === 'string' && /^[1-9]\d*$/.test(id))) {
      throw new TypeError(`${channel} root IDs must be exact decimal strings`);
    }
    let url;
    try { url = new URL(entry.evidenceUrl); } catch { throw new TypeError(`${channel} needs an evidence URL`); }
    if (url.protocol !== 'https:' || typeof entry.hypothesis !== 'string' ||
        entry.hypothesis.trim().length < 20) {
      throw new TypeError(`${channel} needs an HTTPS source and an explicit hypothesis`);
    }
    workerMap[channel] = [...new Set(entry.rootIds)];
    mapped += workerMap[channel].length;
  }
  if (!mapped) throw new TypeError('At least one motor channel must be mapped');
  return {
    dataset: spec.dataset,
    workerMap,
    provenance: Object.fromEntries(Object.entries(spec.channels).map(([channel, entry]) => [channel, {
      evidenceUrl: entry.evidenceUrl,
      hypothesis: entry.hypothesis.trim(),
    }])),
  };
}
