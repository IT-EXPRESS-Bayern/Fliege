"""Synthetic checks for aggregation, 64-bit identity and delayed dynamics."""

import csv
import gzip
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

from brain.build import NT_COLUMNS, build
from brain.simulation import BrainSimulation, Graph


A = 720575940600000001
B = 720575940600000009
C = 720575940600000017


class GraphBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.root_ids = self.path / "roots.npy"
        np.save(self.root_ids, np.array([C, A, B], dtype=np.uint64))
        self.connections = self.path / "connections.csv"
        with self.connections.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=("pre_pt_root_id", "post_pt_root_id", "neuropil",
                                                    "syn_count", *NT_COLUMNS))
            writer.writeheader()
            writer.writerows([
                self.row(A, B, "AL_L", 3, ach=1),
                self.row(B, C, "AL_L", 2, gaba=1),
                self.row(A, B, "AL_R", 7, ach=0.5, gaba=0.5),
                self.row(999, C, "AL_R", 5, ach=1),
                self.row(C, A, "AL_L", 1, glut=1),
            ])
        self.annotations = self.path / "annotations.tsv"
        with self.annotations.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=("root_id", "cell_type", "top_nt"), delimiter="\t")
            writer.writeheader()
            writer.writerows([
                {"root_id": str(A), "cell_type": "input", "top_nt": "acetylcholine"},
                {"root_id": str(B), "cell_type": "relay", "top_nt": "GABA"},
            ])

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def row(pre, post, neuropil, syn, **probs):
        return {"pre_pt_root_id": pre, "post_pt_root_id": post, "neuropil": neuropil,
                "syn_count": syn, **{c: probs.get(c.split("_")[0], 0) for c in NT_COLUMNS}}

    def test_aggregate_across_neuropils_and_batches(self):
        out = self.path / "graph"
        manifest = build(self.connections, self.root_ids, self.annotations, out,
                         "synthetic", chunk_rows=2)
        self.assertEqual(manifest["node_count"], 3)
        self.assertEqual(manifest["edge_count"], 3)
        self.assertEqual(manifest["synapse_count"], 13)
        self.assertEqual(manifest["dropped_rows"], 1)
        self.assertEqual(manifest["dropped_synapses"], 5)
        with Graph(out) as graph:
            self.assertEqual([int(x) for x in graph.ids], [A, B, C])
            self.assertEqual([int(x) for x in graph.offsets], [0, 1, 2, 3])
            self.assertEqual([int(x) for x in graph.targets], [1, 2, 0])
            self.assertEqual([int(x) for x in graph.synapses], [10, 2, 1])
            self.assertAlmostEqual(graph.nt_probs[0, 0] / 255, 0.65, places=2)
            self.assertAlmostEqual(graph.nt_probs[0, 1] / 255, 0.35, places=2)
            self.assertEqual(json.loads((out / "annotations.json").read_text())[0]["id"], str(A))
            self.assertEqual(graph.index_of(str(C)), 2)

    def test_threshold_and_event_delay(self):
        out = self.path / "strong"
        build(self.connections, self.root_ids, self.annotations, out,
              "synthetic", min_synapses=5, chunk_rows=2)
        with Graph(out) as graph:
            self.assertEqual(graph.manifest["edge_count"], 1)
            self.assertEqual(int(graph.synapses[0]), 10)
            sim = BrainSimulation(graph, synapse_gain=2.0)
            first = sim.step(force_spikes=[str(A)], readout=[str(B)])
            self.assertEqual(first["spikes"], [str(A)])
            self.assertEqual(first["readout"][str(B)], 0.0)
            second = sim.step(readout=[str(B)])
            self.assertEqual(second["spikes"], [str(B)])
            self.assertEqual(second["spike_count"], 1)

    def test_codex_gzip_categorical_export(self):
        codex = self.path / "codex.csv.gz"
        with gzip.open(codex, "wt", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=("pre_root_id", "post_root_id", "neuropil",
                                                    "syn_count", "nt_type"))
            writer.writeheader()
            writer.writerows([
                {"pre_root_id": A, "post_root_id": B, "neuropil": "AL_L", "syn_count": 3, "nt_type": "ACH"},
                {"pre_root_id": A, "post_root_id": B, "neuropil": "AL_R", "syn_count": 7, "nt_type": "GABA"},
                {"pre_root_id": B, "post_root_id": C, "neuropil": "AL_L", "syn_count": 2, "nt_type": "GLUT"},
            ])
        out = self.path / "codex-graph"
        manifest = build(codex, self.root_ids, self.annotations, out, "synthetic-codex", chunk_rows=1)
        self.assertEqual(manifest["edge_count"], 2)
        self.assertEqual(manifest["synapse_count"], 12)
        self.assertEqual(manifest["sources"]["connections"]["format"], "codex_princeton_categorical_nt")
        self.assertIn("not source probability estimates", manifest["sources"]["connections"]["neurotransmitter_semantics"])
        with Graph(out) as graph:
            self.assertAlmostEqual(graph.nt_probs[0, 0] / 255, 0.3, places=2)
            self.assertAlmostEqual(graph.nt_probs[0, 1] / 255, 0.7, places=2)
            self.assertAlmostEqual(graph.nt_probs[1, 2] / 255, 1.0, places=2)

    @unittest.skipUnless(importlib.util.find_spec("pyarrow"), "pyarrow not installed")
    def test_feather_v2_batches(self):
        import pyarrow as pa
        import pyarrow.feather as feather

        with self.connections.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        columns = {
            "pre_pt_root_id": pa.array([int(r["pre_pt_root_id"]) for r in rows], type=pa.uint64()),
            "post_pt_root_id": pa.array([int(r["post_pt_root_id"]) for r in rows], type=pa.uint64()),
            "syn_count": pa.array([int(r["syn_count"]) for r in rows], type=pa.uint32()),
            **{c: pa.array([float(r[c]) for r in rows], type=pa.float32()) for c in NT_COLUMNS},
        }
        feather_path = self.path / "connections.feather"
        feather.write_feather(pa.table(columns), feather_path, version=2, chunksize=2)
        out = self.path / "feather-graph"
        result = build(feather_path, self.root_ids, self.annotations, out,
                       "synthetic-feather", chunk_rows=2)
        self.assertEqual(result["edge_count"], 3)
        self.assertEqual(result["synapse_count"], 13)
        with Graph(out) as graph:
            self.assertEqual([int(x) for x in graph.synapses], [10, 2, 1])

    def test_ndjson_bridge(self):
        out = self.path / "cli-graph"
        build(self.connections, self.root_ids, self.annotations, out,
              "synthetic", min_synapses=5)
        request = {"force_spikes": [str(A)], "readout": [str(B)]}
        run = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("simulation.py")),
             "--graph", str(out), "--synapse-gain", "2"],
            input=json.dumps(request) + "\n" + json.dumps({"readout": [str(B)]}) + "\n",
            text=True, capture_output=True, check=True,
        )
        responses = [json.loads(line) for line in run.stdout.splitlines()]
        self.assertEqual(responses[0]["spikes"], [str(A)])
        self.assertEqual(responses[1]["spikes"], [str(B)])


if __name__ == "__main__":
    unittest.main()
