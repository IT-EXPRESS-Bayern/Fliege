"""Independent fixture checks for the derived CSR graph audit."""

import csv
import gzip
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

import codex_graph_audit as audit


class CodexGraphAuditTests(unittest.TestCase):
    def test_csr_integrity_and_source_count(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            graph = folder / "graph"
            graph.mkdir()
            source = folder / "source"
            source.mkdir()
            ids = np.array([720575940628857210, 720575940628857211], dtype="<u8")
            arrays = {
                "nodes.u64": ids,
                "offsets.u32": np.array([0, 1, 1], dtype="<u4"),
                "targets.u32": np.array([1], dtype="<u4"),
                "synapses.u32": np.array([5], dtype="<u4"),
                "nt_probs.u8": np.array([255, 0, 0, 0, 0, 0], dtype="u1"),
            }
            for name, values in arrays.items():
                values.tofile(graph / name)
            annotations = [{"id": str(int(item))} for item in ids]
            (graph / "annotations.json").write_text(json.dumps(annotations), encoding="utf-8")
            source_path = source / "connections_princeton.csv.gz"
            with gzip.open(source_path, "wt", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["pre_root_id", "post_root_id", "neuropil", "syn_count", "nt_type"])
                writer.writerow([str(int(ids[0])), str(int(ids[1])), "AL_L", 5, "ACH"])
            files = {}
            for path in graph.iterdir():
                files[path.name] = {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            manifest = {
                "node_count": 2, "edge_count": 1, "synapse_count": 5, "input_rows": 1,
                "files": files,
                "sources": {"connections": {
                    "file": source_path.name,
                    "published_md5": hashlib.md5(source_path.read_bytes()).hexdigest(),
                    "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
                }},
            }
            (graph / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = audit.audit_graph(graph, source, ids, skip_hashes=False)
            self.assertTrue(result["checks_all_true"])
            self.assertFalse(result["incomplete"])
            self.assertEqual(result["graph_stats"]["synapses_in_graph"], 5)
            self.assertTrue(result["codex_source"]["synapses_match_graph"])


if __name__ == "__main__":
    unittest.main()
