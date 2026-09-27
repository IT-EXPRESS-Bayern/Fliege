/** Sparse, exploratory discrete-time dynamics on a brain-csr-v1 graph.
 *
 * The graph has measured anatomical connectivity and inferred transmitters.
 * The voltage, signs, weights, refractory period and motor mapping below are
 * simplifying assumptions; they are not a calibrated physiological model.
 */

const CONTROL_KIND = "fly.control.v1";
const clamp = (value, lo, hi) => Math.max(lo, Math.min(hi, value));

export class BrainEngine {
  constructor(graph, { dtMs = 1, tauMs = 20, threshold = 1, resetVoltage = 0,
    synapseGain = 0.1, refractorySteps = 2, background = null } = {}) {
    if (!graph || graph.manifest?.schema !== "brain-csr-v1") throw new TypeError("Expected brain-csr-v1 graph");
    if (![dtMs, tauMs, threshold, resetVoltage, synapseGain].every(Number.isFinite) ||
        dtMs <= 0 || tauMs <= 0 || threshold <= resetVoltage || synapseGain < 0 ||
        !Number.isInteger(refractorySteps) || refractorySteps < 0) {
      throw new RangeError("Invalid dynamics settings");
    }
    this.graph = graph;
    this.dtMs = dtMs;
    this.decay = Math.exp(-dtMs / tauMs);
    this.threshold = threshold;
    this.resetVoltage = resetVoltage;
    this.synapseGain = synapseGain;
    this.refractorySteps = refractorySteps;
    if (background !== null) {
      const { eventsPerMs, amplitude, seed = 0x5eed1234, targets } = background;
      if (!Number.isFinite(eventsPerMs) || eventsPerMs < 0 ||
          !Number.isFinite(amplitude) || amplitude <= 0 ||
          !Number.isInteger(seed) || seed < 0 || seed > 0xffffffff ||
          eventsPerMs * dtMs > 10_000 ||
          (targets !== undefined && (!Array.isArray(targets) || !targets.length))) {
        throw new RangeError("Invalid background drive settings");
      }
      this.background = {
        eventsPerMs, amplitude, seed: (seed >>> 0) || 1,
        targets: targets?.map(id => graph.indexOf(id)) ?? null,
      };
    } else {
      this.background = null;
    }
    this.reset();
  }

  /** Seeded xorshift32; used only for the optional hypothetical background. */
  random() {
    let value = this.rngState;
    value ^= value << 13;
    value ^= value >>> 17;
    value ^= value << 5;
    this.rngState = value >>> 0;
    return (this.rngState + 1) / 4294967297;
  }

  reset() {
    const n = this.graph.ids.length;
    this.voltage = new Float32Array(n);
    this.voltage.fill(this.resetVoltage);
    this.pending = new Float32Array(n);
    this.stimulus = new Float32Array(n);
    this.lastStep = new Float64Array(n);
    this.refractoryUntil = new Float64Array(n);
    this.pendingFlag = new Uint8Array(n);
    this.candidateFlag = new Uint8Array(n);
    this.forcedFlag = new Uint8Array(n);
    this.pendingNodes = [];
    this.stepNumber = 0;
    this.rngState = this.background?.seed ?? 1;
    this.nextBackgroundEventMs = this.background?.eventsPerMs ?
      -Math.log(this.random()) / this.background.eventsPerMs : Infinity;
  }

  /** Return lazily decayed voltage without sweeping every node. */
  voltageOf(id) {
    const index = this.graph.indexOf(id);
    return this.resetVoltage + (this.voltage[index] - this.resetVoltage) *
      Math.pow(this.decay, this.stepNumber - this.lastStep[index]);
  }

