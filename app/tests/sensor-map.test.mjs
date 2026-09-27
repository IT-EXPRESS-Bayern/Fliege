import assert from 'node:assert/strict';
import test from 'node:test';
import { encodeSensoryInput, validateSensorAdapterSpec } from '../sensor-map.mjs';

const spec = {
  schema: 'fly.sensor-adapter.v1', dataset: 'flywire_fafb_v783_codex_princeton',
  channels: {
    wallSignal: {
      rootIds: ['720575940600000002'],
      evidenceUrl: 'https://doi.org/10.0000/example',
      hypothesis: 'Wandnähe wird versuchsweise als Strom in diese sensorische Zelle kodiert.',
    },
  },
  encode(observation) {
    return { stimuli: { '720575940600000002': observation.x }, forceSpikes: [] };
  },
};

test('sensor adapter admits only declared exact IDs and finite inputs', () => {
  const adapter = validateSensorAdapterSpec(spec);
  assert.deepEqual(encodeSensoryInput(adapter, { x: 0.5 }).stimuli,
    { '720575940600000002': 0.5 });
  assert.throws(() => encodeSensoryInput(adapter, { x: Infinity }), /Unsupported/);
  assert.throws(() => encodeSensoryInput({ ...adapter,
    encode: () => ({ stimuli: { '720575940600000003': 1 } }) }, {}), /Unsupported/);
});

test('sensor adapter requires provenance and decimal-string root IDs', () => {
  assert.throws(() => validateSensorAdapterSpec({ ...spec, channels: {
    wallSignal: { ...spec.channels.wallSignal, rootIds: [720575940600000002] },
  } }), /sensor channel/);
  assert.throws(() => validateSensorAdapterSpec({ ...spec, channels: {
    wallSignal: { ...spec.channels.wallSignal, evidenceUrl: 'http://example.org' },
  } }), /HTTPS source/);
});
