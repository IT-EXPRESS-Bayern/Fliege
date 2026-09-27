import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';

export const project = resolve(import.meta.dirname, '../..');
export const sha = (bytes) => createHash('sha256').update(bytes).digest('hex');
export const readJSON = (path) => JSON.parse(readFileSync(resolve(project, path), 'utf8'));

export function loadGraph() {
  const base = resolve(project, 'brain/graph-original-v783');
  const manifest = JSON.parse(readFileSync(resolve(base, 'manifest.json'), 'utf8'));
  const checksums = {};
  const arrays = {};
  for (const [file, name, Type] of [
    ['nodes.u64', 'ids', BigUint64Array], ['offsets.u32', 'offsets', Uint32Array],
    ['targets.u32', 'targets', Uint32Array], ['synapses.u32', 'synapses', Uint32Array],
    ['nt_probs.u8', 'ntProbs', Uint8Array],
  ]) {
    const bytes = readFileSync(resolve(base, file));
    if (bytes.byteLength !== manifest.files[file].bytes) throw new Error(`Size mismatch: ${file}`);
    checksums[file] = sha(bytes);
    if (checksums[file] !== manifest.files[file].sha256) throw new Error(`SHA mismatch: ${file}`);
    arrays[name] = new Type(bytes.buffer, bytes.byteOffset, bytes.byteLength / Type.BYTES_PER_ELEMENT);
  }
  const index = new Map(Array.from(arrays.ids, (id, i) => [id.toString(), i]));
  const annotationBytes=readFileSync(resolve(base,'annotations.json'));
  checksums['annotations.json']=sha(annotationBytes);
  if(checksums['annotations.json']!==manifest.files['annotations.json'].sha256)throw new Error('Annotation SHA mismatch');
  const annotations = JSON.parse(annotationBytes);
  return { manifest, ...arrays, annotations, checksums,
    indexOf(id) {
      if (typeof id === 'number') throw new TypeError('IDs must be strings or BigInt');
      const i = index.get(String(id));
      if (i === undefined) throw new Error(`Unknown graph ID: ${id}`);
      return i;
    },
  };
}
