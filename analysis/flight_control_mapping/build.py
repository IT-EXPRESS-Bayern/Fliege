"""Exact BANC-v888 flight anatomy and separate detector paths, never physiological signs.

Run analysis/.venv/Scripts/python.exe analysis/flight_control_mapping/build.py.
The inventories include conflicts; default anatomical pools exclude them explicitly.
"""
from pathlib import Path
from collections import Counter
import csv, hashlib, json, xml.etree.ElementTree as ET
import duckdb
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as feather
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
SRC=ROOT/'data/research_sources/other/banc_2026'
OUT.mkdir(parents=True,exist_ok=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def csvout(name,rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def nerve_side(r):
    prefix=(r.get('nerve') or '').split('_')[0]
    return prefix if prefix in ('left','right') else None
fields=['banc_888_id','cell_type','side','super_class','cell_class','cell_sub_class','nerve','proofread','body_part_effector','body_part_sensory','peripheral_target_type','cell_function','cell_function_detailed','neurotransmitter_predicted','neurotransmitter_verified','fafb_match','fanc_match','manc_match']
meta={r['banc_888_id']:r for r in feather.read_table(SRC/'banc_888_meta.feather',columns=fields).to_pylist()}
assert all(isinstance(x,str) and x.isdigit() for x in meta)
def node(r):
    return dict(id=r['banc_888_id'],cellType=r['cell_type'],sourceSide=r['side'],nerve=r['nerve'],superClass=r['super_class'],cellClass=r['cell_class'],proofread=r['proofread']=='TRUE',ntVerified=r['neurotransmitter_verified'],ntPredicted=r['neurotransmitter_predicted'],biologicalOutputSign=None)
motors=[]
for r in meta.values():
    if r['super_class']!='motor' or r['body_part_effector'] not in ('wing','haltere'): continue
    m=node(r);body=r['body_part_effector'];fun=r['cell_function'];detailed=r['cell_function_detailed']
    conflict=('source_superclass_motor_but_peripheral_intrinsic_neuron' if r['cell_class']=='peripheral_intrinsic_neuron' else
              'source_haltere_target_but_leg_motor_class_or_function' if body=='haltere' and (r['cell_class']=='hind_leg_motor_neuron' or fun=='leg_motor' or detailed=='unknown_leg_movement') else None)
    mechanism=('asynchronous_wing_power' if fun=='wing_power' else
               'synchronous_wing_steering' if fun=='wing_steering' else
               'wing_tension_action_unresolved' if fun=='wing_tension' else
               'asynchronous_haltere_power_candidate' if fun=='haltere_power' or detailed=='haltere_power' else
               'haltere_steering_candidate' if fun=='haltere_steering' else 'unresolved')
    m.update(bodyPart=body,effectorSide=nerve_side(r),effectorSideEvidence='peripheral_nerve_name_prefix' if nerve_side(r) else 'unknown',
             sourceFunction=fun,sourceFunctionDetailed=detailed,targetMuscle=r['peripheral_target_type'],mechanism=mechanism,
             annotationConflict=conflict,eligibleForAnatomicalMotorPool=not conflict and r['proofread']=='TRUE' and nerve_side(r) is not None,
             kinematicSign=None,forceGain=None,wingbeatRatePerSpike=None,sourceId='banc_meta')
    motors.append(m)
motors.sort(key=lambda x:x['id']); assert len(motors)==91
sens=[]
for r in meta.values():
    if r['super_class']!='sensory' or not any(x in (r['body_part_sensory'] or '') for x in ('wing','haltere')):continue
    s=node(r);s.update(bodyPart=r['body_part_sensory'],peripheralStructure=r['peripheral_target_type'],sourceFunction=r['cell_function'],sourceFunctionDetailed=r['cell_function_detailed'],
      sourceSubclass=r['cell_sub_class'],proprioceptorCandidate=r['cell_function']=='proprioception',
      tuningPolarity=None,phaseResponse=None,strainGain=None,sourceId='banc_meta',fancMatch=r['fanc_match'])
    sens.append(s)
sens.sort(key=lambda x:x['id'])
lit=list(csv.DictReader((SRC/'supplemental_data_9.txt').open(encoding='utf-8-sig')))
lit={x['cell_type']:x for x in lit if x['super_class']=='descending' and x['cell_function'] in ('flight','landing','escape_takeoff')}
dns=[]
priority={'DNg02','DNg07','DNp03','DNp07','DNp10'}
for r in meta.values():
    if r['super_class']!='descending':continue
    family='DNg02' if (r['cell_type'] or '').startswith('DNg02_') else r['cell_type']
    if family not in lit:continue
    d=node(r);claim=lit[family]
    d.update(literatureType=family,publishedTypeRole=claim['cell_function'],citation=claim['citations'],doi=claim['doi'],
      evidenceScope='published_cell_type_or_parent_family; exact-root behavior not measured',queryPriority=family in priority,
      subtypeSpecificFunctionKnown=False if family=='DNg02' else None,sourceId='banc_literature_roles')
    dns.append(d)
dns.sort(key=lambda x:x['id'])
visual=[node(r) for r in meta.values() if r['cell_class']=='lobula_plate_tangential_cell' and (r['cell_type'] or '').startswith(('HS','VS'))]
visual.sort(key=lambda x:x['id'])
for x in visual:x.update(evidenceScope='source LPTC class/type; exact-root retinal motion tuning uncalibrated',visualTuning=None)
csvout('motor_inventory.csv',motors);csvout('sensory_inventory.csv',sens);csvout('dn_candidates.csv',dns);csvout('visual_candidates.csv',visual)
csvout('annotation_conflicts.csv',[x for x in motors if x['annotationConflict']])
csvout('source_side_vs_effector_side.csv',[x for x in motors if x['sourceSide']!=x['effectorSide']])

motor_ids={m['id'] for m in motors if m['eligibleForAnatomicalMotorPool']}
sensor_ids={s['id'] for s in sens if s['proprioceptorCandidate'] and s['proofread']}
dn_ids={d['id'] for d in dns if d['queryPriority'] and d['proofread']}
input_ids=sensor_ids|dn_ids
db=duckdb.connect();db.execute("SET memory_limit='1300MB'");db.execute('SET threads=2')
detectors={};included=set(m['id'] for m in motors)|sensor_ids|dn_ids|{x['id'] for x in visual};input_sums={}
sources=[]
for filename in ['banc_888_meta.feather','supplemental_data_9.txt','banc_888_edgelist_simple_v2.feather','banc_888_edgelist_simple_v3.feather']:
    p=SRC/filename;sources.append(dict(id='banc_meta' if filename.startswith('banc_888_meta') else 'banc_literature_roles' if filename=='supplemental_data_9.txt' else filename,
       path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size))
for v in ('v2','v3'):
    graph=feather.read_table(SRC/f'banc_888_edgelist_simple_{v}.feather',columns=['pre','post','count'])
    nonself=pc.not_equal(graph['pre'],graph['post'])
    outgoing=graph.filter(pc.and_(nonself,pc.is_in(graph['pre'],value_set=pa.array(sorted(input_ids)))))
    incoming=graph.filter(pc.and_(nonself,pc.is_in(graph['post'],value_set=pa.array(sorted(motor_ids)))))
    db.register('outgoing',outgoing);db.register('incoming',incoming)
    db.register('allowed_mid',pa.table({'id':[x for x,r in meta.items() if r['super_class'] not in ('sensory','motor') and r['proofread']=='TRUE']}))
    direct=db.execute('SELECT pre AS input, NULL::VARCHAR AS intermediate, post AS motor, count AS countA, NULL::INTEGER AS countB FROM outgoing WHERE post IN (SELECT DISTINCT post FROM incoming) ORDER BY pre,post').fetch_arrow_table()
    two=db.execute('SELECT a.pre AS input,a.post AS intermediate,b.post AS motor,a.count AS countA,b.count AS countB FROM outgoing a JOIN incoming b ON a.post=b.pre JOIN allowed_mid q ON a.post=q.id WHERE a.pre<>b.post ORDER BY a.pre,a.post,b.post').fetch_arrow_table()
    allpaths=pa.concat_tables([direct,two],promote_options='default');pq.write_table(allpaths,OUT/f'paths_{v}.parquet',compression='zstd')
    pathrows=allpaths.to_pylist();displaypaths=[r for r in pathrows if r['countA']>=5 and (r['countB'] is None or r['countB']>=5)]
    edges={}
    for p in displaypaths:
        sequence=[p['input']]+([p['intermediate']] if p['intermediate'] else [])+[p['motor']]
        for a,b,n in zip(sequence,sequence[1:],[p['countA'],p['countB']]):edges[(a,b)]=int(n)
    erows=[dict(pre=a,post=b,count=n,biologicalSign=None) for (a,b),n in sorted(edges.items())]
    pq.write_table(pa.Table.from_pylist(erows),OUT/f'edges_{v}_at5.parquet',compression='zstd')
    included.update(x for pair in edges for x in pair)
    vis=graph.filter(pc.and_(pc.is_in(graph['pre'],value_set=pa.array([x['id'] for x in visual])),pc.is_in(graph['post'],value_set=pa.array(sorted(dn_ids))))).to_pylist()
    vis.sort(key=lambda x:(x['pre'],x['post']))
    csvout(f'visual_to_dn_{v}.csv',vis) if vis else None
    vo=graph.filter(pc.and_(nonself,pc.is_in(graph['pre'],value_set=pa.array([x['id'] for x in visual]))))
    vi=graph.filter(pc.and_(nonself,pc.is_in(graph['post'],value_set=pa.array(sorted(dn_ids)))))
    db.register('vo',vo);db.register('vi',vi)
    vp=db.execute('SELECT a.pre AS visual,a.post AS intermediate,b.post AS dn,a.count AS countA,b.count AS countB FROM vo a JOIN vi b ON a.post=b.pre JOIN allowed_mid q ON q.id=a.post WHERE a.pre<>b.post ORDER BY a.pre,a.post,b.post').fetch_arrow_table()
    pq.write_table(vp,OUT/f'visual_two_edge_paths_{v}.parquet',compression='zstd')
    vp5=[x for x in vp.to_pylist() if x['countA']>=5 and x['countB']>=5]
    vedges={}
    for p in vp5:
        vedges[(p['visual'],p['intermediate'])]=int(p['countA']);vedges[(p['intermediate'],p['dn'])]=int(p['countB'])
    vrows=[dict(pre=a,post=b,count=n,biologicalSign=None) for (a,b),n in sorted(vedges.items())]
    included.update(x for pair in vedges for x in pair)
    vp5.sort(key=lambda p:(-min(p['countA'],p['countB']),p['visual'],p['dn'],p['intermediate']))
    examples=[]
    for cls,ids in [('descending',dn_ids),('proprioceptor',sensor_ids)]:
        for body in ('wing','haltere'):
            target_ids={x['id'] for x in motors if x['bodyPart']==body}
            candidates=[p for p in displaypaths if p['input'] in ids and p['motor'] in target_ids]
            candidates.sort(key=lambda p:(-min(p['countA'],p['countB'] or p['countA']),p['input'],p['motor'],p['intermediate'] or ''))
            for p in candidates[:40]:examples.append(dict(**p,inputClass=cls,bodyPart=body))
    summary=dict(allDirectPaths=direct.num_rows,allTwoEdgePaths=two.num_rows,pathsAt5=len(displaypaths),edgesAt5=len(erows),browserPathExamples=len(examples),visualToDnEdges=len(vis),
      dnPathCountAt5=sum(p['input'] in dn_ids for p in displaypaths),sensoryPathCountAt5=sum(p['input'] in sensor_ids for p in displaypaths),sameDetectorOnly=True,
      fullPathsFile=f'analysis/flight_control_mapping/paths_{v}.parquet',allPathsFileSha256=sha(OUT/f'paths_{v}.parquet'))
    summary.update(visualTwoEdgePaths=vp.num_rows,visualTwoEdgePathsAt5=len(vp5),visualTwoEdgeEdgesAt5=len(vrows))
    detectors[v]=dict(edges=erows,paths=examples,pathsTruncated=len(examples)<len(displaypaths),summary=summary,visualToDnEdges=vis,
       visualTwoEdgePaths=vp5[:80],visualTwoEdgePathsTruncated=len(vp5)>80,visualTwoEdgeEdges=vrows)
    sums=graph.filter(pc.and_(nonself,pc.is_in(graph['post'],value_set=pa.array(sorted(included))))).group_by('post').aggregate([('count','sum')])
    input_sums[v]={r['post']:int(r['count_sum']) for r in sums.to_pylist()}
    print(v,summary,flush=True)
    del graph,outgoing,incoming,allpaths,pathrows,two,direct,vo,vi,vp
# Compute sums for the final union even when a node was introduced only by v3.
for v in ('v2','v3'):
    missing=included-set(input_sums[v])
    if missing:
        graph=feather.read_table(SRC/f'banc_888_edgelist_simple_{v}.feather',columns=['pre','post','count'])
        sums=graph.filter(pc.and_(pc.not_equal(graph['pre'],graph['post']),pc.is_in(graph['post'],value_set=pa.array(sorted(missing))))).group_by('post').aggregate([('count','sum')])
        input_sums[v].update({r['post']:int(r['count_sum']) for r in sums.to_pylist()});del graph
nodes={x:dict(**node(meta[x]),inputCountV2=input_sums['v2'].get(x,0),inputCountV3=input_sums['v3'].get(x,0),inputCountDefinition='sum all original non-autaptic incoming contacts in the selected detector, not just flight subgraph') for x in sorted(included)}
assert all(e['pre'] in nodes and e['post'] in nodes for d in detectors.values() for e in d['edges'])
# Independent exact-edge recheck of all browser contacts against each source graph.
checks={}
for v in ('v2','v3'):
    graph=feather.read_table(SRC/f'banc_888_edgelist_simple_{v}.feather',columns=['pre','post','count'])
    all_edges=detectors[v]['edges']+detectors[v]['visualTwoEdgeEdges']
    chosen=graph.filter(pc.is_in(graph['pre'],value_set=pa.array(sorted({e['pre'] for e in all_edges}))))
    original={(x['pre'],x['post']):x['count'] for x in chosen.to_pylist()}
    assert all(original[(e['pre'],e['post'])]==e['count'] for e in all_edges)
    checks[v]=dict(browserEdgesRechecked=len(all_edges),exactCounts=True,mixedDetectorPaths=False)
    del graph,chosen,original
flybase=ROOT/'data/research_sources/other/autonomous_behavior/flybody/github/flybody'
flyfiles=['fruitfly/assets/fruitfly.xml','fruitfly/fruitfly.py','tasks/flight_imitation.py','tasks/pattern_generators.py','fly_envs.py']
flysources=[dict(path=(flybase/p).relative_to(ROOT).as_posix(),sha256=sha(flybase/p),bytes=(flybase/p).stat().st_size) for p in flyfiles]
xml=ET.parse(flybase/flyfiles[0]).getroot()
mechanics=dict(source='local original FlyBody XML and task code',files=flysources,rawMujocoOption=xml.find('option').attrib,
  wingDegreesOfFreedomPerSide=['yaw','roll','pitch'],jointDefaults={c:xml.find(f".//default[@class='{c}']/joint").attrib for c in ['yaw','roll','pitch']},
  wingFluidGeoms=[x.attrib for x in xml.findall('.//geom') if x.get('name') in ('wing_left_fluid','wing_right_fluid')],
  unitRule='Raw source units retained; convert the complete length/mass/time system consistently before browser use. XML density/viscosity numbers are not SI values.',
  controller='flight_imitation combines a requested-frequency baseline wing pattern and learnt action; this is an engineered/RL controller, not a BANC reconstruction',
  noBiologicalSpikeToWingFrequencyMapping=True,meshesFullyVerified=False)
save(OUT/'flybody_mechanics.json',mechanics)
result=dict(schema='fly.flight-control-mapping.v1',asOf='2026-09-27',namespace='BANC_v888',sources=sources,
  motors=motors,sensors=sens,dns=dns,visualCandidates=visual,nodes=nodes,detectors=detectors,mechanicalReference=mechanics,
  selection=dict(pathInputs='proofread proprioception candidates and DNg02-family/DNg07/DNp03/DNp07/DNp10 DNs',motorTargets='proofread non-conflicting wing/haltere motor-class records with nerve-derived effector side',
     intermediate='proofread, neither sensory nor motor',paths='direct and exactly two chemical edges; detectors independent',browserEdges='all edges belonging to a complete path with >=5 contacts per edge',
     sensoryTuning='unknown per root; no invented roll/pitch/yaw sign or phase preference'),
  interpretation=dict(anatomicalMapping=True,neuralDynamicsSimulated=False,flightPhysicsSimulated=False,flightValidated=False,fullBrainAutonomy=False,originalGraphModified=False,electricalSynapsesIncluded=False))
browser=ROOT/'app/data/flight_control_mapping.json';save(browser,result)
audit=dict(schema='fly.flight-control-mapping-audit.v1',namespace='BANC_v888',sources=sources,
  motorRows=len(motors),wingRows=sum(m['bodyPart']=='wing' for m in motors),haltereRows=sum(m['bodyPart']=='haltere' for m in motors),
  eligibleMotorPoolRows=len(motor_ids),annotationConflictRows=sum(bool(m['annotationConflict']) for m in motors),
  wingPowerRows=sum(m['sourceFunction']=='wing_power' for m in motors),wingSteeringRows=sum(m['sourceFunction']=='wing_steering' for m in motors),
  sourceVsEffectorSideDisagreements=sum(m['sourceSide']!=m['effectorSide'] for m in motors),
  sensorInventoryRows=len(sens),proprioceptorCandidates=sum(s['proprioceptorCandidate'] for s in sens),proofreadProprioceptorInputs=len(sensor_ids),
  dnCandidates=len(dns),priorityDnInputs=len(dn_ids),dng02FamilyRoots=sum(d['literatureType']=='DNg02' for d in dns),visualLptcCandidates=len(visual),
  browserNodes=len(nodes),detectors={v:d['summary'] for v,d in detectors.items()},checks=checks,
  idsStoredAsDecimalStrings=True,sourceSignSeparated=True,rootTuningUnassigned=True,flightBiologicallyValidated=False,
  browserFile=browser.relative_to(ROOT).as_posix(),browserSha256=sha(browser),browserBytes=browser.stat().st_size)
save(OUT/'audit.json',audit)
print(json.dumps({k:v for k,v in audit.items() if not isinstance(v,(list,dict))},ensure_ascii=False),flush=True)
