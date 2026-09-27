"""Exploratory event-driven LIF-like dynamics over a brain-csr-v1 graph.

This is intentionally a simple numerical toy, not a calibrated fly brain.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np


class Graph:
    """Memory-mapped CSR graph with exact uint64 neuron IDs."""

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.manifest = json.loads((self.directory / "manifest.json").read_text(encoding="utf-8"))
        if self.manifest.get("schema") != "brain-csr-v1":
            raise ValueError("Unsupported graph schema")
        n = self.manifest["node_count"]
        m = self.manifest["edge_count"]
        self.ids = np.memmap(self.directory / "nodes.u64", dtype="<u8", mode="r", shape=(n,))
        self.offsets = np.memmap(self.directory / "offsets.u32", dtype="<u4", mode="r", shape=(n + 1,))
        if m:
            self.targets = np.memmap(self.directory / "targets.u32", dtype="<u4", mode="r", shape=(m,))
            self.synapses = np.memmap(self.directory / "synapses.u32", dtype="<u4", mode="r", shape=(m,))
            self.nt_probs = np.memmap(self.directory / "nt_probs.u8", dtype="u1", mode="r", shape=(m, 6))
        else:
            self.targets = np.empty(0, dtype="<u4")
            self.synapses = np.empty(0, dtype="<u4")
            self.nt_probs = np.empty((0, 6), dtype="u1")
        if int(self.offsets[-1]) != m:
            raise ValueError("CSR offsets do not match edge count")
        self.annotations = json.loads((self.directory / "annotations.json").read_text(encoding="utf-8"))

    def close(self) -> None:
        """Release mapped files, which also permits deletion on Windows."""
        for name in ("ids", "offsets", "targets", "synapses", "nt_probs"):
            mapped = getattr(self, name, None)
            if isinstance(mapped, np.memmap) and mapped._mmap is not None:
                mapped._mmap.close()

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()

    def index_of(self, root_id: str | int) -> int:
        exact = int(root_id)
        if exact < 0 or exact > np.iinfo(np.uint64).max:
            raise KeyError(root_id)
        i = int(np.searchsorted(self.ids, np.uint64(exact)))
        if i == len(self.ids) or int(self.ids[i]) != exact:
            raise KeyError(root_id)
        return i

    def id_of(self, index: int) -> str:
        return str(int(self.ids[index]))


class BrainSimulation:
    """Discrete-time threshold network with one-step delayed synaptic events.

    ACh contributes positive drive; GABA and glutamate contribute negative drive.
    Dopamine, serotonin, and octopamine probabilities are retained in the graph,
    but this simple dynamical rule does not model their context-dependent effects.
    Synapse count is compressed with log1p. None of these choices are a measured
    electrical conductance or a validated behavioral model.
    """

    def __init__(self, graph: Graph, *, dt_ms: float = 1.0, tau_ms: float = 20.0,
                 threshold: float = 1.0, reset: float = 0.0, synapse_gain: float = 0.1,
                 refractory_steps: int = 2):
        if dt_ms <= 0 or tau_ms <= 0 or threshold <= reset or synapse_gain < 0 or refractory_steps < 0:
            raise ValueError("Invalid dynamics parameters")
        self.graph = graph
        self.dt_ms = float(dt_ms)
        self.decay = math.exp(-dt_ms / tau_ms)
        self.threshold = float(threshold)
        self.reset = float(reset)
        self.synapse_gain = float(synapse_gain)
        self.refractory_steps = int(refractory_steps)
        self.voltage = np.full(len(graph.ids), reset, dtype=np.float32)
        self.pending = np.zeros(len(graph.ids), dtype=np.float32)
        self.refractory = np.zeros(len(graph.ids), dtype=np.uint16)
        self.step_number = 0

    def step(self, stimuli: Mapping[str | int, float] | None = None,
             force_spikes: Iterable[str | int] = (),
             readout: Iterable[str | int] = ()) -> dict:
        """Advance one dt. Stimuli are arbitrary current units, keyed by exact root IDs."""
        self.voltage *= self.decay
        self.voltage += self.pending
        self.pending.fill(0.0)
        active_refractory = self.refractory > 0
        self.refractory[active_refractory] -= 1
        self.voltage[active_refractory] = self.reset
        for root_id, drive in (stimuli or {}).items():
            i = self.graph.index_of(root_id)
            if not active_refractory[i]:
                self.voltage[i] += float(drive)
        spike_mask = (self.voltage >= self.threshold) & ~active_refractory
        for root_id in force_spikes:
            spike_mask[self.graph.index_of(root_id)] = True
        spiking = np.flatnonzero(spike_mask)
        self.voltage[spiking] = self.reset
        if self.refractory_steps:
            self.refractory[spiking] = self.refractory_steps
        for i in spiking:
            lo, hi = int(self.graph.offsets[i]), int(self.graph.offsets[i + 1])
            if lo == hi:
                continue
            p = self.graph.nt_probs[lo:hi].astype(np.float32) / 255.0
            sign = p[:, 0] - p[:, 1] - p[:, 2]
            weight = self.synapse_gain * np.log1p(self.graph.synapses[lo:hi]) * sign
            np.add.at(self.pending, self.graph.targets[lo:hi], weight.astype(np.float32))
        self.step_number += 1
        return {
            "step": self.step_number,
            "time_ms": self.step_number * self.dt_ms,
            "spike_count": len(spiking),
            "spikes": [self.graph.id_of(int(i)) for i in spiking],
            "readout": {str(root_id): float(self.voltage[self.graph.index_of(root_id)])
                        for root_id in readout},
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Line-delimited JSON stimulus/readout interface")
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--dt-ms", type=float, default=1.0)
    parser.add_argument("--tau-ms", type=float, default=20.0)
    parser.add_argument("--synapse-gain", type=float, default=0.1)
    args = parser.parse_args()
    simulation = BrainSimulation(Graph(args.graph), dt_ms=args.dt_ms,
                                 tau_ms=args.tau_ms, synapse_gain=args.synapse_gain)
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            steps = int(request.get("steps", 1))
            if not 1 <= steps <= 1000:
                raise ValueError("steps must be between 1 and 1000")
            result = None
            for _ in range(steps):
                result = simulation.step(request.get("stimuli"), request.get("force_spikes", ()),
                                         request.get("readout", ()))
            print(json.dumps(result, separators=(",", ":")), flush=True)
        except (ValueError, KeyError, TypeError) as exc:
            print(json.dumps({"error": str(exc)}), flush=True)


if __name__ == "__main__":
    main()
