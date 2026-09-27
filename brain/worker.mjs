/** Browser Worker protocol for a brain-csr-v1 graph.
 *
 * Requests: {type:'load',baseUrl,dynamics?,motorMap?,requestId?}
 *           {type:'step',stimuli?,forceSpikes?,readout?,steps?,timestampMs?,requestId?}
 *           {type:'reset',requestId?}
 * Replies:  {type:'loaded'|'state'|'reset'|'error',requestId?,...}
 */

import { loadBrainGraph } from "./web.mjs";
import { BrainEngine, MotorReadout } from "./engine.mjs";

export class BrainWorkerRuntime {
  constructor(loader = loadBrainGraph) {
    this.loader = loader;
    this.graph = null;
    this.engine = null;
    this.motor = null;
  }

  async handle(request) {
    const requestId = request?.requestId;
    if (request?.type === "load") {
      if (typeof request.baseUrl !== "string") throw new TypeError("baseUrl must be a string");
      this.graph = await this.loader(request.baseUrl);
      this.engine = new BrainEngine(this.graph, request.dynamics);
      this.motor = request.motorMap ? new MotorReadout(this.graph, request.motorMap,
        request.motorOptions) : null;
      return { type: "loaded", requestId, manifest: this.graph.manifest };
    }
    if (!this.engine) throw new Error("Load a graph first");
    if (request.type === "reset") {
      this.engine.reset();
      this.motor?.reset();
      return { type: "reset", requestId };
    }
    if (request.type !== "step") throw new TypeError(`Unknown message type: ${request.type}`);
    const steps = request.steps ?? 1;
    if (!Number.isInteger(steps) || steps < 1 || steps > 1000) throw new RangeError("steps must be 1..1000");
    let state;
    let controlFrame;
    for (let i = 0; i < steps; i++) {
      state = this.engine.step(request);
      if (this.motor && Number.isFinite(request.timestampMs)) {
        controlFrame = this.motor.update(state.spikeIndices, request.timestampMs);
      }
    }
    const { spikeIndices, ...publicState } = state;
    return { type: "state", requestId, ...publicState,
      ...(controlFrame ? { controlFrame } : {}) };
  }
}

if (typeof self !== "undefined" && typeof self.postMessage === "function") {
  const runtime = new BrainWorkerRuntime();
  self.onmessage = async event => {
    try {
      self.postMessage(await runtime.handle(event.data));
    } catch (error) {
      self.postMessage({ type: "error", requestId: event.data?.requestId,
        message: error instanceof Error ? error.message : String(error) });
    }
  };
}
