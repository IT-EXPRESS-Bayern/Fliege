"""Small fixture checks for the local FAFB analyzer; no network or real data needed."""

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.feather as feather

import analyze_flywire as audit


class FlyWireAuditTests(unittest.TestCase):
    def test_large_root_id_membership_is_exact(self):
        ids = np.array([720575940628857210, 720575940628857211], dtype=np.uint64)
        query = np.array([720575940628857210, 720575940628857212, -1], dtype=np.int64)
        self.assertEqual(audit.membership(query, ids).tolist(), [True, False, False])

    def test_aggregated_edges_and_annotation_join(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            ids = np.array([720575940628857210, 720575940628857211], dtype=np.uint64)
            path = folder / "proofread_connections_783.feather"
            feather.write_feather(pa.table({
                "pre_pt_root_id": pa.array([int(ids[0]), int(ids[1])], type=pa.int64()),
                "post_pt_root_id": pa.array([int(ids[1]), int(ids[0])], type=pa.int64()),
                "neuropil": ["AL_L", "AL_L"], "syn_count": [3, 2],
                **{f"{name}_avg": [0.5, 0.25] for name in audit.NT},
            }), path)
            result = audit.analyze_feather(path, chunk_size=1, sorted_ids=ids, max_batches=None)
            self.assertTrue(result["complete_scan"])
            self.assertEqual(result["rows_read"], 2)
            self.assertEqual(result["synapse_count_sum"], 5)
            self.assertEqual(result["rows_with_both_proofread"], 2)
            self.assertEqual(result["region_rows"], {"AL_L": 2})
            self.assertEqual(result["top_output_by_synapses"][0]["synapses"], 3)
            annotation = folder / "annotation.tsv"
            annotation.write_text(
                "root_id\tpos_x\tpos_y\tpos_z\tsoma_x\tsoma_y\tsoma_z\ttop_nt\tflow\tside\n"
                f"{int(ids[0])}\t1\t2\t3\t1\t2\t3\tacetylcholine\tintrinsic\tleft\n"
                "720575940628857212\t4\t5\t6\t\t\t\tglutamate\tintrinsic\tright\n",
                encoding="utf-8",
            )
            annotations = audit.annotation_analysis(annotation, ids)
            self.assertEqual(annotations["matched_proofread_root_ids"], 1)
            self.assertEqual(annotations["soma_coordinates_present"], 1)

    def test_probability_range_and_nulls(self):
        stats = audit.empty_stats()
        audit.stats_update(pa.array([0.2, None, 1.1], type=pa.float64()), stats)
        result = audit.finish_stats(stats)
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["nulls"], 1)
        self.assertEqual(result["outside_0_1"], 1)
        self.assertAlmostEqual(result["mean"], 0.65)

    def test_release_summary_uses_lowercase_count(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "per_neuron_neuropil_count_pre_783.feather"
            neuron = 720575940628857210
            feather.write_feather(pa.table({
                "pre_pt_root_id": pa.array([neuron, neuron], type=pa.uint64()),
                "neuropil": ["AL_L", "FB"], "count": [3, 4],
            }), path)
            result = audit.analyze_feather(
                path, chunk_size=1,
                sorted_ids=np.array([neuron], dtype=np.uint64), max_batches=None,
            )
            self.assertEqual(result["synapse_count_sum"], 7)
            self.assertEqual(result["region_synapse_counts"], {"FB": 4, "AL_L": 3})
            self.assertEqual(result["unique_proofread_pre_root_ids"], 1)


if __name__ == "__main__":
    unittest.main()
