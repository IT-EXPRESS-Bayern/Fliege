"""Synthetic morphology tests; exercise metadata, IDs, and coordinate units."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pyarrow as pa
import pyarrow.feather as feather
import pyarrow.parquet as parquet

import morphology_audit as audit


class MorphologyAuditTests(unittest.TestCase):
    def test_nblast_column_and_row_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.feather"
            first = 720575940628857210
            second = 720575940628857211
            feather.write_feather(pa.table({
                "index": [f"{first},78112261444987077", f"{second},78112261444987078"],
                f"{first},78112261444987077": [1.0, 0.2],
            }), path)
            result = audit.nblast(path, np.array([first, second], dtype=np.uint64), deep_scan=False)
            self.assertEqual(result["rows"], 2)
            self.assertEqual(result["column_id_coverage"]["matched_proofread_roots"], 1)
            self.assertEqual(result["row_id_coverage"]["matched_proofread_roots"], 2)
            self.assertEqual(result["sampled_score_quality"][f"{first},78112261444987077"]["min"], 0.2)
            self.assertFalse(result["score_scan"]["all_numeric_values_scanned"])

    def test_nblast_deep_scan_checks_columns_beyond_sample(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.feather"
            neuron = 720575940628857210
            matrix = {"index": [str(neuron), str(neuron)]}
            for number in range(7):
                matrix[f"score_{number}"] = [0.2, 0.4]
            matrix["score_6"] = [-0.5, float("nan")]
            feather.write_feather(pa.table(matrix), path)
            roots = np.array([neuron], dtype=np.uint64)
            sampled = audit.nblast(path, roots, deep_scan=False)
            with patch.object(audit, "NB_TARGET_DECOMPRESSED_BYTES", 16):
                complete = audit.nblast(path, roots, deep_scan=True)
            self.assertEqual(sampled["score_scan"]["columns_scanned"], 5)
            self.assertFalse(sampled["score_scan"]["all_numeric_values_scanned"])
            self.assertEqual(complete["score_scan"]["columns_scanned"], 7)
            self.assertEqual(complete["score_scan"]["column_projection_batch_size"], 1)
            self.assertTrue(complete["score_scan"]["all_numeric_values_scanned"])
            self.assertEqual(complete["score_quality"]["negative"], 1)
            self.assertEqual(complete["score_quality"]["nonfinite"], 1)
            self.assertEqual(complete["score_quality"]["min"], -0.5)

    def test_skeleton_parquet_root_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "skeletons.parquet"
            first = 720575940628857210
            second = 720575940628857211
            parquet.write_table(pa.table({
                "root_id": pa.array([first, second], type=pa.uint64()),
                "x": [1.0, 2.0], "y": [3.0, 4.0], "z": [5.0, 6.0],
                "parent_id": [-1, 0],
            }), path)
            result = audit.skeletons(path, np.array([first, second], dtype=np.uint64), deep_scan=False)
            self.assertEqual(result["rows"], 2)
            self.assertEqual(result["id_coverage"]["matched_proofread_roots"], 2)
            self.assertEqual(result["coordinate_quality_sample"]["z"][0]["max"], 6.0)

    def test_nested_swc_coordinates_are_sampled(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested.parquet"
            neuron = 720575940628857210
            parquet.write_table(pa.table({
                "id": pa.array([str(neuron)]),
                "x": pa.array([[1.0, 2.0]]),
                "y": pa.array([[3.0, 4.0]]),
                "z": pa.array([[5.0, 6.0]]),
            }), path)
            result = audit.skeletons(path, np.array([neuron], dtype=np.uint64), deep_scan=False)
            self.assertEqual(result["id_coverage"]["matched_proofread_roots"], 1)
            self.assertEqual(result["coordinate_quality_sample"]["x"][0]["sampled_values"], 2)
            self.assertEqual(result["coordinate_sample_batch_size"], 4)

    def test_nested_swc_deep_scan_reaches_later_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested.parquet"
            roots = np.arange(720575940628857210, 720575940628857220, dtype=np.uint64)
            xs = [[float(number)] for number in range(9)] + [[-3.0]]
            parquet.write_table(pa.table({
                "root_id": pa.array(roots),
                "x": pa.array(xs),
                "y": pa.array([[1.0]] * 10),
                "z": pa.array([[2.0]] * 10),
                "parent_id": pa.array([0] * 10),
            }), path)
            sampled = audit.skeletons(path, roots, deep_scan=False)
            complete = audit.skeletons(path, roots, deep_scan=True)
            self.assertEqual(sampled["numeric_scan"]["rows_scanned"], 8)
            self.assertFalse(sampled["numeric_scan"]["all_recognized_numeric_values_scanned"])
            self.assertEqual(complete["numeric_scan"]["rows_scanned"], 10)
            self.assertTrue(complete["numeric_scan"]["all_recognized_numeric_values_scanned"])
            self.assertEqual(complete["coordinate_quality"]["x"]["min"], -3.0)
            self.assertEqual(complete["id_coverage"]["matched_proofread_roots"], 10)

    def test_actual_skeleton_column_names_are_fully_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nodes.parquet"
            neuron = 720575940628857210
            parquet.write_table(pa.table({
                "node_id": [1, 2, 3], "parent_id": [-1, 1, 2],
                "radius": [5, 4, 3], "x": [0.0, 1.0, 2.0],
                "y": [0.0, 1.0, 2.0], "z": [0.0, 1.0, 2.0],
                "neuron": pa.array([neuron] * 3, type=pa.int64()),
            }), path)
            result = audit.skeletons(path, np.array([neuron], dtype=np.uint64), deep_scan=True)
            self.assertEqual(result["row_grain"], "skeleton_node")
            self.assertEqual(result["id_column"], "neuron")
            self.assertEqual(result["id_coverage"]["parsed_flywire_ids"], 1)
            self.assertEqual(result["id_rows_unparsed"], 0)
            self.assertEqual(result["numeric_scan"]["columns_scanned"], 6)
            self.assertEqual(result["numeric_scan"]["rows_scanned"], 3)
            self.assertTrue(result["numeric_scan"]["all_recognized_numeric_values_scanned"])

    def test_integrity_and_numeric_content_are_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            neuron = 720575940628857210
            feather_path = folder / "scores.feather"
            parquet_path = folder / "skeleton.parquet"
            feather.write_feather(pa.table({"index": [str(neuron)], "score": [0.5]}), feather_path)
            parquet.write_table(pa.table({
                "root_id": pa.array([neuron], type=pa.uint64()),
                "swc": ["1 3 0 0 0 1 -1"],
            }), parquet_path)
            files = {
                feather_path.name: (feather_path.stat().st_size, audit.md5_file(feather_path)),
                parquet_path.name: (parquet_path.stat().st_size, audit.md5_file(parquet_path)),
            }
            with patch.object(audit, "MORPHOLOGY_FILES", files):
                report = audit.analyze_morphology(folder, np.array([neuron], dtype=np.uint64), False, True)
            self.assertTrue(report["integrity_complete"])
            self.assertTrue(report["structure_complete"])
            self.assertFalse(report["numeric_content_full_scan"])
            self.assertTrue(report["incomplete"])
            self.assertFalse(report["files"][parquet_path.name]["numeric_content_full_scan"])


if __name__ == "__main__":
    unittest.main()
