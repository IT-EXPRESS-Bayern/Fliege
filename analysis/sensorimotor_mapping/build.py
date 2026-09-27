"""Exact BANC v888 FeCO -> LF femur/tibia motor paths, per detector.

Run: analysis/.venv/Scripts/python.exe analysis/sensorimotor_mapping/build.py
No tuning polarity or physiological edge sign is inferred from connectivity.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv, hashlib, json
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as feather
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
SRC=ROOT/'data/research_sources/other/banc_2026'
BODY=ROOT/'analysis/body_neural_interface'
OUT.mkdir(exist_ok=True,parents=True)

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def clean(v):return None if v is None or str(v).lower() in ['na','nan','none','null',''] else str(v)
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def csvout(p,rows):
    if not rows:return
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

cols=['banc_888_id','root_id','cell_type','side','super_class','cell_class','cell_sub_class','cell_function','cell_function_detailed','body_part_sensory','body_part_effector','nerve','peripheral_target_type','proofread','roughly_proofread','status','neurotransmitter_verified','neurotransmitter_predicted','neurotransmitter_score','fanc_match','fanc_nblast_match','fanc_cell_type']
meta={r['banc_888_id']:{k:clean(v) for k,v in r.items()} for r in feather.read_table(SRC/'banc_888_meta.feather',columns=cols).to_pylist()}
legmap={'front_leg':'F','middle_leg':'M','hind_leg':'H'}
subtypes={f'{part}_{sub}_chordotonal_organ_neuron':sub for part in legmap for sub in ['claw','hook','club']}
sensors=[]
for r in meta.values():
    if r['super_class']!='sensory' or r['cell_sub_class'] not in subtypes or r['side'] not in ['left','right']:continue
    subtype=subtypes[r['cell_sub_class']]
    sensors.append({'id':r['banc_888_id'],'leg':r['side'][0].upper()+legmap[r['body_part_sensory']],'joint':'femurTibia','subtype':subtype,'cellType':r['cell_type'],'side':r['side'],'observable':{'claw':'position','hook':'direction','club':'vibration_and_bidirectional_motion'}[subtype],'sourceSubclass':r['cell_sub_class'],'sourceFunction':r['cell_function_detailed'],'tuningPolarity':None,'tuningCurve':None,'ntVerified':r['neurotransmitter_verified'],'ntPredicted':r['neurotransmitter_predicted'],'proofread':r['proofread']=='TRUE','nerve':r['nerve'],'fancMatch':r['fanc_match'],'fancNblastMatch':r['fanc_nblast_match'],'sourceId':'banc_meta','tuningEvidence':'population-level modality from literature; exact-root direction and thresholds unknown'})
sensors.sort(key=lambda x:(x['leg'],x['subtype'],x['id']))
sensor_map={s['id']:s for s in sensors};lfids={s['id'] for s in sensors if s['leg']=='LF'}
motorrows=list(csv.DictReader((BODY/'banc_leg_motor_channels_391.csv').open(encoding='utf-8-sig',newline='')))
motors=[]
for r in motorrows:
    if r['candidate_model_leg']!='LF' or r['candidate_observation_channel']!='femurTibia':continue
    m=meta[r['banc_888_id']]
    motors.append({'id':r['banc_888_id'],'leg':'LF','joint':'femurTibia','action':'flex' if r['cell_function_detailed']=='flex_femur_tibia_joint' else 'extend','cellType':r['cell_type'],'sourceAction':r['cell_function_detailed'],'ntVerified':m['neurotransmitter_verified'],'ntPredicted':m['neurotransmitter_predicted'],'forceGain':None,'mechanicalSignInBodyCoordinates':1 if r['cell_function_detailed']=='flex_femur_tibia_joint' else -1,'mechanicalSignEvidence':'geometric convention of body flexion angle; not a synaptic sign','proofread':m['proofread']=='TRUE'})
motors.sort(key=lambda x:x['id']);motor_map={m['id']:m for m in motors};motor_ids=set(motor_map)
assert len(lfids)==110 and len(motors)==19
provenance=json.loads((SRC/'provenance.json').read_text(encoding='utf-8-sig'))
sources=[]
for name in ['banc_888_meta.feather','banc_888_edgelist_simple_v2.feather','banc_888_edgelist_simple_v3.feather']:
    p=SRC/name; entry=next(x for x in provenance['files'] if x['path'].endswith('/'+name));digest=sha(p)
    assert digest==entry['sha256']
    sources.append({'id':'banc_meta' if name.endswith('meta.feather') else name,'path':p.relative_to(ROOT).as_posix(),'url':entry['source_url'],'sha256':digest,'bytes':p.stat().st_size})

detectors={};stats={};all_node_ids=set(lfids)|motor_ids; input_counts={}
for version in ['v2','v3']:
    # Load each observed graph separately; all joins remain within this version.
    g=feather.read_table(SRC/f'banc_888_edgelist_simple_{version}.feather',columns=['pre','post','count'])
    se=g.filter(pc.and_(pc.is_in(g['pre'],value_set=pa.array(sorted(lfids))),pc.not_equal(g['pre'],g['post'])))
    incoming=pq.read_table(BODY/f'banc_motor_incoming_{version}.parquet').filter(pc.is_in(pq.read_table(BODY/f'banc_motor_incoming_{version}.parquet',columns=['post'])['post'],value_set=pa.array(sorted(motor_ids))))
    bypre=defaultdict(list)
    for e in incoming.to_pylist():bypre[e['pre']].append(e)
    paths=[];used_edges={};presyn_targets=set()
    for e in se.to_pylist():
        pre,post,n=e['pre'],e['post'],int(e['count'])
        if post in motor_ids:
            paths.append({'sensor':pre,'intermediate':None,'motor':post,'edgeCounts':[n],'bottleneck':n,'hops':1})
            used_edges[(pre,post)]={'pre':pre,'post':post,'count':n,'biologicalSign':None}
        if post not in meta or meta[post]['super_class'] in ['sensory','motor']:continue
        for e2 in bypre.get(post,[]):
            if e2['post']==pre or e2['post']==post:continue
            n2=int(e2['count']);paths.append({'sensor':pre,'intermediate':post,'motor':e2['post'],'edgeCounts':[n,n2],'bottleneck':min(n,n2),'hops':2})
            used_edges[(pre,post)]={'pre':pre,'post':post,'count':n,'biologicalSign':None}
            used_edges[(post,e2['post'])]={'pre':post,'post':e2['post'],'count':n2,'biologicalSign':None}
            presyn_targets.add(post)
    paths.sort(key=lambda x:(x['hops'],-x['bottleneck'],x['sensor'],x['motor'],x['intermediate'] or ''))
    edges=sorted(used_edges.values(),key=lambda x:(x['pre'],x['post']))
    all_node_ids.update(presyn_targets)
    all_input=g.filter(pc.not_equal(g['pre'],g['post']))
    input_counts[version]={x['post']:int(x['count_sum']) for x in all_input.group_by('post').aggregate([('count','sum')]).to_pylist()}
    del all_input
    pq.write_table(pa.Table.from_pylist(paths),OUT/f'lf_paths_{version}.parquet',compression='zstd')
    pq.write_table(pa.Table.from_pylist(edges),OUT/f'lf_edges_{version}.parquet',compression='zstd')
    summary=[]
    for subtype in ['claw','hook','club']:
        for action in ['flex','extend']:
            for threshold in [1,5]:
                q=[p for p in paths if p['bottleneck']>=threshold and sensor_map[p['sensor']]['subtype']==subtype and motor_map[p['motor']]['action']==action]
                summary.append({'detector':version,'subtype':subtype,'motor_action':action,'min_edge_count':threshold,'paths':len(q),'sensors':len({p['sensor'] for p in q}),'motor_roots':len({p['motor'] for p in q}),'direct_paths':sum(p['hops']==1 for p in q),'two_edge_paths':sum(p['hops']==2 for p in q)})
    csvout(OUT/f'lf_reachability_{version}.csv',summary)
    # Compact browser keeps all observed nodes and edges, and bounded anatomical examples.
    examples=[]
    for subtype in ['claw','hook','club']:
        for action in ['flex','extend']:
            q=[p for p in paths if p['bottleneck']>=5 and sensor_map[p['sensor']]['subtype']==subtype and motor_map[p['motor']]['action']==action]
            q.sort(key=lambda p:(-p['bottleneck'],p['hops'],p['sensor'],p['motor']))
            for p in q[:8]:examples.append(dict(p,sensorSubtype=subtype,motorAction=action,anatomySupported=True,tuningValidated=False))
    detectors[version]={'edges':edges,'paths':examples,'pathsTruncated':len(examples)<len(paths),'allPathsFile':f'analysis/sensorimotor_mapping/lf_paths_{version}.parquet','pathCount':len(paths),'summary':summary}
    stats[version]={'sensor_outgoing_pairs':len(se),'used_edges':len(edges),'all_paths':len(paths),'direct_paths':sum(p['hops']==1 for p in paths),'two_edge_paths':sum(p['hops']==2 for p in paths),'premotor_ids':len(presyn_targets),'examples':len(examples)}
    print(version,json.dumps(stats[version]),flush=True)
    del g,se,incoming

nodes={}
for id in sorted(all_node_ids):
    r=meta[id]
    nodes[id]={'id':id,'cellType':r['cell_type'],'side':r['side'],'superClass':r['super_class'],'cellClass':r['cell_class'],'ntVerified':r['neurotransmitter_verified'],'ntPredicted':r['neurotransmitter_predicted'],'proofread':r['proofread']=='TRUE','biologicalOutputSign':None,'sourceId':'banc_meta','inputCountV2':input_counts['v2'].get(id,0),'inputCountV3':input_counts['v3'].get(id,0),'inputCountDefinition':'sum of count across full corresponding detector graph, autapses excluded; zero means no incoming pair in that graph'}

lit=[
 {'id':'mamiya2018','url':'https://doi.org/10.1016/j.neuron.2018.09.009','title':'Neural Coding of Leg Proprioception in Drosophila','evidence':'calcium imaging during controlled tibia motion','supports':'FeCO claw position, hook directional motion, club vibration/bidirectional motion; not per-BANC-root tuning'},
 {'id':'lee2025','url':'https://doi.org/10.1038/s41467-025-59302-3','title':'Divergent neural circuits for proprioceptive and exteroceptive sensing of the Drosophila leg','evidence':'FANC reconstruction and putative neurotransmitter-weighted path analysis','supports':'Claw/hook contact local motor pathways; functional impact scores are not measured dynamics; FANC IDs do not identify BANC roots automatically'},
 {'id':'mamiya2023','url':'https://doi.org/10.1016/j.neuron.2023.07.009','title':'Biomechanical origins of proprioceptor feature selectivity and topographic maps in the Drosophila leg','evidence':'peripheral biomechanics and sensory calcium imaging','supports':'Claw population has angle-selective organization; subtype alone does not fix a universal linear transfer'},
 {'id':'dallmann2025','url':'https://doi.org/10.1038/s41586-025-09554-2','title':'Selective presynaptic inhibition of leg proprioception in behaving Drosophila','evidence':'behaving-fly recordings and circuit analysis','supports':'State-dependent hook gating; constant gain is a model assumption'}]
result={'schema':'fly.sensorimotor-mapping.v1','asOf':'2026-09-27','namespace':'BANC_v888','scope':{'inventory':'all exactly annotated claw/hook/club leg sensors','paths':'110 left-front FeCO sensors to 19 left-front femur-tibia motor neurons, direct or one intermediate','intermediateExclusion':'sensory and motor cells excluded as premotor intermediates','edgeThreshold':'all observed positive counts exported; examples require every edge >=5','detectorsMixed':False},'sensors':sensors,'motors':motors,'nodes':nodes,'detectors':detectors,'sources':sources,'literature':lit,'limits':['Synapse counts are structural evidence, not measured conductance or firing transfer.','No exact-root flexion/extension tuning was verified; all tuningPolarity values are null.','SNpp50 and SNpp51 are not treated as flexion/extension labels.','NT verified and predicted are preserved separately; receptor-specific biological edge sign remains unknown.','Body flexion-angle sign is a geometry convention, not a neurotransmitter sign.','Any polarity/gain assignment in a running controller must be recorded as a model hypothesis.','Club output to motor targets here is a structural observation in BANC, not a contradiction resolved against FANC physiology.']}
dump(ROOT/'app/data/sensorimotor_mapping.json',result)
csvout(OUT/'sensor_inventory.csv',sensors);csvout(OUT/'lf_motor_inventory.csv',motors)
audit={'namespace':'BANC_v888','sources':sources,'sensor_inventory_roots':len(sensors),'by_leg_subtype':{f'{leg}:{sub}':n for (leg,sub),n in Counter((s['leg'],s['subtype']) for s in sensors).items()},'lf_sensor_roots':len(lfids),'lf_motor_roots':len(motors),'detectors':stats,'unknown_root_tuning':sum(s['tuningPolarity'] is None for s in sensors),'verified_predicted_nt_disagreements':sum(s['ntVerified'] is not None and s['ntPredicted'] is not None and s['ntVerified']!=s['ntPredicted'] for s in sensors),'browser_file':'app/data/sensorimotor_mapping.json','browser_sha256':sha(ROOT/'app/data/sensorimotor_mapping.json'),'checks':{'sensor_ids_unique':len(sensor_map)==len(sensors),'all_ids_strings':all(isinstance(s['id'],str) for s in sensors),'motors_unique':len(motor_map)==len(motors),'separate_detector_joins':True,'unknown_polarity_preserved':all(s['tuningPolarity'] is None for s in sensors)}}
assert all(audit['checks'].values())
dump(OUT/'audit.json',audit)
print('DONE',json.dumps({'sensors':len(sensors),'nodes':len(nodes),'browser_bytes':(ROOT/'app/data/sensorimotor_mapping.json').stat().st_size}),flush=True)
