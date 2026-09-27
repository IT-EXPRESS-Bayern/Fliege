import { ExternalControlInbox } from './control.mjs';
import { validateMotorMapSpec } from './motor-map.mjs';

export const GRAPH_SCHEMA = 'brain-csr-v1';
export const GRAPH_BASE_URL = '/brain/graph-original-v783';
export const ORIGINAL_GRAPH_DATASET = 'flywire_fafb_v783_original';

/** Prevent a filtered graph with the same neuron IDs from appearing as the original. */
export function matchesLoadedOriginalGraph(status, loaded) {
  return status?.state === 'ready' && status.dataset === ORIGINAL_GRAPH_DATASET &&
    loaded?.dataset === ORIGINAL_GRAPH_DATASET &&
    loaded.nodeCount === status.nodeCount && loaded.edgeCount === status.edgeCount;
}

/** Adapter for the actual brain/worker.mjs load/step/state protocol. */
export class BrainWorkerBridge {
  constructor(onChange = () => {}) {
    this.onChange = onChange;
    this.worker = null;
    this.status = 'disconnected';
    this.message = 'Kein Graph-Worker verbunden';
    this.metadata = null;
    this.motorSpec = null;
    this.inbox = new ExternalControlInbox();
    this.requestNumber = 0;
    this.currentLoadId = null;
    this.stepPending = false;
    this.lastState = null;
    this.onMessage = (event) => this.receive(event.data);
    this.onWorkerError = () => this.fail('Graph-Worker konnte nicht ausgeführt werden');
  }

  get motorConfigured() {
    return this.status === 'ready' && this.motorSpec !== null;
  }

  attach(worker) {
    if (!worker || typeof worker.addEventListener !== 'function' ||
        typeof worker.removeEventListener !== 'function' || typeof worker.postMessage !== 'function') {
      throw new TypeError('A Worker-like message transport is required');
    }
    this.detach();
    this.worker = worker;
    worker.addEventListener('message', this.onMessage);
    worker.addEventListener('error', this.onWorkerError);
    this.load();
  }

  setMotorMap(spec) {
    this.motorSpec = validateMotorMapSpec(spec);
    if (this.worker) this.load();
    else this.onChange();
  }

  clearMotorMap() {
    this.motorSpec = null;
    this.inbox.clear();
    if (this.worker) this.load();
    else this.onChange();
  }

  load() {
    if (!this.worker) return;
    this.status = 'loading';
    this.message = 'Connectome-Graph wird im Worker geladen';
    this.metadata = null;
    this.lastState = null;
    this.stepPending = false;
    this.inbox.clear();
    this.currentLoadId = `load-${++this.requestNumber}`;
    this.worker.postMessage({
      type: 'load',
      requestId: this.currentLoadId,
      baseUrl: GRAPH_BASE_URL,
      ...(this.motorSpec ? { motorMap: this.motorSpec.workerMap } : {}),
    });
    this.onChange();
  }

  receive(payload) {
    if (!this.worker || !payload || typeof payload !== 'object') return;
    if (payload.type === 'loaded') {
      if (payload.requestId !== this.currentLoadId) return;
      const manifest = payload.manifest;
      if (manifest?.schema !== GRAPH_SCHEMA || !Number.isInteger(manifest.node_count) ||
          manifest.node_count <= 0 || !Number.isInteger(manifest.edge_count) || manifest.edge_count < 0) {
        this.fail('Worker hat ein unpassendes Graph-Manifest geladen');
        return;
      }
      if (this.motorSpec && this.motorSpec.dataset !== manifest.dataset) {
        this.fail('Motorzuordnung und Graph verwenden unterschiedliche Datensätze');
        return;
      }
      this.metadata = {
        dataset: manifest.dataset,
        nodeCount: manifest.node_count,
        edgeCount: manifest.edge_count,
      };
      this.status = 'ready';
      this.message = this.motorSpec
        ? 'Graph geladen · hypothetische Motorzuordnung konfiguriert'
        : 'Graph geladen · keine Motorzuordnung';
      this.onChange();
    } else if (payload.type === 'state' && this.status === 'ready') {
      this.stepPending = false;
      this.lastState = payload;
      if (this.motorSpec && payload.controlFrame) {
        try { this.inbox.receive(payload.controlFrame); }
        catch { this.fail('Ungültiger Steuerframe vom Graph-Worker'); }
      }
    } else if (payload.type === 'error') {
      if (payload.requestId && payload.requestId !== this.currentLoadId &&
          !String(payload.requestId).startsWith('step-')) return;
      this.fail(typeof payload.message === 'string' ? payload.message : 'Graph-Worker meldet einen Fehler');
    }
  }

  step(timestampMs, steps = 16, input = {}) {
    if (this.status !== 'ready' || !this.worker || this.stepPending) return false;
    this.stepPending = true;
    this.worker.postMessage({ type: 'step', requestId: `step-${++this.requestNumber}`,
      timestampMs, steps, stimuli: input.stimuli || {}, forceSpikes: input.forceSpikes || [] });
    return true;
  }

  reset() {
    if (this.status !== 'ready' || !this.worker) return;
    this.stepPending = false;
    this.inbox.clear();
    this.worker.postMessage({ type: 'reset', requestId: `reset-${++this.requestNumber}` });
  }

  sample(nowMs) {
    return this.motorConfigured ? this.inbox.sample(nowMs) : null;
  }

  fail(message) {
    this.status = 'error';
    this.message = message;
    this.stepPending = false;
    this.inbox.clear();
    this.onChange();
  }

  detach() {
    if (this.worker) {
      this.worker.removeEventListener('message', this.onMessage);
      this.worker.removeEventListener('error', this.onWorkerError);
    }
    this.worker = null;
    this.status = 'disconnected';
    this.message = 'Kein Graph-Worker verbunden';
    this.metadata = null;
    this.stepPending = false;
    this.lastState = null;
    this.inbox.clear();
    this.onChange();
  }
}
