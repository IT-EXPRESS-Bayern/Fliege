# FlyWire graph preparation and exploratory simulation

`build.py` converts the FlyWire FAFB v783 *proofread* connectivity table or the
Codex v783 Princeton export into a
directed compressed sparse row (CSR) graph. It groups the original
`(pre, post, neuropil)` rows into one directed edge per ordered neuron pair.
Synapse counts are summed; six neurotransmitter channels are weighted by
synapse count. All 139,255
proofread root IDs remain as nodes, including nodes with no outgoing edge.

The default is **one or more synapses per edge**. Use `--min-synapses 5` for a
smaller, more conservative graph like the threshold used in many published
analyses. An edge is a neuron pair; it can contain multiple synapses.

## Inputs

Place the files under the sibling `data/` directory:

* `data/flywire_fafb_v783/proofread_connections_783.feather` and
  `proofread_root_ids_783.npy` from the [FlyWire v783 Zenodo archive](https://doi.org/10.5281/zenodo.10676866).
  The Feather table includes six source-predicted mean neurotransmitter
  probabilities for every connection row.
* Alternatively, `data/codex_fafb_v783/connections_princeton.csv.gz` from the
  [public Codex v783 Princeton export](https://storage.googleapis.com/flywire-data/codex/data/fafb/783/connections_princeton.csv.gz).
  Its `nt_type` column is **one categorical prediction**, not six probabilities.
  The builder maps it to one-hot channels before combining rows. This Codex
  export is already filtered: in the verified file, every ordered neuron pair
  has at least five synapses across neuropils. A row for one neuropil can have
  fewer. `--min-synapses 1` cannot restore omitted weak pairs. The manifest
  records its URL, verified published MD5, SHA-256,
  input schema and altered transmitter meaning.
* `data/flywire_annotations_v2.1.0/Supplemental_file1_neuron_annotations.tsv`
  from the [pinned v2.1.0 FlyWire annotations release](https://github.com/flyconnectome/flywire_annotations/releases/tag/v2.1.0).

The builder also accepts CSV, TSV and gzipped CSV/TSV tables with either input
schema. It reads the Feather file batch by batch and sorts runs on disk. It
does not need the 9.5 GB synapse-level image table.

Create a project-local environment and build (PowerShell example):

```powershell
& '<USER_HOME>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m venv brain/.venv
& brain/.venv/Scripts/python.exe -m pip install -r brain/requirements.txt --index-url https://pypi.org/simple
& brain/.venv/Scripts/python.exe brain/build.py --out brain/graph-v783
```

To build the browser graph now from the smaller Codex export:

```powershell
& '<USER_HOME>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' brain/build.py --connections data/codex_fafb_v783/connections_princeton.csv.gz --root-ids data/flywire_fafb_v783/proofread_root_ids_783.npy --annotations data/flywire_annotations_v2.1.0/Supplemental_file1_neuron_annotations.tsv --out brain/graph-v783 --dataset flywire_fafb_v783_codex_princeton
```

`--out` can be any directory. `--dataset` changes the dataset label without
changing the binary schema. Rebuilding a different dataset needs a compatible
connection table and an exact root-ID NPY file. `--chunk-rows` bounds temporary
memory. Temporary sorted runs are automatically removed on success. The
manifest records SHA-256 digests of every input and output for provenance.

## Browser format: `brain-csr-v1`

All arrays are little-endian. Node indexes are assigned by sorting exact
unsigned 64-bit root IDs. **Never parse a root ID into a JavaScript Number**;
use `BigInt` or its decimal string. `web.mjs` exposes a ready-to-use loader:

```js
import { loadBrainGraph } from "./brain/web.mjs";
const graph = await loadBrainGraph("/brain/graph-v783");
const i = graph.indexOf("720575940600000001");
const edges = graph.outgoing("720575940600000001");
```

| File | Element type | Shape | Meaning |
| --- | --- | --- | --- |
| `nodes.u64` | uint64 | N | Sorted root IDs |
| `offsets.u32` | uint32 | N+1 | CSR starts; outgoing edges for node `i` occupy `[offsets[i], offsets[i+1])` |
| `targets.u32` | uint32 | E | Target node indexes |
| `synapses.u32` | uint32 | E | Summed synapse counts |
| `nt_probs.u8` | uint8 | E×6 | Mean transmitter scores, each divided by 255; source meaning and order in manifest |
| `annotations.json` | JSON array | N | Node metadata aligned with `nodes.u64`, IDs as decimal strings |
| `manifest.json` | JSON | — | Counts, schema, source digests and encoding |

For the full unfiltered v783 table with a one-synapse threshold, expect about
15 million neuron-pair edges and roughly 200 MB of binary arrays. The filtered
Codex export produces fewer edges. A web app may load an
edge-filtered graph or a selected subgraph for lower memory use. The format is
independent of display code and suitable for HTTP range serving or static
hosting. The annotations are a separate JSON file so a renderer can skip them
when it needs only topology.

## Simulation bridge

`simulation.py` is an **exploratory numerical model**. It uses a leaky voltage,
a spike threshold, a refractory period and one-step delayed edge events. ACh
probability contributes positive drive; GABA and glutamate contribute negative
drive. Dopamine, serotonin and octopamine are preserved in the graph but their
context-dependent effects are not modeled. Weight magnitude is
`synapse_gain × log1p(synapse_count)` in arbitrary units. This is not a
physiologically calibrated brain, behavioral prediction or conscious copy.

Run an NDJSON process, then write one JSON request per line to stdin. Root IDs
are strings. Each line returns one JSON response. `steps` repeats the same
stimulus for up to 1000 time steps; default `dt_ms` is 1 ms.

```powershell
& brain/.venv/Scripts/python.exe brain/simulation.py --graph brain/graph-v783
```

```json
{"stimuli":{"720575940600000001":1.2},"readout":["720575940600000009"]}
```

```json
{"force_spikes":["720575940600000001"],"readout":["720575940600000009"]}
```

Responses contain `step`, `time_ms`, `spike_count`, exact-ID `spikes`, and
`readout` voltage values. An app can send sensory inputs as `stimuli` or
`force_spikes` and consume named motor-neuron readouts. The graph and interface
do not imply that FAFB contains the fly's body or ventral nerve cord.

## Browser Worker and app bridge

The optional browser engine runs in a module Worker, leaving the display
thread responsive. `engine.mjs` updates only activated neurons, applies decay
when they are next touched, and traverses outgoing edges only for neurons that
spike. The full graph must still be fetched into browser memory once. The
`spikes` reply is capped at 256 IDs by default; `spikeCount` keeps the full
count. Set `maxReportedSpikes` explicitly when more IDs are needed.

```js
const worker = new Worker("/brain/worker.mjs", { type: "module" });
worker.onmessage = ({ data }) => console.log(data);
worker.postMessage({
  type: "load", requestId: "load-1", baseUrl: "/brain/graph-v783",
  dynamics: {
    dtMs: 1, tauMs: 20, synapseGain: 0.1,
    background: { eventsPerMs: 10, amplitude: 1.2, seed: 12345 },
  },
});
// Send this after the "loaded" reply:
worker.postMessage({
  type: "step", requestId: "step-1", timestampMs: performance.now(),
  stimuli: { "720575940600000001": 1.2 },
  readout: ["720575940600000009"],
});
```

Step responses contain `readout`, `spikes`, `spikeCount`, `activeNodes`, and
`traversedEdges`. `backgroundEvents` counts spontaneous events. `steps`
repeats the supplied stimulus over 1–1000 time
steps. A `reset` request clears dynamics. Errors are returned as
`{type:"error",message,requestId}`.

`background` is an **optional, hypothetical** source of independent Poisson
events, implemented with a seeded random generator. It can make the graph
active without external stimuli or a user-specified goal. It is off by default;
its frequency, amplitude and target distribution are modeling choices, not
measured FlyWire data. Set `targets` to exact root-ID strings to limit where
events enter. Its event scheduler is sparse and does not scan every neuron on
each step. The seed makes a run repeatable after `reset`.

To connect to the display's `fly.control.v1` frames, supply an **explicit
experimental** motor map on `load`:

```js
worker.postMessage({
  type: "load", baseUrl: "/brain/graph-v783",
  motorMap: {
    forward: ["<validated forward-related root ID>"],
    turnLeft: [], turnRight: [], wing: [], groom: [],
  },
  motorOptions: { smoothing: 0.2 },
});
```

When a step request includes the main thread's `performance.now()` value as
`timestampMs`, the reply includes `controlFrame`. Pass it to
`window.FlyDemo.submitControlFrame(data.controlFrame)`. Each channel is a
smoothed fraction of its mapped neurons that spiked; `turn` is the right minus
left difference. This mapping is a simple adapter to a demonstration body.
No sensory or motor neuron IDs are assigned by default, and the method does
not model muscles, wing mechanics, or the ventral nerve cord.

The pinned annotation table contains candidate descending neurons DNa02
(`720575940604737708` right; `720575940629327659` left) and DNg13
(`720575940616471052` left; `720575940606112940` right). These are exact IDs
present in the built graph. In [Yang et al., *Fine-grained descending control
of steering in walking Drosophila*](https://pmc.ncbi.nlm.nih.gov/articles/PMC10614758/),
unilateral DNa02 activation and DNg13 depolarization each produced a turn
toward the stimulated cell's soma side, with no significant forward-velocity
effect. An exploratory `turnLeft`/`turnRight` grouping by soma side is thus
biologically motivated at the **cell-type** level. Transferring that result to
these particular FAFB cells and translating spike fractions into display
rotation are still uncalibrated model assumptions. That study does not justify
mapping these cells to `forward`.

Run the small synthetic tests without the large downloads:

```powershell
& '<USER_HOME>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest brain.test_brain -v
& '<USER_HOME>\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test brain/test_engine.mjs
```

With a built graph present, `node brain/verify_graph.mjs brain/graph-v783`
exercises the same browser loader against the actual binary files and takes a
single reproducible background-driven simulation step.
