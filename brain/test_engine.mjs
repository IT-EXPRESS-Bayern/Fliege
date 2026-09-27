import test from "node:test";
import assert from "node:assert/strict";
import { BrainEngine } from "./engine.mjs";
import { BrainWorkerRuntime } from "./worker.mjs";
import { normalizeControlFrame } from "../app/control.mjs";

const A = 720575940600000001n;
const B = 720575940600000009n;
const C = 720575940600000017n;

function syntheticGraph() {
  const ids = BigUint64Array.from([A, B, C]);
  const map = new Map([...ids].map((id, i) => [id.toString(), i]));
  return {
    manifest: { schema: "brain-csr-v1", node_count: 3, edge_count: 2 },
    ids,
    offsets: Uint32Array.from([0, 1, 2, 2]),
    targets: Uint32Array.from([1, 2]),
    synapses: Uint32Array.from([10, 5]),
    ntProbs: Uint8Array.from([255, 0, 0, 0, 0, 0, 0, 255, 0, 0, 0, 0]),
    indexOf(id) {
      if (typeof id === "number") throw new TypeError("Unsafe numeric root ID");
      const i = map.get(String(id));
      if (i === undefined) throw new Error(`Unknown ID: ${id}`);
      return i;
    },
  };
}

test("sparse event stepping preserves exact IDs and one-step delay", () => {
  const engine = new BrainEngine(syntheticGraph(), { synapseGain: 1 });
  const first = engine.step({ forceSpikes: [A.toString()], readout: [B.toString()] });
  assert.deepEqual(first.spikes, [A.toString()]);
  assert.equal(first.activeNodes, 1);
  assert.equal(first.readout[B.toString()], 0);
  const second = engine.step({ readout: [B.toString()] });
  assert.deepEqual(second.spikes, [B.toString()]);
  assert.equal(second.activeNodes, 1);
  assert.equal(second.traversedEdges, 1);
  const third = engine.step({ readout: [C.toString()] });
  assert.equal(third.spikeCount, 0);
  assert.ok(third.readout[C.toString()] < 0, "GABA edge should inhibit target");
  assert.equal(third.activeNodes, 1);
});

test("invalid stimulus leaves pending events and clock intact", () => {
  const engine = new BrainEngine(syntheticGraph(), { synapseGain: 1 });
  engine.step({ forceSpikes: [A.toString()] });
  assert.throws(() => engine.step({ stimuli: { [B.toString()]: Infinity } }), /Non-finite/);
  assert.equal(engine.stepNumber, 1);
  assert.deepEqual(engine.step().spikes, [B.toString()]);
});

test("background drive is opt-in, sparse and reproducible without a user goal", () => {
  const idle = new BrainEngine(syntheticGraph());
  for (let i = 0; i < 5; i++) {
    const state = idle.step();
    assert.equal(state.activeNodes, 0);
    assert.equal(state.backgroundEvents, 0);
    assert.equal(state.spikeCount, 0);
  }
  const config = { synapseGain: 1, background: {
    eventsPerMs: 10, amplitude: 2, seed: 12345, targets: [A.toString()],
  } };
  const first = new BrainEngine(syntheticGraph(), config);
  const second = new BrainEngine(syntheticGraph(), config);
  const timeline = Array.from({ length: 8 }, () => first.step());
  assert.deepEqual(timeline.map(x => [x.backgroundEvents, x.spikes]),
    Array.from({ length: 8 }, () => second.step()).map(x => [x.backgroundEvents, x.spikes]));
  assert.ok(timeline.some(x => x.spikes.includes(A.toString())));
  assert.ok(timeline.every(x => x.activeNodes <= 3));
  first.reset();
  assert.equal(first.step().backgroundEvents, timeline[0].backgroundEvents);
  const everywhere = new BrainEngine(syntheticGraph(), {
    background: { eventsPerMs: 10, amplitude: 2, seed: 12345 },
  });
  assert.ok(everywhere.step().spikeCount > 0);
});

test("worker emits app-compatible control frame only with explicit motor map", async () => {
  const runtime = new BrainWorkerRuntime(async () => syntheticGraph());
  const loaded = await runtime.handle({ type: "load", baseUrl: "/unused", requestId: "load",
    dynamics: { synapseGain: 1 }, motorMap: { forward: [B.toString()] },
    motorOptions: { smoothing: 1 } });
  assert.equal(loaded.type, "loaded");
  const first = await runtime.handle({ type: "step", requestId: "one",
    forceSpikes: [A.toString()], timestampMs: 1000 });
  assert.equal(first.controlFrame.forward, 0);
  const second = await runtime.handle({ type: "step", requestId: "two", timestampMs: 1016 });
  assert.equal(second.controlFrame.forward, 1);
  assert.deepEqual(normalizeControlFrame(second.controlFrame), second.controlFrame);
  assert.equal(second.requestId, "two");
  assert.equal(second.spikeIndices, undefined);
  const reset = await runtime.handle({ type: "reset" });
  assert.equal(reset.type, "reset");
});
