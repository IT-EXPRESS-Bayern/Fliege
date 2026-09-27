/** Frozen, bounded full-graph model experiments. No parameter fitting to outputs. */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { gzipSync } from 'node:zlib';
import { AssayEngine } from './assay-engine.mjs';
import { project, loadGraph, readJSON, sha } from './graph.mjs';

const out=resolve(project,'analysis/neuron_assays');
mkdirSync(resolve(out,'trajectories'),{recursive:true});
const graph=loadGraph();
const supplement=readJSON('data/research_sources/shiu/derived/shiu_supplement_index.json');
const eligible=supplement.candidates.filter(c=>c.v783_exact_root_present&&c.shiu_v783_completeness_exact_root_present);
const idsFor=(cats)=>[...new Set(eligible.filter(c=>cats.includes(c.category)).map(c=>c.source_root_id))].sort();
const aBN1='720575940630907434';
const readouts=[
  {id:aBN1,label:'aBN1',role:'Antennenputz-Interneuron, Workbook-Identität in v783 nicht unabhängig bestätigt',bodyChannel:null,sideStatus:'no lateral mapping'},
  {id:'720575940616185531',label:'aDN1 (Workbook _l)',role:'Absteigender Antennenputz-Kandidat',bodyChannel:'groom',sideStatus:'Workbook links / v783 rechts: ungeklärt'},
  {id:'720575940629806974',label:'aDN2 (Workbook _l)',role:'Absteigender Antennenputz-Kandidat',bodyChannel:'groom',sideStatus:'Workbook links / v783 rechts: ungeklärt'},
  {id:'720575940660219265',label:'MN9 rechts',role:'Motorneuron für Muskel9 / Proboscis-Kandidat',bodyChannel:'proboscis',sideStatus:'Tastekin2026 rechts'},
  {id:'720575940618238523',label:'MN9 links',role:'Motorneuron für Muskel9 / Proboscis-Kandidat',bodyChannel:'proboscis',sideStatus:'Tastekin2026 links, unabhängig vom fehlenden Shiu-v630-Root'},
  {id:'720575940604737708',label:'DNa02 (Stürner L)',role:'Absteigender Typ mit publizierten Steuerungseffekten',bodyChannel:null,sideStatus:'Stürner L / Originalannotation rechts: Seitenkonvention ungeklärt'},
  {id:'720575940629327659',label:'DNa02 (Stürner R)',role:'Absteigender Typ mit publizierten Steuerungseffekten',bodyChannel:null,sideStatus:'Stürner R / Originalannotation links: Seitenkonvention ungeklärt'},
  {id:'720575940606112940',label:'DNg13 (Stürner L)',role:'Absteigender Typ mit publizierten Bein-/Steuerungseffekten',bodyChannel:null,sideStatus:'Stürner L / Originalannotation rechts: Seitenkonvention ungeklärt'},
  {id:'720575940616471052',label:'DNg13 (Stürner R)',role:'Absteigender Typ mit publizierten Bein-/Steuerungseffekten',bodyChannel:null,sideStatus:'Stürner R / Originalannotation links: Seitenkonvention ungeklärt'},
];
for(const r of readouts) graph.indexOf(r.id);
const readoutIDs=readouts.map(r=>r.id);
const definitions=[
  ['jo_ce','Johnston-Organ C/E',['jon_c','jon_e'],'Antennen-Mechanosensorik / Antennenputz-Hypothese'],
  ['jo_f','Johnston-Organ F',['jon_f'],'Antennen-Mechanosensorik / publizierter Vergleichskanal'],
  ['jo_all','Johnston-Organ gesamt',['jon_c','jon_e','jon_f','jon_other'],'Antennen-Mechanosensorik'],
  ['sugar','Zucker-Sensoren',['sugar_grn'],'Geschmack / Fütterungsinitiierung'],
  ['water','Wasser-Sensoren',['water_grn'],'Geschmack / Fütterungsinitiierung'],
  ['bitter','Bitter-Sensoren',['bitter_grn'],'Geschmack / aversiver Vergleichskanal'],
];
const durationMs=600, stimulusWindowMs=[100,500];
const dynamics={dtMs:1,tauMs:20,threshold:1,resetVoltage:0,synapseGain:0.1,refractorySteps:2,background:null};
const bounds={maxCumulativeTraversedEdges:500_000_000,maxWallSecondsPerTrial:120};
const annotations=new Map(graph.annotations.map(r=>[r.id,r]));
const inDegree=new Uint32Array(graph.ids.length);
const outDegree=new Uint32Array(graph.ids.length);
for(const target of graph.targets)inDegree[target]++;
for(let i=0;i<outDegree.length;i++)outDegree[i]=graph.offsets[i+1]-graph.offsets[i];
const allInputs=new Set(idsFor(['jon_c','jon_e','jon_f','jon_other','sugar_grn','water_grn','bitter_grn','ir94e_grn']));
const excluded=new Set([...allInputs,...readoutIDs]);
function degreeMatch(sourceIDs){
  const used=new Set(excluded), result=[];
  for(const source of sourceIDs){
    const src=graph.indexOf(source), a=annotations.get(source)||{};
    let best=null;
    for(let j=0;j<graph.ids.length;j++){
      const id=graph.ids[j].toString(), b=annotations.get(id)||{};
      if(used.has(id)||b.super_class!==a.super_class||b.top_nt!==a.top_nt||b.side!==a.side)continue;
      const score=Math.abs(Math.log1p(inDegree[src])-Math.log1p(inDegree[j]))+
        Math.abs(Math.log1p(outDegree[src])-Math.log1p(outDegree[j]));
      if(!best||score<best.score)best={id,score,source,inDegree:inDegree[j],outDegree:outDegree[j],sourceInDegree:inDegree[src],sourceOutDegree:outDegree[src]};
    }
    if(!best)throw new Error(`No sham match for ${source}`);
    used.add(best.id);result.push(best);
  }
  return result;
}
const upstreamSham=degreeMatch([aBN1]);
const json=(p,v)=>writeFileSync(resolve(project,p),JSON.stringify(v,null,2)+'\n');
const sources=[
  {id:'graph',path:'brain/graph-original-v783/manifest.json',doi:'https://doi.org/10.1038/s41586-024-07558-y',description:'Unveränderter originaler v783-Graph: alle139255Knoten/15091983gerichtetePaare'},
  {id:'shiu',path:'data/research_sources/shiu/derived/shiu_supplement_index.json',doi:supplement.paper,workbookSha256:supplement.workbook_sha256,description:'v630-Workbook; nur exakt vorhandene v783-IDs; keine Vollreproduktion des Shiu-Modells'},
  {id:'tastekin',path:'data/research_sources/other/tastekin/tastekin_2026_cell_table_s1.xlsx',doi:'https://doi.org/10.1016/j.cell.2026.08.016',description:'Sheet MNs, rows68/69: aktuelle v783-MN9 R/L, Target_Muscle9'},
  {id:'stuerner',path:'data/research_sources/other/stuerner_neckconnective/Supplemental_file5_FAFB_DNs.tsv',doi:'https://doi.org/10.1038/s41586-025-08925-z',description:'Exakte FAFB-DN-IDs und quellenspezifische Seiten; Seitenkonflikt zur Originalannotation; funktionelle DNa02/DNg13-Evidenz separat DOI10.1016/j.cell.2024.08.033'},
];
for(const s of sources)s.localSha256=sha(readFileSync(resolve(project,s.path)));
const scenarios=definitions.map(([id,label,categories,role])=>({id,label,
  input:{ids:idsFor(categories),categories,role,source:'shiu',excluded: supplement.candidates.filter(c=>categories.includes(c.category)&&!eligible.includes(c))},
  readouts, trials:[], upstreamSilenced:id.startsWith('jo_')?[aBN1]:[],
}));
const protocol={schema:'fly.neuron-assay-protocol.v1',frozenAt:new Date().toISOString(),dynamics,durationMs,stimulusWindowMs,bounds,
  graphChecksums:graph.checksums,engineBaseSha256:sha(readFileSync(resolve(project,'brain/engine.mjs'))),
  assayEngineSha256:sha(readFileSync(resolve(out,'assay-engine.mjs'))),sources,
  stimulus:'Deterministische regelmäßige Eingangsspitzen; pro ID feste Phase aus uint64-Modulo1009. Eingänge werden gesetzt, Ausgänge entstehen ausschließlich durch Graphpropagation. Zeitfenster [100,500)ms.',
  shamMethod:'Greedy nearest L1 distance on log1p(in-degree),log1p(out-degree), exact super_class/top_nt/side; excludes all literature input and readout IDs. Anatomical comparison, no biological specificity proof.',
  upstreamSham,scenarios:scenarios.map(s=>({id:s.id,input:s.input,readouts:s.readouts,upstreamSilenced:s.upstreamSilenced}))};
