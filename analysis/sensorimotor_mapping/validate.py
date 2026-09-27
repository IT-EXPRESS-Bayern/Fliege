"""Recheck exported path counts against each original graph, never a merged graph."""
from pathlib import Path
import json, hashlib
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as feather
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
x=json.loads((ROOT/'app/data/sensorimotor_mapping.json').read_text(encoding='utf-8'))
sensors={s['id']:s for s in x['sensors']};motors={m['id']:m for m in x['motors']}
checks={'ids_strings':all(isinstance(k,str) for k in list(sensors)+list(motors)+list(x['nodes'])),'sensor_ids_unique':len(sensors)==len(x['sensors']),'tuning_unknown_preserved':all(s['tuningPolarity'] is None for s in sensors.values()),'proofread_is_boolean':all(isinstance(n['proofread'],bool) for n in list(sensors.values())+list(motors.values())+list(x['nodes'].values()))}
versions={}
for version,d in x['detectors'].items():
    g=feather.read_table(ROOT/f'data/research_sources/other/banc_2026/banc_888_edgelist_simple_{version}.feather',columns=['pre','post','count'])
    wanted_pres=pa.array(sorted({e['pre'] for e in d['edges']}));wanted_posts=pa.array(sorted({e['post'] for e in d['edges']}))
    actual=g.filter(pc.and_(pc.is_in(g['pre'],value_set=wanted_pres),pc.is_in(g['post'],value_set=wanted_posts)))
    lookup={(e['pre'],e['post']):int(e['count']) for e in actual.to_pylist()}
    edges={(e['pre'],e['post']):e['count'] for e in d['edges']}
    assert len(edges)==len(d['edges'])
    assert all(lookup.get(k)==n and n>0 and k[0]!=k[1] for k,n in edges.items())
    paths=pq.read_table(OUT/f'lf_paths_{version}.parquet').to_pylist()
    for p in paths:
        seq=[p['sensor']]+([p['intermediate']] if p['intermediate'] is not None else [])+[p['motor']]
        assert sensors[p['sensor']]['leg']=='LF' and p['motor'] in motors
        assert all(isinstance(i,str) and i in x['nodes'] for i in seq)
        assert len(seq)==len(set(seq))
        observed=[lookup[k] for k in zip(seq,seq[1:])]
        assert observed==p['edgeCounts'] and min(observed)==p['bottleneck']
        assert len(observed)==p['hops']
    inp=g.filter(pc.and_(pc.is_in(g['post'],value_set=pa.array(sorted(x['nodes']))),pc.not_equal(g['pre'],g['post'])))
    sums={r['post']:int(r['count_sum']) for r in inp.group_by('post').aggregate([('count','sum')]).to_pylist()}
    assert all(n[f'inputCountV{version[-1]}']==sums.get(k,0) for k,n in x['nodes'].items())
    versions[version]={'edges_rechecked':len(edges),'paths_rechecked':len(paths),'full_graph_input_sums_rechecked':len(x['nodes']),'all_counts_exact':True,'within_same_detector':True}
assert all(checks.values())
out={'checks':checks,'detectors':versions,'browser_sha256':hashlib.sha256((ROOT/'app/data/sensorimotor_mapping.json').read_bytes()).hexdigest(),'physiological_validation_performed':False,'interpretation':'Validates source identity and structural joins; tuning, receptor signs and force dynamics remain unvalidated.'}
(OUT/'validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out))
