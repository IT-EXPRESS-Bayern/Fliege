import test from 'node:test';
import assert from 'node:assert/strict';
import { BrainEngine } from '../../brain/engine.mjs';
import { AssayEngine } from './assay-engine.mjs';

const ids = ['720575940600000001', '720575940600000009', '720575940600000017'];
function fixture() {
  return {manifest:{schema:'brain-csr-v1'},ids:ids.map(BigInt),offsets:Uint32Array.from([0,1,2,2]),
    targets:Uint32Array.from([1,2]),synapses:Uint32Array.from([20,20]),
    ntProbs:Uint8Array.from([255,0,0,0,0,0,255,0,0,0,0,0]),
    indexOf(id) {const i=ids.indexOf(String(id));if(i<0) throw new Error('unknown'); return i;}};
}
test('assay copy exactly matches production without silencing', () => {
  const a=new BrainEngine(fixture(),{synapseGain:0.4});
  const b=new AssayEngine(fixture(),{synapseGain:0.4});
  for(let i=0;i<100;i++){
    const input={forceSpikes:i%7===0?[ids[0]]:[],readout:ids};
    assert.deepEqual(a.step(input),b.step(input));
  }
});
test('upstream ablation blocks propagated activity and forced spikes', () => {
  const engine=new AssayEngine(fixture(),{synapseGain:0.4,silenced:[ids[1]]});
  engine.step({forceSpikes:[ids[0]]});
  for(let i=0;i<10;i++){
    const r=engine.step({forceSpikes:[ids[1]],readout:ids});
    assert.equal(r.spikeCount,0); assert.equal(r.readout[ids[1]],0); assert.equal(r.readout[ids[2]],0);
  }
});
test('source silencing blocks all outgoing events', () => {
  const engine=new AssayEngine(fixture(),{synapseGain:0.4,silenced:[ids[0]]});
  const r=engine.step({forceSpikes:[ids[0]],readout:ids});
  assert.equal(r.spikeCount,0); assert.equal(r.traversedEdges,0);
});
