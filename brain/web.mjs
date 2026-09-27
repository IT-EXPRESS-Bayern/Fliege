/** Exact-ID browser reader for brain-csr-v1. All IDs exposed as BigInt/string. */
export async function loadBrainGraph(baseUrl) {
  const base = baseUrl.replace(/\/$/, "");
  const manifest = await (await fetch(`${base}/manifest.json`)).json();
  if (manifest.schema !== "brain-csr-v1") throw new Error("Unsupported graph schema");
  const names = ["nodes.u64", "offsets.u32", "targets.u32", "synapses.u32", "nt_probs.u8"];
  const buffers = await Promise.all(names.map(async name => {
    const response = await fetch(`${base}/${name}`);
    if (!response.ok) throw new Error(`Unable to fetch ${name}: ${response.status}`);
    const data = await response.arrayBuffer();
    if (data.byteLength !== manifest.files[name].bytes) throw new Error(`Wrong size: ${name}`);
    return data;
  }));
  const [idBuf, offsetBuf, targetBuf, synBuf, ntBuf] = buffers;
  const ids = new BigUint64Array(idBuf);
  const offsets = new Uint32Array(offsetBuf);
  const targets = new Uint32Array(targetBuf);
  const synapses = new Uint32Array(synBuf);
  const ntProbs = new Uint8Array(ntBuf);
  if (ids.length !== manifest.node_count || offsets.length !== ids.length + 1 ||
      targets.length !== manifest.edge_count || synapses.length !== targets.length ||
      ntProbs.length !== targets.length * 6 || offsets[ids.length] !== targets.length) {
    throw new Error("Inconsistent graph array lengths");
  }
  // Avoid Number(rootId): FlyWire IDs exceed Number.MAX_SAFE_INTEGER.
  const indexById = new Map(Array.from(ids, (id, index) => [id.toString(), index]));
  const indexOf = id => {
    if (typeof id === "number") throw new TypeError("Root IDs must be BigInt or decimal strings");
    const index = indexById.get(String(id));
    if (index === undefined) throw new Error(`Unknown root ID: ${String(id)}`);
    return index;
  };
  const outgoingIndex = index => {
    if (!Number.isInteger(index) || index < 0 || index >= ids.length) throw new RangeError("Node index out of range");
    const start = offsets[index], end = offsets[index + 1];
    return { start, end, targets: targets.subarray(start, end),
      synapses: synapses.subarray(start, end),
      ntProbs: ntProbs.subarray(start * 6, end * 6) };
  };
  const outgoing = id => outgoingIndex(indexOf(id));
  return { manifest, ids, offsets, targets, synapses, ntProbs, indexOf, outgoing, outgoingIndex };
}
