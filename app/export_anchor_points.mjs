import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const sourcePath = resolve(here, '../data/flywire_annotations_v2.1.0/Supplemental_file1_neuron_annotations.tsv');
const outputPath = resolve(here, 'data/brain-anchor-points.json');
const fullOutputPath = resolve(here, 'data/brain-anchor-points-all.json');
export const VOXEL_SIZE_NM = [4, 4, 40];

export function voxelsToMicrometers(x, y, z) {
  return [Number((x * 0.004).toFixed(3)), Number((y * 0.004).toFixed(3)),
    Number((z * 0.04).toFixed(3))];
}

function stableHash(value) {
  let hash = 2166136261;
  for (let i = 0; i < value.length; i++) {
    hash = Math.imul(hash ^ value.charCodeAt(i), 16777619) >>> 0;
  }
  return hash;
}

/**
 * Select all classes with <= fullClassLimit cells and a deterministic fraction
 * of the larger classes. Every output point still comes from a measured row.
 */
export function extractAnchorPoints(tsvText, { stride = 8, fullClassLimit = 2500 } = {}) {
  if (!Number.isInteger(stride) || stride < 1 || !Number.isInteger(fullClassLimit) || fullClassLimit < 0) {
    throw new TypeError('Invalid sampling parameters');
  }
  const lines = tsvText.trimEnd().split(/\r?\n/);
  const header = lines.shift()?.split('\t') || [];
  const column = Object.fromEntries(header.map((name, index) => [name, index]));
  for (const required of ['root_id', 'pos_x', 'pos_y', 'pos_z', 'super_class']) {
    if (column[required] === undefined) throw new TypeError(`Missing column: ${required}`);
  }
  const rows = [];
  const ids = new Set();
  const classCountsFull = {};
  for (const line of lines) {
    if (!line) continue;
    const fields = line.split('\t');
    const id = fields[column.root_id];
    const raw = ['pos_x', 'pos_y', 'pos_z'].map((key) => fields[column[key]]);
    if (!id || raw.some((value) => value === '')) continue;
    if (!/^[1-9]\d*$/.test(id) || ids.has(id)) throw new TypeError(`Invalid or duplicate root ID: ${id}`);
    const voxels = raw.map(Number);
    if (!voxels.every(Number.isSafeInteger)) throw new TypeError(`Invalid anchor voxels for ${id}`);
    ids.add(id);
    const category = fields[column.super_class] || 'unbekannt';
    const um = voxelsToMicrometers(...voxels);
    rows.push({ id, um, category });
    classCountsFull[category] = (classCountsFull[category] || 0) + 1;
  }
  const classes = Object.keys(classCountsFull).sort((a, b) =>
    classCountsFull[b] - classCountsFull[a] || a.localeCompare(b));
  const classIndex = Object.fromEntries(classes.map((name, index) => [name, index]));
  const classCountsExported = Object.fromEntries(classes.map((name) => [name, 0]));
  const min = [Infinity, Infinity, Infinity];
  const max = [-Infinity, -Infinity, -Infinity];
  const points = [];
  for (const row of rows) {
    if (classCountsFull[row.category] > fullClassLimit && stableHash(row.id) % stride !== 0) continue;
    for (let axis = 0; axis < 3; axis++) {
      min[axis] = Math.min(min[axis], row.um[axis]);
      max[axis] = Math.max(max[axis], row.um[axis]);
    }
    points.push([row.id, ...row.um, classIndex[row.category]]);
    classCountsExported[row.category]++;
  }
  return {
    schema: 'flywire-anchor-points-v1',
    source: 'FlyWire Supplemental_file1_neuron_annotations.tsv v2.1.0',
    coordinateColumns: ['pos_x', 'pos_y', 'pos_z'],
    voxelSizeNm: VOXEL_SIZE_NM,
    units: 'µm',
    selection: { method: 'deterministic FNV-1a root-ID sampling', stride,
      fullClassLimit, rule: 'all cells in classes at or below limit; 1/stride of larger classes' },
    totalAnchors: rows.length,
    exportedAnchors: points.length,
    classes,
    classCountsFull,
    classCountsExported,
    boundsUm: { min, max },
    points,
  };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const source = await readFile(sourcePath);
  const digest = createHash('sha256').update(source).digest('hex');
  const output = extractAnchorPoints(source.toString('utf8'));
  output.sourceSha256 = digest;
  await writeFile(outputPath, JSON.stringify(output));
  const full = extractAnchorPoints(source.toString('utf8'), { stride: 1, fullClassLimit: 0 });
  full.sourceSha256 = digest;
  await writeFile(fullOutputPath, JSON.stringify(full));
  console.log(JSON.stringify({ output: outputPath, totalAnchors: output.totalAnchors,
    exportedAnchors: output.exportedAnchors, bytes: (await readFile(outputPath)).byteLength,
    fullOutput: fullOutputPath, fullAnchors: full.exportedAnchors,
    fullBytes: (await readFile(fullOutputPath)).byteLength }));
}