  step({ stimuli = {}, forceSpikes = [], readout = [], maxReportedSpikes = 256 } = {}) {
    if (!stimuli || typeof stimuli !== "object" || Array.isArray(stimuli)) throw new TypeError("stimuli must be an ID-to-current object");
    if (!Array.isArray(forceSpikes) || !Array.isArray(readout)) throw new TypeError("forceSpikes and readout must be arrays");
    if (!Number.isInteger(maxReportedSpikes) || maxReportedSpikes < 0) throw new RangeError("Invalid maxReportedSpikes");
    // Validate IDs and currents before advancing or consuming pending events.
    const inputs = Object.entries(stimuli).map(([rootId, current]) => {
      if (!Number.isFinite(current)) throw new TypeError(`Non-finite stimulus for ${rootId}`);
      return [this.graph.indexOf(rootId), current];
    });
    const forcedIndexes = forceSpikes.map(id => this.graph.indexOf(id));
    const readoutIndexes = readout.map(id => [String(id), this.graph.indexOf(id)]);
    const step = ++this.stepNumber;
    const candidates = this.pendingNodes;
    this.pendingNodes = [];
    for (const i of candidates) {
      this.pendingFlag[i] = 0;
      this.candidateFlag[i] = 1;
    }
    const addCandidate = i => {
      if (!this.candidateFlag[i]) {
        this.candidateFlag[i] = 1;
        candidates.push(i);
      }
    };
    for (const [i, current] of inputs) {
      this.stimulus[i] += current;
      addCandidate(i);
    }
    for (const i of forcedIndexes) {
      this.forcedFlag[i] = 1;
      addCandidate(i);
    }
    let backgroundEvents = 0;
    if (this.background?.eventsPerMs) {
      const endMs = step * this.dtMs;
      const { targets: backgroundTargets, amplitude, eventsPerMs } = this.background;
      while (this.nextBackgroundEventMs <= endMs) {
        const poolLength = backgroundTargets?.length ?? this.graph.ids.length;
        const chosen = Math.floor(this.random() * poolLength);
        const index = backgroundTargets ? backgroundTargets[chosen] : chosen;
        this.stimulus[index] += amplitude;
        addCandidate(index);
        backgroundEvents++;
        this.nextBackgroundEventMs += -Math.log(this.random()) / eventsPerMs;
      }
    }

    const spiking = [];
    for (const i of candidates) {
      const input = this.pending[i] + this.stimulus[i];
      this.pending[i] = 0;
      this.stimulus[i] = 0;
      const forced = this.forcedFlag[i] !== 0;
      const blocked = step <= this.refractoryUntil[i];
      let voltage = blocked ? this.resetVoltage :
        this.resetVoltage + (this.voltage[i] - this.resetVoltage) *
          Math.pow(this.decay, step - this.lastStep[i]) + input;
      if (forced || (!blocked && voltage >= this.threshold)) {
        voltage = this.resetVoltage;
        this.refractoryUntil[i] = step + this.refractorySteps;
        spiking.push(i);
      }
      this.voltage[i] = voltage;
      this.lastStep[i] = step;
      this.candidateFlag[i] = 0;
      this.forcedFlag[i] = 0;
    }

    const { offsets, targets, synapses, ntProbs } = this.graph;
    let traversedEdges = 0;
    let deliveredEvents = 0;
    for (const src of spiking) {
      const end = offsets[src + 1];
      for (let edge = offsets[src]; edge < end; edge++) {
        traversedEdges++;
        const nt = edge * 6;
        // ACh positive, GABA and glutamate negative. Monoamines: not modeled.
        const sign = (ntProbs[nt] - ntProbs[nt + 1] - ntProbs[nt + 2]) / 255;
        if (sign === 0) continue;
        const dst = targets[edge];
        this.pending[dst] += this.synapseGain * Math.log1p(synapses[edge]) * sign;
        if (!this.pendingFlag[dst]) {
          this.pendingFlag[dst] = 1;
          this.pendingNodes.push(dst);
        }
        deliveredEvents++;
      }
    }
    const readoutValues = {};
    for (const [id, index] of readoutIndexes) {
      readoutValues[id] = this.resetVoltage + (this.voltage[index] - this.resetVoltage) *
        Math.pow(this.decay, step - this.lastStep[index]);
    }
    return {
      step, timeMs: step * this.dtMs, activeNodes: candidates.length,
      traversedEdges, deliveredEvents, backgroundEvents, spikeCount: spiking.length,
      spikes: spiking.slice(0, maxReportedSpikes).map(i => this.graph.ids[i].toString()),
      spikesTruncated: spiking.length > maxReportedSpikes,
      readout: readoutValues,
      // Internal local result; the Worker removes this before postMessage.
      spikeIndices: spiking,
    };
  }
}

/** Explicit, experimental adapter to the app's fly.control.v1 contract.
 * No FlyWire neuron IDs or sensor/motor semantics are hard-coded here.
 */
export class MotorReadout {
  constructor(graph, map, { smoothing = 0.2 } = {}) {
    if (!Number.isFinite(smoothing) || smoothing <= 0 || smoothing > 1) throw new RangeError("Invalid smoothing");
    this.smoothing = smoothing;
    this.groups = {};
    for (const name of ["forward", "turnLeft", "turnRight", "wing", "groom"]) {
      const ids = map?.[name] ?? [];
      if (!Array.isArray(ids)) throw new TypeError(`${name} must be an array of root IDs`);
      this.groups[name] = ids.map(id => graph.indexOf(id));
    }
    this.activity = { forward: 0, turnLeft: 0, turnRight: 0, wing: 0, groom: 0 };
  }

  reset() {
    for (const name of Object.keys(this.activity)) this.activity[name] = 0;
  }

  update(spikeIndices, timestampMs) {
    if (!Number.isFinite(timestampMs)) throw new TypeError("timestampMs must be the app's performance.now() value");
    const active = new Set(spikeIndices);
    for (const [name, indexes] of Object.entries(this.groups)) {
      const fraction = indexes.length ? indexes.reduce((sum, i) => sum + Number(active.has(i)), 0) / indexes.length : 0;
      this.activity[name] += this.smoothing * (fraction - this.activity[name]);
    }
    return {
      kind: CONTROL_KIND, timestampMs,
      forward: clamp(this.activity.forward, 0, 1),
      turn: clamp(this.activity.turnRight - this.activity.turnLeft, -1, 1),
      wing: clamp(this.activity.wing, 0, 1),
      groom: clamp(this.activity.groom, 0, 1),
    };
  }
}
