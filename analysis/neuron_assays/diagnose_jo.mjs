/** Follow-up of a failed qualitative prediction, with the same frozen dynamics. */
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';
import { AssayEngine } from './assay-engine.mjs';
import { project,loadGraph,readJSON } from './graph.mjs';

const graph=loadGraph(), data=readJSON('app/data/neuron_assays.json');
const annotation=new Map(graph.annotations.map(r=>[r.id,r]));
const targets=['720575940630907434','720575940616185531','720575940629806974'];
const targetIndexes=new Map(targets.map(id=>[graph.indexOf(id),id]));
const incomingBySource=new Map();
for(let src=0;src<graph.ids.length;src++){
  for(let edge=graph.offsets[src];edge<graph.offsets[src+1];edge++){
    const target=targetIndexes.get(graph.targets[edge]);if(!target)continue;
    const nt=edge*6,sign=(graph.ntProbs[nt]-graph.ntProbs[nt+1]-graph.ntProbs[nt+2])/255;
    const weight=data.dynamics.synapseGain*Math.log1p(graph.synapses[edge])*sign;
    if(!weight)continue;
    if(!incomingBySource.has(src))incomingBySource.set(src,[]);
    incomingBySource.get(src).push({target,weight,synapses:graph.synapses[edge]});
  }
}
const results=[];
for(const condition of ['original_replay','count_phase_matched_60'])for(const scenarioID of ['jo_ce','jo_f']){
  const scenario=data.scenarios.find(s=>s.id===scenarioID);
  const reference=scenario.trials.find(t=>t.id==='reference');
  const ids=condition==='original_replay'?scenario.input.ids:scenario.input.ids.slice(0,60);
  const phases=ids.map((id,i)=>condition==='original_replay'?Number(BigInt(id)%1009n)/1009:i/60);
  const engine=new AssayEngine(graph,data.dynamics),contributions=new Map(),samples=[];
  const readoutCounts=Object.fromEntries(targets.map(id=>[id,0]));
  for(let t=0;t<600;t++){
    const elapsed=t-100;
    const forceSpikes=t>=100&&t<500?ids.filter((id,i)=>
      Math.floor((elapsed+1)*0.15+phases[i])>Math.floor(elapsed*0.15+phases[i])):[];
    const r=engine.step({forceSpikes,readout:targets,maxReportedSpikes:0});
    const active=new Set(r.spikeIndices);
    const sample={tMs:r.timeMs,readout:r.readout,spikes:Object.fromEntries(targets.map(id=>[id,Number(active.has(graph.indexOf(id)))]))};
    samples.push(sample);
    for(const id of targets)if(t>=100&&t<500)readoutCounts[id]+=sample.spikes[id];
    if(condition==='original_replay'){
      for(const id of targets){
        assert.equal(sample.readout[id],reference.samples[t].voltageByReadout[id]);
        assert.equal(sample.spikes[id],reference.samples[t].spikesByReadout[id]);
      }
    }
    // These events arrive on the next step. Report delivery and blocked current separately.
    if(t===599)continue;
    for(const src of r.spikeIndices)for(const edge of incomingBySource.get(src)||[]){
      const source=graph.ids[src].toString(),key=`${source}:${edge.target}`;
      if(!contributions.has(key))contributions.set(key,{source,target:edge.target,
        sourceCellType:annotation.get(source)?.cell_type||'',sourceCellClass:annotation.get(source)?.cell_class||'',
        sourceIsInput:ids.includes(source),edgeSynapses:edge.synapses,eventWeight:edge.weight,
        deliveredEvents:0,deliveredPositiveCurrent:0,deliveredNegativeCurrent:0,
        acceptedEvents:0,acceptedPositiveCurrent:0,acceptedNegativeCurrent:0,blockedEvents:0});
      const c=contributions.get(key),positive=edge.weight>0;
      c.deliveredEvents++;c[positive?'deliveredPositiveCurrent':'deliveredNegativeCurrent']+=edge.weight;
      const blocked=engine.stepNumber+1<=engine.refractoryUntil[graph.indexOf(edge.target)];
      if(blocked)c.blockedEvents++;
      else{c.acceptedEvents++;c[positive?'acceptedPositiveCurrent':'acceptedNegativeCurrent']+=edge.weight;}
    }
  }
  const rows=[...contributions.values()].sort((a,b)=>Math.abs(b.acceptedPositiveCurrent+b.acceptedNegativeCurrent)-Math.abs(a.acceptedPositiveCurrent+a.acceptedNegativeCurrent));
  const totals=Object.fromEntries(targets.map(id=>[id,{
    stimulusRateHz:readoutCounts[id]/0.4,
    deliveredPositiveCurrent:rows.filter(c=>c.target===id).reduce((n,c)=>n+c.deliveredPositiveCurrent,0),
    deliveredNegativeCurrent:rows.filter(c=>c.target===id).reduce((n,c)=>n+c.deliveredNegativeCurrent,0),
    acceptedPositiveCurrent:rows.filter(c=>c.target===id).reduce((n,c)=>n+c.acceptedPositiveCurrent,0),
    acceptedNegativeCurrent:rows.filter(c=>c.target===id).reduce((n,c)=>n+c.acceptedNegativeCurrent,0),
    fromABN1:rows.find(c=>c.source===targets[0]&&c.target===id)||null,
  } ]));
  results.push({condition,scenario:scenarioID,inputIDs:ids,inputCount:ids.length,doseHz:150,
    sourcePhaseRule:condition==='original_replay'?'uint64_id_mod1009':'sorted_input_index/60',
    matchesSavedReference:condition==='original_replay'?true:null,totals,contributions:rows,samples});
  console.log(JSON.stringify({condition,scenario:scenarioID,totals}));
}
const output={schema:'fly.jo-diagnostic.v1',dynamics:data.dynamics,generatedAt:new Date().toISOString(),
  interpretation:'Diagnostic only: quantify current events under frozen sign/gain rules; accepted excludes refractory-step input but is not a measured conductance. Spikes/reset and leak make summed current non-equivalent to voltage.',
  countControl:'CE first60IDs in numeric-string sorted order; F60; identical index phases and150Hz schedules. Single deterministic subset, not sampling inference.',
  results};
writeFileSync(resolve(project,'analysis/neuron_assays/jo_diagnostic.json'),JSON.stringify(output,null,2)+'\n');