json('analysis/neuron_assays/protocol.json',protocol);
const phase=id=>Number(BigInt(id)%1009n)/1009;
function scheduled(ids,hz,t){
  if(!hz||t<stimulusWindowMs[0]||t>=stimulusWindowMs[1])return [];
  const elapsed=t-stimulusWindowMs[0];
  return ids.filter(id=>Math.floor((elapsed+1)*hz/1000+phase(id))>Math.floor(elapsed*hz/1000+phase(id)));
}
const eventRows=['scenario,trial,root_id,spike_count,forced_input_count'];
function runTrial(scenario,spec){
  const {id,label,condition,doseHz,silenced=[],stimulusIDs=scenario.input.ids}=spec;
  const engine=new AssayEngine(graph,{...dynamics,silenced});
  const samples=[], counts=new Uint32Array(graph.ids.length),forcedCounts=new Uint32Array(graph.ids.length);
  const totals=Object.fromEntries(readoutIDs.map(id=>[id,{spikeCount:0,stimulusSpikeCount:0,voltageMin:0,voltageMax:0,voltageMean:0,firstSpikeMs:null}]));
  let traversedEdges=0,networkSpikeCount=0,forcedInputCount=0,aborted=null;
  const start=Date.now();
  for(let t=0;t<durationMs;t++){
    const forceSpikes=scheduled(stimulusIDs,doseHz,t);
    const result=engine.step({forceSpikes,readout:readoutIDs,maxReportedSpikes:0});
    const active=new Set(result.spikeIndices), spikesByReadout={};
    for(const i of result.spikeIndices)counts[i]++;
    for(const id of forceSpikes){const i=graph.indexOf(id);if(active.has(i)){forcedCounts[i]++;forcedInputCount++;}}
    for(const id of readoutIDs){
      const spike=Number(active.has(graph.indexOf(id))),v=result.readout[id],stat=totals[id];
      spikesByReadout[id]=spike;stat.spikeCount+=spike;
      if(t>=stimulusWindowMs[0]&&t<stimulusWindowMs[1])stat.stimulusSpikeCount+=spike;
      stat.voltageMin=Math.min(stat.voltageMin,v);stat.voltageMax=Math.max(stat.voltageMax,v);stat.voltageMean+=v;
      if(spike&&stat.firstSpikeMs===null)stat.firstSpikeMs=result.timeMs;
    }
    samples.push({tMs:result.timeMs,spikesByReadout,voltageByReadout:result.readout,networkSpikes:result.spikeCount});
    traversedEdges+=result.traversedEdges;networkSpikeCount+=result.spikeCount;
    if(traversedEdges>bounds.maxCumulativeTraversedEdges){aborted='cumulative_edge_limit';break;}
    if(Date.now()-start>bounds.maxWallSecondsPerTrial*1000){aborted='wall_time_limit';break;}
  }
  for(const stat of Object.values(totals)){
    stat.voltageMean/=samples.length;stat.stimulusRateHz=stat.stimulusSpikeCount/0.4;
  }
  let uniqueActiveNeurons=0;
  for(let i=0;i<counts.length;i++)if(counts[i]){uniqueActiveNeurons++;eventRows.push(`${scenario.id},${id},${graph.ids[i]},${counts[i]},${forcedCounts[i]}`);}
  const trial={id,label,condition,doseHz,dtMs:1,durationMs,stimulusWindowMs,silencedIDs:silenced,stimulusIDs,samples,
    summary:{status:aborted?'incomplete':'complete',aborted,completedSteps:samples.length,networkSpikeCount,forcedInputCount,
      graphPropagatedSpikes:networkSpikeCount-forcedInputCount,uniqueActiveNeurons,traversedEdges,wallSeconds:(Date.now()-start)/1000,readouts:totals}};
  writeFileSync(resolve(out,'trajectories',`${scenario.id}_${id}.json.gz`),gzipSync(JSON.stringify(trial)));
  console.log(JSON.stringify({scenario:scenario.id,trial:id,...trial.summary}));
  return trial;
}
for(const s of scenarios){
  const inputSham=degreeMatch(s.input.ids);
  s.inputShamMatches=inputSham;
  const specs=[
    {id:'baseline',label:'Ohne Reiz',condition:'baseline',doseHz:0},
    {id:'low',label:'Eingang50Hz',condition:'stimulation',doseHz:50},
    {id:'reference',label:'Eingang150Hz',condition:'stimulation',doseHz:150},
    {id:'input_ablated',label:'Sensorneuronen stillgelegt',condition:'input_ablation',doseHz:150,silenced:s.input.ids},
    {id:'readout_ablated',label:'Ausleseneuronen stillgelegt',condition:'readout_ablation',doseHz:150,silenced:readoutIDs.filter(id=>id!==aBN1)},
    {id:'input_sham',label:'Gradangepasste andere Sensorneuronen',condition:'degree_matched_input_sham',doseHz:150,stimulusIDs:inputSham.map(m=>m.id)},
  ];
  if(s.upstreamSilenced.length)specs.push(
    {id:'upstream_ablated',label:'aBN1 stillgelegt',condition:'upstream_ablation',doseHz:150,silenced:s.upstreamSilenced},
    {id:'upstream_sham',label:'Ähnliches anderes Interneuron stillgelegt',condition:'degree_matched_ablation_sham',doseHz:150,silenced:upstreamSham.map(m=>m.id)},
  );
  for(const spec of specs)s.trials.push(runTrial(s,spec));
  // Write partial status so a stopped run is never represented as complete.
  json('analysis/neuron_assays/status.json',{stage:'running',completedScenario:s.id,completedTrials:scenarios.reduce((n,s)=>n+s.trials.length,0)});
}
const limitations=[
  'In-silico-Modelltests; keine neuen biologischen Funktionsnachweise und keine physiologisch validierte Emulation.',
  'Alle139255Originalknoten und15091983Paare geladen. 616Knoten ohne Originalkante; neue Princeton-Kandidaten bleiben unintegriert.',
  'Vorhandene abstrakte LIF-Parameter vor den Tests fixiert; ACh positiv, GABA/Glutamat negativ, Monoamine ohne dynamischen Beitrag. Kein Parametersuchen auf gewünschtes Verhalten.',
  'Die Shiu-Rollen stammen aus v630. Exakte vorhandene IDs unterstützen eine Zuordnung; sie belegen keine unveränderte Morphologie oder Funktion in v783.',
  'Gleichmäßige phasenversetzte Eingangsspitzen,600ms,keine Hintergrundaktivität: Dies ist kein vollständiger Nachbau der publizierten Shiu-Experimente.',
  'Stille Auslese bedeutet bei diesen Parametern keine Schwellenüberschreitung; sie widerlegt die biologische Funktion nicht.',
  'Auslese-Ablation prüft die Intervention; das erwartete Nullsignal allein beweist keine Funktionszuordnung. aBN1-Ablation plus Sham prüft Abhängigkeit nur innerhalb dieses Modells.',
  'Körperbewegung aus Readouts ist ein offengelegter Darstellungsadapter. Keine gemessenen Muskelkräfte, kein vollständiges VNC, keine sensorische Rückkopplung aus dem Körper in diesen offenen Tests.',
];
const result={schema:'fly.neuron-assays.v1',generatedAt:new Date().toISOString(),status:scenarios.every(s=>s.trials.every(t=>t.summary.status==='complete'))?'complete':'partial',
  graph:{nodes:graph.manifest.node_count,edges:graph.manifest.edge_count,synapses:graph.manifest.synapse_count,modified:false},
  protocol:'analysis/neuron_assays/protocol.json',dynamics,sources,limitations,scenarios};
json('app/data/neuron_assays.json',result);
writeFileSync(resolve(out,'neuron_spike_counts.csv.gz'),gzipSync(eventRows.join('\n')+'\n'));
json('analysis/neuron_assays/summary.json',{...result,scenarios:scenarios.map(s=>({...s,trials:s.trials.map(({samples,...trial})=>trial)}))});
json('analysis/neuron_assays/status.json',{stage:result.status,completedAt:result.generatedAt,scenarios:scenarios.length,trials:scenarios.reduce((n,s)=>n+s.trials.length,0),file:'app/data/neuron_assays.json'});
