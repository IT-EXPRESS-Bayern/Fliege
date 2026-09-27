import assert from 'node:assert/strict';
import test from 'node:test';
import { extractAnchorPoints, voxelsToMicrometers } from '../export_anchor_points.mjs';

test('4×4×40 nm voxels become micrometers without changing exact root IDs', () => {
  assert.deepEqual(voxelsToMicrometers(1000, 2000, 300), [4, 8, 12]);
  const tsv = 'root_id\tpos_x\tpos_y\tpos_z\tsuper_class\n' +
    '720575940604737708\t1000\t2000\t300\tdescending\n' +
    '720575940629327659\t2000\t3000\t400\tdescending\n';
  const output = extractAnchorPoints(tsv, { stride: 8, fullClassLimit: 10 });
  assert.equal(output.totalAnchors, 2);
  assert.equal(output.exportedAnchors, 2);
  assert.deepEqual(output.points[0], ['720575940604737708', 4, 8, 12, 0]);
  assert.deepEqual(output.voxelSizeNm, [4, 4, 40]);
});

test('sampling is stable and rejects duplicated or imprecise IDs', () => {
  const tsv = 'root_id\tpos_x\tpos_y\tpos_z\tsuper_class\n' +
    Array.from({ length: 20 }, (_, index) =>
      `${720575940600000000n + BigInt(index)}\t${index}\t2\t3\toptic`).join('\n');
  assert.deepEqual(extractAnchorPoints(tsv, { stride: 4, fullClassLimit: 0 }).points,
    extractAnchorPoints(tsv, { stride: 4, fullClassLimit: 0 }).points);
  assert.equal(extractAnchorPoints(tsv, { stride: 1, fullClassLimit: 0 }).exportedAnchors, 20);
  assert.throws(() => extractAnchorPoints(tsv + '\n720575940600000000\t1\t2\t3\toptic'), /duplicate/);
});
