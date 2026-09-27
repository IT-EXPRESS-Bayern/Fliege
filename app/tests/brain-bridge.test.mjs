import assert from 'node:assert/strict';
import test from 'node:test';
import { BrainWorkerBridge, GRAPH_BASE_URL } from '../brain-bridge.mjs';
import { validateMotorMapSpec } from '../motor-map.mjs';

class FakeWorker {
  constructor() { this.listeners = new Map(); this.sent = []; }
  addEventListener(type, callback) { this.listeners.set(type, callback); }
  removeEventListener(type) { this.listeners.delete(type); }
  postMessage(message) { this.sent.push(message); }
  emit(message) { this.listeners.get('message')?.({ data: message }); }
}

const manifest = {
  schema: 'brain-csr-v1', dataset: 'flywire_fafb_v783_original',
  node_count: 139255, edge_count: 15091983,
};
const motorSpec = {
  schema: 'fly.motor-map.v1', dataset: manifest.dataset,
  channels: {
    forward: {
      rootIds: ['720575940600000001'],
      evidenceUrl: 'https://doi.org/10.0000/example',
      hypothesis: 'Diese Zelle könnte vorwärtsgerichtete Aktivität kodieren.',
    },
  },
};

test('actual brain worker protocol loads a graph without claiming motor control', () => {
  const bridge = new BrainWorkerBridge();
  const worker = new FakeWorker();
  bridge.attach(worker);
  assert.equal(worker.sent[0].type, 'load');
  assert.equal(worker.sent[0].baseUrl, GRAPH_BASE_URL);
  assert.equal(GRAPH_BASE_URL, '/brain/graph-original-v783');
  assert.equal(worker.sent[0].motorMap, undefined);
  worker.emit({ type: 'loaded', requestId: worker.sent[0].requestId, manifest });
  assert.equal(bridge.status, 'ready');
  assert.equal(bridge.motorConfigured, false);
  assert.equal(bridge.sample(100), null);
});

test('motor frames require an explicit mapped reload and expire when stale', () => {
  const bridge = new BrainWorkerBridge();
  const worker = new FakeWorker();
  bridge.attach(worker);
  worker.emit({ type: 'loaded', requestId: worker.sent[0].requestId, manifest });
  bridge.setMotorMap(motorSpec);
  const mappedLoad = worker.sent.at(-1);
  assert.deepEqual(mappedLoad.motorMap.forward, ['720575940600000001']);
  assert.equal(bridge.motorConfigured, false, 'control stays disabled while reloading');
  worker.emit({ type: 'loaded', requestId: mappedLoad.requestId, manifest });
  assert.equal(bridge.motorConfigured, true);
  assert.equal(bridge.step(100, 10, { stimuli: { '720575940600000002': 1.5 } }), true);
  assert.equal(worker.sent.at(-1).stimuli['720575940600000002'], 1.5);
  assert.equal(bridge.step(101, 10), false, 'only one step may be in flight');
  worker.emit({ type: 'state', requestId: worker.sent.at(-1).requestId,
    controlFrame: { kind: 'fly.control.v1', timestampMs: 100, forward: 0.7,
      turn: 0, wing: 0, groom: 0 } });
  assert.equal(bridge.sample(200).forward, 0.7);
  assert.equal(bridge.sample(500), null);
  bridge.detach();
  assert.equal(bridge.motorConfigured, false);
});

test('motor map schema rejects missing evidence and numeric root IDs', () => {
  assert.throws(() => validateMotorMapSpec({ ...motorSpec, channels: {
    forward: { ...motorSpec.channels.forward, rootIds: [720575940600000001] },
  } }), /root IDs/);
  assert.throws(() => validateMotorMapSpec({ ...motorSpec, channels: {
    forward: { ...motorSpec.channels.forward, evidenceUrl: '' },
  } }), /evidence URL/);
  assert.equal(validateMotorMapSpec(motorSpec).workerMap.forward.length, 1);
});
