"""Observed BANC v888 DN-to-leg-motor routes, detector-aware and structural only."""
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timezone
import csv, hashlib, json
import duckdb
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as feather
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
SRC=ROOT/'data/research_sources/other/banc_2026'; BODY=ROOT/'analysis/body_neural_interface'
OUT.mkdir(exist_ok=True,parents=True)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def clean(x):return '' if x is None or str(x).lower() in ['nan','na','none','null'] else str(x)
def readcsv(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def save(name,data): (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def csvout(name,rows):
    if not rows:return
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

columns=['banc_888_id','root_id','root_626','root_850','root_888','supervoxel_id','cell_type','side','super_class','cell_class','proofread','region','nerve','neurotransmitter_predicted','neurotransmitter_verified','neurotransmitter_score','fafb_match','fafb_cell_type','fafb_alignment_cell_type']
meta={r['banc_888_id']:{k:clean(v) for k,v in r.items()} for r in feather.read_table(SRC/'banc_888_meta.feather',columns=columns).to_pylist()}
motors=readcsv(BODY/'banc_leg_motor_channels_391.csv'); motor_ids={m['banc_888_id'] for m in motors};motor_map={m['banc_888_id']:m for m in motors}
for motor in motors:
    motor['enabled_for_control']=False
    motor['actuator_sign']=None
    motor['force_gain']=None
literature=readcsv(SRC/'supplemental_data_9.txt')
roles={'steering','walking','grooming','halting','landing','escape_takeoff'}
lit={r['cell_type']:r for r in literature if r['super_class']=='descending' and r['cell_function'] in roles}
dns=[r for r in meta.values() if r['super_class']=='descending' and r['cell_type'] in lit]
dn_ids={d['banc_888_id'] for d in dns};priority={d['banc_888_id'] for d in dns if d['cell_type'] in ['DNa02','DNg13']}
assert len(priority)==4
provenance=json.loads((SRC/'provenance.json').read_text(encoding='utf-8-sig'))
sources={}
for name in ['banc_888_meta.feather','banc_888_edgelist_simple_v2.feather','banc_888_edgelist_simple_v3.feather','supplemental_data_9.txt','banc_fafb_reviewed_matches.csv.gz']:
    p=SRC/name;digest=sha(p); expected=next(r for r in provenance['files'] if r['path'].endswith('/'+name))
    assert digest==expected['sha256'],name
    sources[name]={'sha256':digest,'source_url':expected['source_url'],'bytes':p.stat().st_size}

db=duckdb.connect();db.execute("SET memory_limit='1500MB'");db.execute('SET threads=2')
db.execute(f"SET temp_directory='{(OUT/'duckdb_tmp').as_posix()}'")
incoming_sources=set()
for version in ['v2','v3']:
    m=pq.read_table(BODY/f'banc_motor_incoming_{version}.parquet')
    incoming_sources.update(m['pre'].to_pylist())
    db.register('arrow',m);db.execute(f'CREATE TABLE m{version[-1]} AS SELECT cast(pre as UBIGINT) pre,cast(post as UBIGINT) post,cast(count as INTEGER) n FROM arrow');db.unregister('arrow')
first_targets=set()
for version in ['v2','v3']:
    g=feather.read_table(SRC/f'banc_888_edgelist_simple_{version}.feather',columns=['pre','post','count'])
    d=g.filter(pc.and_(pc.is_in(g['pre'],value_set=pa.array(sorted(dn_ids))),pc.not_equal(g['pre'],g['post'])))
    first_targets.update(d.filter(pc.is_in(d['pre'],value_set=pa.array(sorted(priority))))['post'].to_pylist())
    db.register('arrow',d);db.execute(f'CREATE TABLE d{version[-1]} AS SELECT cast(pre as UBIGINT) pre,cast(post as UBIGINT) post,cast(count as INTEGER) n FROM arrow');db.unregister('arrow')
    del g,d
db.execute('CREATE TABLE d AS SELECT coalesce(a.pre,b.pre) pre,coalesce(a.post,b.post) post,a.n n2,b.n n3 FROM d2 a FULL JOIN d3 b USING(pre,post)')
db.execute('CREATE TABLE m AS SELECT coalesce(a.pre,b.pre) pre,coalesce(a.post,b.post) post,a.n n2,b.n n3 FROM m2 a FULL JOIN m3 b USING(pre,post)')
db.execute('CREATE TABLE direct AS SELECT d.pre dn,d.post motor,0::UBIGINT mid, d.n2 a2,d.n3 a3,NULL::INTEGER b2,NULL::INTEGER b3 FROM d JOIN m ON d.pre=m.pre AND d.post=m.post')
db.execute('CREATE TABLE p2 AS SELECT d.pre dn,m.post motor,d.post mid,d.n2 a2,d.n3 a3,m.n2 b2,m.n3 b3 FROM d JOIN m ON d.post=m.pre WHERE d.pre<>m.post AND d.post<>m.post')
db.execute('DELETE FROM p2 WHERE NOT(coalesce(a2>=1 AND b2>=1,false) OR coalesce(a3>=1 AND b3>=1,false))')
db.execute(f"COPY p2 TO '{(OUT/'all_two_edge_paths.parquet').as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
db.execute(f"COPY direct TO '{(OUT/'all_direct_paths.parquet').as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
reach=[]
for detector in ['v2','v3','common']:
    for threshold in [1,5]:
        a=f'a{detector[-1]}>={threshold}' if detector!='common' else f'a2>={threshold} AND a3>={threshold}'
        b=f'b{detector[-1]}>={threshold}' if detector!='common' else f'b2>={threshold} AND b3>={threshold}'
        for dn in sorted(dn_ids):
            directs=db.execute(f'SELECT motor FROM direct WHERE dn={dn} AND {a}').fetchnumpy()['motor'].tolist()
            pairs=db.execute(f'SELECT motor,count(*) n FROM p2 WHERE dn={dn} AND {a} AND {b} GROUP BY motor').fetchall()
            reach.append({'dn_id':dn,'dn_type':meta[dn]['cell_type'],'dn_side':meta[dn]['side'],'detector':detector,'threshold':threshold,
                          'direct_motor_count':len(directs),'two_edge_path_count':sum(c for _,c in pairs),'within_two_motor_count':len(set(directs)|{i for i,_ in pairs})})
csvout('reachability.csv',reach)
print('two-edge summary',json.dumps({'dns':len(dns),'types':len({r['cell_type'] for r in dns}),'paths':db.execute('select count(*) from p2').fetchone()[0],'priority':[r for r in reach if r['dn_id'] in priority and r['detector']=='common' and r['threshold']==5]}),flush=True)

# Three-edge expansion restricted to four priority DNs; do not materialize unrelated full graph paths.
for version in ['v2','v3']:
    g=feather.read_table(SRC/f'banc_888_edgelist_simple_{version}.feather',columns=['pre','post','count'])
    selected=pc.and_(pc.is_in(g['pre'],value_set=pa.array(sorted(first_targets))),pc.is_in(g['post'],value_set=pa.array(sorted(incoming_sources))))
    e=g.filter(pc.and_(selected,pc.not_equal(g['pre'],g['post'])))
    db.register('arrow',e);db.execute(f'CREATE TABLE e{version[-1]} AS SELECT cast(pre as UBIGINT) pre,cast(post as UBIGINT) post,cast(count as INTEGER) n FROM arrow');db.unregister('arrow')
    del g,e
db.execute('CREATE TABLE e AS SELECT coalesce(a.pre,b.pre) pre,coalesce(a.post,b.post) post,a.n n2,b.n n3 FROM e2 a FULL JOIN e3 b USING(pre,post)')
plist=','.join(sorted(priority))
db.execute(f'''CREATE TABLE p3 AS SELECT d.pre dn,m.post motor,d.post mid,e.post mid2,d.n2 a2,d.n3 a3,e.n2 b2,e.n3 b3,m.n2 c2,m.n3 c3
FROM d JOIN e ON d.post=e.pre JOIN m ON e.post=m.pre
WHERE d.pre IN ({plist}) AND d.pre<>e.post AND d.pre<>m.post AND d.post<>m.post''')
db.execute('DELETE FROM p3 WHERE NOT(coalesce(a2>=1 AND b2>=1 AND c2>=1,false) OR coalesce(a3>=1 AND b3>=1 AND c3>=1,false))')
three_reach=[]
for detector in ['v2','v3','common']:
    for t in [1,5]:
        predicate=' AND '.join(f'{edge}{v}>={t}' for edge in 'abc' for v in (['2','3'] if detector=='common' else [detector[-1]]))
        for dn in sorted(priority):
            row=db.execute(f'SELECT count(*),count(distinct motor) FROM p3 WHERE dn={dn} AND {predicate}').fetchone()
            three_reach.append({'dn_id':dn,'dn_type':meta[dn]['cell_type'],'dn_side':meta[dn]['side'],'detector':detector,'threshold':t,'three_edge_path_count':row[0],'three_edge_motor_count':row[1]})
csvout('three_edge_reachability.csv',three_reach)
# Keep top three per DN/motor for each detector separately plus common; complete aggregates above.
db.execute('CREATE TABLE selected3 AS SELECT * FROM p3 WHERE false')
for detector in ['v2','v3','common']:
    cols=[f'{e}{v}' for e in 'abc' for v in (['2','3'] if detector=='common' else [detector[-1]])]
    predicate=' AND '.join(f'{c} IS NOT NULL' for c in cols)
    db.execute(f"INSERT INTO selected3 SELECT * FROM p3 WHERE {predicate} QUALIFY row_number() OVER(PARTITION BY dn,motor ORDER BY least({','.join(cols)}) DESC,mid,mid2)<=3")
db.execute(f"COPY (SELECT DISTINCT * FROM selected3) TO '{(OUT/'top_three_edge_paths.parquet').as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")

# Version-aware examples: up to 3 strongest same-path/common>=5 routes per DN and leg.
records=[]
for hops,table in [(1,'direct'),(2,'p2'),(3,'selected3')]:
    cols=['a2','a3']+(['b2','b3'] if hops>=2 else [])+(['c2','c3'] if hops==3 else [])
    rows=db.execute(f"SELECT DISTINCT * FROM {table} WHERE {' AND '.join(c+'>=5' for c in cols)}").fetch_arrow_table().to_pylist()
    bygroup=defaultdict(list)
    for r in rows:
        r.update(hops=hops,bottleneck=min(r[c] for c in cols))
        bygroup[(str(r['dn']),motor_map[str(r['motor'])]['candidate_model_leg'])].append(r)
    for group,items in bygroup.items():records.extend(sorted(items,key=lambda r:(-r['bottleneck'],r['motor'],r['mid']))[:3])

def node(id):
    r=meta[str(id)]
    return {'id':str(id),'type':r['cell_type'],'side':r['side'],'superClass':r['super_class'],'ntPredicted':r['neurotransmitter_predicted'],'ntVerified':r['neurotransmitter_verified'],'proofread':r['proofread']}
examples=[]
for i,r in enumerate(sorted(records,key=lambda r:(0 if str(r['dn']) in priority else 1,r['hops'],-r['bottleneck'],r['dn'],r['motor']))):
    sequence=[r['dn']]+([r['mid']] if r['hops']>=2 else [])+([r['mid2']] if r['hops']==3 else [])+[r['motor']]
    edges=[{'pre':str(a),'post':str(b),'countV2':r[f'{c}2'],'countV3':r[f'{c}3']} for a,b,c in zip(sequence,sequence[1:],'abc')]
    examples.append({'id':f'banc-path-{i+1:04d}','dnId':str(r['dn']),'motorId':str(r['motor']),'intermediates':[str(x) for x in sequence[1:-1]],
       'nodes':[node(x) for x in sequence],'edges':edges,'hops':r['hops'],'bottleneckV2':min(e['countV2'] for e in edges),
       'bottleneckV3':min(e['countV3'] for e in edges),'commonBothAt5':True,'rank':i+1,'motor':motor_map[str(r['motor'])],'structuralOnly':True})

# Structural intervention on all <=2-edge routes, not on the displayed truncated examples.
ablations=[]
for dn in sorted(priority):
    rows=db.execute(f'SELECT * FROM p2 WHERE dn={dn} AND a2>=5 AND a3>=5 AND b2>=5 AND b3>=5').fetch_arrow_table().to_pylist()
    direct_motors={str(r[0]) for r in db.execute(f'SELECT motor FROM direct WHERE dn={dn} AND a2>=5 AND a3>=5').fetchall()}
    coverage=Counter(str(r['mid']) for r in rows)
    if not coverage:continue
    target=sorted(coverage,key=lambda k:(-coverage[k],k))[0]
    outdegree=dict(db.execute('SELECT cast(pre as VARCHAR),count(*) FROM m WHERE n2>=5 AND n3>=5 GROUP BY pre').fetchall())
    sham_pool=[k for k in outdegree if k not in coverage and k not in dn_ids and k not in motor_ids and meta[k]['super_class']==meta[target]['super_class']]
    sham=min(sham_pool,key=lambda k:(abs(outdegree[k]-outdegree[target]),k)) if sham_pool else None
    for condition,removed in [('baseline',None),('remove_high_coverage_premotor',target),('matched_degree_sham',sham),('remove_dn',dn)]:
        surviving=[] if removed==dn else [r for r in rows if str(r['mid'])!=removed and str(r['motor'])!=removed]
        motors_remaining=set() if removed==dn else direct_motors|{str(r['motor']) for r in surviving}
        ablations.append({'dnId':dn,'dnType':meta[dn]['cell_type'],'condition':condition,'removedId':removed,
            'removedType':meta[removed]['cell_type'] if removed else None,'motorOutdegreeCommon5':outdegree.get(removed) if removed else None,
            'survivingTwoEdgePaths':len(surviving),'reachableMotorsWithinTwo':len(motors_remaining),
            'lostMotorIds':sorted((direct_motors|{str(r['motor']) for r in rows})-motors_remaining),
            'meaning':'Node-removal reachability on the intersection of both BANC detectors at >=5 contacts per edge; no spike or force test.'})
save('structural_ablations.json',ablations)

# Reviewed cross-animal matches: only unambiguous v888 resolutions; all source identifiers retained.
sv=defaultdict(set); old=defaultdict(set)
for id,r in meta.items():
    if r['supervoxel_id']:sv[r['supervoxel_id']].add(id)
    for key in ['root_626','root_850','root_888']:
        if r[key]:old[r[key]].add(id)
review=[]
for rownum,r in enumerate(readcsv(SRC/'banc_fafb_reviewed_matches.csv.gz'),2):
    if r['valid']!='t' or not r['match_id'].isdigit():continue
    choices=[('supervoxel',sv.get(r['pt_supervoxel_id'],set())),('direct_pt_root',{r['pt_root_id']} if r['pt_root_id'] in meta else set()),('direct_query',{r['query_id']} if r['query_id'] in meta else set()),('version_crosswalk',old.get(r['query_id'],set()))]
    singles=[(method,next(iter(ids))) for method,ids in choices if len(ids)==1]
    if not singles or not any(id in dn_ids for _,id in singles):continue
    resolved={id for _,id in singles}
    id=singles[0][1] if len(resolved)==1 else ''
    review.append({'source_row':rownum,'source_query_id':r['query_id'],'source_pt_root_id':r['pt_root_id'],'source_supervoxel':r['pt_supervoxel_id'],
       'banc_v888_id':id,'fafb_v783_candidate_id':r['match_id'],'match_cell_type':r['match_cell_type'],'resolution_method':singles[0][0] if id else 'conflicting_resolutions',
       'evidence':'reviewed_cross_animal_homology_not_identical_neuron_or_fafb_synapse'})
csvout('reviewed_dn_homologies.csv',review)
dns_ui=[{**node(r['banc_888_id']),'literature':lit[r['cell_type']],'fafbMatch':r['fafb_match'],
         'reviewedHomologies':[m for m in review if m['banc_v888_id']==r['banc_888_id']],
         'fafbEvidence':'Source match or reviewed cross-animal homology only; never join BANC edges into the FAFB graph.'} for r in dns]
limitations=['Observed anatomical paths within the BANC v888 specimen; FAFB v783 is a different animal.',
 'Detector agreement is robustness within one animal, not independent biological replication.',
 'Synapse counts do not calibrate firing, delay, current, muscle force or movement. NT predictions are not verified signs; no sign-chain inference is made.',
 'Path examples are ranked by minimum contact count, not by probability or causal influence. All one/two-edge routes are exported; three-edge search only covers DNa02/DNg13, with full counts and top-three examples per endpoint.',
 'Motor somatic side is not assumed to equal a descending neuron side. DNg13 crossed projections require actual path endpoints.',
 'Structural node-removal tests describe graph redundancy; no spiking physiology, learned motor policy or biological necessity is demonstrated.']
output={'schema':'fly.motor-pathways.v1','generatedAt':datetime.now(timezone.utc).isoformat(),'namespace':'BANC_v888','sources':sources,
        'motors':motors,'dns':dns_ui,'paths':examples,'reachability':reach,'threeEdgeReachability':three_reach,'ablations':ablations,'limitations':limitations}
(ROOT/'app/data/motor_pathways.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audit={'sources':sources,'dn_count':len(dns),'dn_type_count':len({r['cell_type'] for r in dns}),'motor_count':len(motors),
       'direct_paths_union':db.execute('select count(*) from direct').fetchone()[0],
       'two_edge_paths_union':db.execute('select count(*) from p2').fetchone()[0],
       'three_edge_paths_union_priority_only':db.execute('select count(*) from p3').fetchone()[0],
       'common5_display_examples':len(examples),'reachability':reach,'three_edge_reachability':three_reach,
       'reviewed_homology_rows':len(review),'conflicting_resolution_rows':sum(not r['banc_v888_id'] for r in review),
       'structural_ablations':ablations,'original_fafb_graph_changed':False,'biological_sign_inference':False,
       'checks':{'unique_motor_ids':len(motor_ids)==391,'source_hashes_verified':True,'four_priority_dns':len(priority)==4,
                 'path_nodes_all_in_banc_meta':all(n['id'] in meta for p in examples for n in p['nodes']),
                 'path_edges_both_versions_at_least5':all(e['countV2']>=5 and e['countV3']>=5 for p in examples for e in p['edges']),
                 'no_cycles_in_examples':all(len(p['nodes'])==len({n['id'] for n in p['nodes']}) for p in examples)}}
assert all(audit['checks'].values())
save('audit.json',audit)
csvout('path_examples.csv',[{'id':p['id'],'dn_id':p['dnId'],'dn_type':p['nodes'][0]['type'],'dn_side':p['nodes'][0]['side'],
  'motor_id':p['motorId'],'motor_leg':p['motor']['candidate_model_leg'],'motor_action':p['motor']['cell_function_detailed'],
  'hops':p['hops'],'node_ids':';'.join(n['id'] for n in p['nodes']),'counts_v2':';'.join(str(e['countV2']) for e in p['edges']),
  'counts_v3':';'.join(str(e['countV3']) for e in p['edges']),'bottleneck_v2':p['bottleneckV2'],'bottleneck_v3':p['bottleneckV3']} for p in examples])
print(json.dumps({k:audit[k] for k in ['dn_count','dn_type_count','motor_count','direct_paths_union','two_edge_paths_union','three_edge_paths_union_priority_only','common5_display_examples','reviewed_homology_rows','checks']}),flush=True)
