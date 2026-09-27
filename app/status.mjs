import { readFile, stat } from 'node:fs/promises';
import { join } from 'node:path';

export const GRAPH_FILES = [
  'nodes.u64', 'offsets.u32', 'targets.u32', 'synapses.u32',
  'nt_probs.u8', 'annotations.json',
];
/** Check availability and manifest sizes without reading large graph arrays. */
export async function inspectBrainGraph(directory, io = { readFile, stat }) {
  let manifest;
  try {
    manifest = JSON.parse(await io.readFile(join(directory, 'manifest.json'), 'utf8'));
  } catch (error) {
    return error.code === 'ENOENT'
      ? { state: 'missing', reason: 'Graph noch nicht erstellt' }
      : { state: 'error', reason: 'Graph-Manifest nicht lesbar' };
  }
  if (manifest.schema !== 'brain-csr-v1' || !Number.isInteger(manifest.node_count) ||
      manifest.node_count <= 0 || !Number.isInteger(manifest.edge_count) || manifest.edge_count < 0) {
    return { state: 'error', reason: 'Unpassendes Graph-Manifest' };
  }
  for (const name of GRAPH_FILES) {
    const expected = manifest.files?.[name]?.bytes;
    if (!Number.isSafeInteger(expected) || expected < 0) {
      return { state: 'error', reason: `Manifest-Eintrag fehlt: ${name}` };
    }
    try {
      const file = await io.stat(join(directory, name));
      if (!file.isFile() || file.size !== expected) {
        return { state: 'incomplete', reason: `Graphdatei unvollständig: ${name}` };
      }
    } catch {
      return { state: 'incomplete', reason: `Graphdatei fehlt: ${name}` };
    }
  }
  return {
    state: 'ready',
    reason: 'Graphdateien vorhanden',
    schema: manifest.schema,
    dataset: manifest.dataset,
    nodeCount: manifest.node_count,
    edgeCount: manifest.edge_count,
    synapseCount: Number.isSafeInteger(manifest.synapse_count) ? manifest.synapse_count : null,
    sourceFile: typeof manifest.sources?.connections?.file === 'string'
      ? manifest.sources.connections.file : null,
  };
}

/** Small annotation excerpt for inspection; names are candidates, not motor outputs. */
export async function inspectBrainCandidates(directory, io = { readFile }) {
  const annotations = JSON.parse(await io.readFile(join(directory, 'annotations.json'), 'utf8'));
  if (!Array.isArray(annotations)) throw new TypeError('Expected annotation array');
  const candidates = annotations.flatMap((row) => {
    if (!row || typeof row.id !== 'string') return [];
    const label = ['DNa02', 'DNg13'].find((name) =>
      row.cell_type === name || row.hemibrain_type === name);
    if (!label) return [];
    return [{ rootId: row.id, label, side: row.side || 'unbekannt',
      flow: row.flow || 'unbekannt', superClass: row.super_class || 'unbekannt' }];
  });
  return { source: 'FlyWire-Annotationen v2.1.0 · annotations.json', candidates };
}
