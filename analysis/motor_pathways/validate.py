"""Independent source checks of displayed BANC routes and structural accounting."""
from pathlib import Path
from collections import defaultdict
import json,hashlib,csv
import duckdb
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as f
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
DATA=ROOT/'data/research_sources/other/banc_2026';BODY=ROOT/'analysis/body_neural_interface'
d=json.loads((ROOT/'app/data/motor_pathways.json').read_text(encoding='utf-8'))
checks=[]
def check(name,value):
    checks.append({'name':name,'passed':bool(value)})
    assert value,name
for v in ['v2','v3']:
    graph=f.read_table(DATA/f'banc_888_edgelist_simple_{v}.feather',columns=['pre','post','count'])
    motorids=pa.array([m['banc_888_id'] for m in d['motors']])
    filt=graph.filter(pc.and_(pc.is_in(graph['post'],value_set=motorids),pc.not_equal(graph['pre'],graph['post'])))
    check(v+'_cached_motor_inputs_exactly_equal_original_graph_filter',filt.equals(pq.read_table(BODY/f'banc_motor_incoming_{v}.parquet')))
    wanted={e['pre'] for p in d['paths'] for e in p['edges']}
    subset=graph.filter(pc.is_in(graph['pre'],value_set=pa.array(sorted(wanted))))
    exact={(r['pre'],r['post']):r['count'] for r in subset.to_pylist()}
    key='countV'+v[-1]
    check(v+'_every_displayed_edge_has_exact_original_count',all(exact.get((e['pre'],e['post']))==e[key] for p in d['paths'] for e in p['edges']))
    del graph,subset,exact
db=duckdb.connect();par=(OUT/'all_two_edge_paths.parquet').as_posix()
check('no_mixed_detector_only_two_edge_combinations',db.execute(f"SELECT count(*)=0 FROM read_parquet('{par}') WHERE NOT(coalesce(a2>=1 AND b2>=1,false) OR coalesce(a3>=1 AND b3>=1,false))").fetchone()[0])
check('two_edge_path_combinations_unique',db.execute(f"SELECT count(*)=count(distinct(dn,mid,motor)) FROM read_parquet('{par}')").fetchone()[0])
for row in d['reachability']:
    n=str(row['dn_id']);t=row['threshold'];versions=['2','3'] if row['detector']=='common' else [row['detector'][-1]]
    pred=' AND '.join(f'{e}{v}>={t}' for e in ['a','b'] for v in versions)
    count=db.execute(f"SELECT count(*) FROM read_parquet('{par}') WHERE dn={n} AND {pred}").fetchone()[0]
    check('recount_'+n+'_'+row['detector']+'_'+str(t),count==row['two_edge_path_count'])
check('path_string_ids',all(isinstance(n['id'],str) and n['id'].isdigit() for p in d['paths'] for n in p['nodes']))
check('path_id_unique',len(d['paths'])==len({p['id'] for p in d['paths']}))
check('no_geometric_actuator_enabled',all(m['enabled_for_control'] is False and m['actuator_sign'] is None and m['force_gain'] is None for m in d['motors']))
groups=defaultdict(list)
for r in d['ablations']:groups[r['dnId']].append(r)
for dn,rows in groups.items():
    b=next(r for r in rows if r['condition']=='baseline')
    for r in rows:
        check('removal_nonincreasing_'+dn+'_'+r['condition'],r['reachableMotorsWithinTwo']<=b['reachableMotorsWithinTwo'] and r['survivingTwoEdgePaths']<=b['survivingTwoEdgePaths'])
        check('lost_count_'+dn+'_'+r['condition'],len(r['lostMotorIds'])==b['reachableMotorsWithinTwo']-r['reachableMotorsWithinTwo'])
metadata=f.read_table(DATA/'banc_888_meta.feather',columns=['banc_888_id','cell_type']).to_pylist()
lookup={r['banc_888_id']:r['cell_type'] for r in metadata}
review=list(csv.DictReader((OUT/'reviewed_dn_homologies.csv').open()))
check('reviewed_resolved_roots_in_v888',all(not r['banc_v888_id'] or r['banc_v888_id'] in lookup for r in review))
audit={'all_passed':all(r['passed'] for r in checks),'checks_count':len(checks),'checks':checks,
       'browser_source_sha256':hashlib.sha256((ROOT/'app/data/motor_pathways.json').read_bytes()).hexdigest(),
       'scope':'Complete cached motor-input equality, every displayed path edge against original graph counts, complete two-edge count and nonmixing checks, structural removal invariants. No functional or physiological validation.'}
(OUT/'validation.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps({k:audit[k] for k in ['all_passed','checks_count','browser_source_sha256']}))
