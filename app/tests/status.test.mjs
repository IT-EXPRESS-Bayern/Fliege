import assert from 'node:assert/strict';
import test from 'node:test';
import { basename } from 'node:path';
import { GRAPH_FILES, inspectBrainCandidates, inspectBrainGraph } from '../status.mjs';
import { ORIGINAL_GRAPH_DATASET, matchesLoadedOriginalGraph } from '../brain-bridge.mjs';

const manifest = {
  schema: 'brain-csr-v1', dataset: ORIGINAL_GRAPH_DATASET, node_count: 2, edge_count: 1,
  synapse_count: 3, sources: { connections: { file: 'proofread_connections_783.feather' } },
  files: Object.fromEntries(GRAPH_FILES.map((name) => [name, { bytes: 8 }])),
};
const fakeIo = {
  async readFile() { return JSON.stringify(manifest); },
  async stat() { return { isFile: () => true, size: 8 }; },
};

test('graph status requires all manifest-listed files at the expected sizes', async () => {
  const ready = await inspectBrainGraph('unused', fakeIo);
  assert.equal(ready.state, 'ready');
  assert.equal(ready.synapseCount, 3);
  assert.equal(ready.sourceFile, 'proofread_connections_783.feather');
  const incomplete = await inspectBrainGraph('unused', {
    ...fakeIo,
    async stat(path) { return { isFile: () => true, size: basename(path) === 'targets.u32' ? 4 : 8 }; },
  });
  assert.equal(incomplete.state, 'incomplete');
  const missing = await inspectBrainGraph('unused', {
    async readFile() { throw Object.assign(new Error('missing'), { code: 'ENOENT' }); },
  });
  assert.equal(missing.state, 'missing');
});

test('filtered graph cannot be mistaken for the full original worker graph', () => {
  const server = { state: 'ready', dataset: ORIGINAL_GRAPH_DATASET, nodeCount: 139255,
    edgeCount: 15091983 };
  const loaded = { dataset: ORIGINAL_GRAPH_DATASET, nodeCount: 139255, edgeCount: 15091983 };
  assert.equal(matchesLoadedOriginalGraph(server, loaded), true);
  assert.equal(matchesLoadedOriginalGraph(server, { ...loaded, edgeCount: 3732460 }), false);
  assert.equal(matchesLoadedOriginalGraph(server, { ...loaded, dataset: 'flywire_fafb_v783_codex_princeton' }), false);
});

test('candidate excerpt keeps exact IDs and annotation labels without assigning motor channels', async () => {
  const result = await inspectBrainCandidates('unused', {
    async readFile() { return JSON.stringify([
      { id: '720575940604737708', hemibrain_type: 'DNa02', side: 'right', flow: 'efferent' },
      { id: '720575940606112940', cell_type: 'DNg13', side: 'right', flow: 'efferent' },
      { id: '720575940600000000', cell_type: 'other' },
    ]); },
  });
  assert.deepEqual(result.candidates.map((item) => item.rootId),
    ['720575940604737708', '720575940606112940']);
  assert.deepEqual(result.candidates.map((item) => item.label), ['DNa02', 'DNg13']);
  assert.equal('motorChannel' in result.candidates[0], false);
});
