/** Read a local built graph through the browser loader and run one smoke step.
 * Usage: node brain/verify_graph.mjs [brain/graph-v783]
 */
import { readFile } from "node:fs/promises";
import { resolve, basename, join } from "node:path";
import { fileURLToPath } from "node:url";
import { dirname } from "node:path";
import { loadBrainGraph } from "./web.mjs";
import { BrainEngine } from "./engine.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const directory = resolve(process.argv[2] ?? join(here, "graph-v783"));
globalThis.fetch = async url => {
  const name = basename(new URL(url, "http://local.test").pathname);
  try {
    return new Response(await readFile(join(directory, name)), { status: 200 });
  } catch {
    return new Response("missing", { status: 404 });
  }
};

const graph = await loadBrainGraph("/graph");
if (graph.ids.length === 0) throw new Error("Graph is empty");
const firstId = graph.ids[0].toString();
if (graph.indexOf(firstId) !== 0) throw new Error("Exact-ID lookup failed");
const engine = new BrainEngine(graph, { background: {
  eventsPerMs: 10, amplitude: 2, seed: 42, targets: [firstId],
} });
const state = engine.step();
if (state.backgroundEvents < 1 || state.spikeCount < 1) {
  throw new Error("Background drive did not activate the graph");
}
console.log(JSON.stringify({
  nodeCount: graph.ids.length,
  edgeCount: graph.targets.length,
  synapseCount: graph.manifest.synapse_count,
  dataset: graph.manifest.dataset,
  firstId,
  backgroundEvents: state.backgroundEvents,
  spikeCount: state.spikeCount,
}));
