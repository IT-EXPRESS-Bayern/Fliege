"""Independent trajectory arithmetic, provenance checks and honest model findings."""
from pathlib import Path
import csv, gzip, hashlib, json, math
from collections import defaultdict

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/neuron_assays'
def load(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))
def save(p,value): (ROOT/p).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(8*1024*1024),b''):h.update(part)
    return h.hexdigest()

data=load('app/data/neuron_assays.json')
protocol=load('analysis/neuron_assays/protocol.json')
manifest=load('brain/graph-original-v783/manifest.json')
annotations={r['id']:r for r in load('brain/graph-original-v783/annotations.json')}
checks=[]
def check(name,condition,detail=None):
    checks.append({'name':name,'passed':bool(condition),'detail':detail})
    if not condition: raise AssertionError(name)

# Correct discovered source-side conflicts, with unchanged simulation numbers.
dn_ids={'720575940604737708':('DNa02','L','rechts'),'720575940629327659':('DNa02','R','links'),
        '720575940606112940':('DNg13','L','rechts'),'720575940616471052':('DNg13','R','links')}
for doc in [data,protocol]:
    for source in doc['sources']:
        if source['id']=='stuerner':
            source['doi']='https://doi.org/10.1038/s41586-025-08925-z'
            source['description']='Exakte FAFB-DN-IDs und quellenspezifische Seiten; Seitenkonflikt zur Originalannotation; Funktionsnachweis separat DOI10.1016/j.cell.2024.08.033'
    for scenario in doc['scenarios']:
        for r in scenario['readouts']:
            if r['id'] in dn_ids:
                name,side,original=dn_ids[r['id']]
                r.update(label=f'{name} (Stürner {side})',bodyChannel=None,
                         sideStatus=f'Stürner {side} / Originalannotation {original}: Seitenkonvention ungeklärt')

for filename,entry in manifest['files'].items():
    actual=sha(ROOT/'brain/graph-original-v783'/filename)
    check('original_graph_sha256_'+filename,actual==entry['sha256'])
    protocol['graphChecksums'][filename]=actual
for source in data['sources']:
    check('source_sha256_'+source['id'],sha(ROOT/source['path'])==source['localSha256'])

readout_names={r['id']:r['label'] for r in data['scenarios'][0]['readouts']}
count_rows=list(csv.DictReader(gzip.open(OUT/'neuron_spike_counts.csv.gz','rt',encoding='utf-8')))
count_map=defaultdict(list)
for r in count_rows:count_map[(r['scenario'],r['trial'])].append(r)
summary_rows=[]
for scenario in data['scenarios']:
    inputs=scenario['input']['ids']
    check(scenario['id']+'_input_unique',len(inputs)==len(set(inputs)))
    check(scenario['id']+'_input_readout_disjoint',not set(inputs)&set(readout_names))
    for match in scenario['inputShamMatches']:
        a,b=annotations[match['source']],annotations[match['id']]
        check(scenario['id']+'_sham_'+match['source'],all(a.get(k)==b.get(k) for k in ['super_class','top_nt','side']))
    for trial in scenario['trials']:
        prefix=scenario['id']+'_'+trial['id']
        samples=trial['samples'];stats=trial['summary'];rows=count_map[(scenario['id'],trial['id'])]
        check(prefix+'_complete',stats['status']=='complete' and len(samples)==600)
        check(prefix+'_time_axis',[s['tMs'] for s in samples]==list(range(1,601)))
        check(prefix+'_no_prestim_activity',all(s['networkSpikes']==0 for s in samples[:100]))
        check(prefix+'_network_counts',sum(s['networkSpikes'] for s in samples)==stats['networkSpikeCount']==sum(int(r['spike_count']) for r in rows))
        check(prefix+'_forced_counts',sum(int(r['forced_input_count']) for r in rows)==stats['forcedInputCount'])
        if trial['condition'] in ['baseline','input_ablation']:
            check(prefix+'_silent',stats['networkSpikeCount']==0)
        if trial['condition']=='readout_ablation':
            check(prefix+'_silenced',all(stats['readouts'][root]['spikeCount']==0 for root in trial['silencedIDs']))
        check(prefix+'_raw_archive_matches',json.loads(gzip.decompress((OUT/'trajectories'/f'{prefix}.json.gz').read_bytes()))['samples']==samples)
        for root,name in readout_names.items():
            emitted=[s['spikesByReadout'][root] for s in samples]
            volts=[s['voltageByReadout'][root] for s in samples]
            window=sum(emitted[100:500])
            r=stats['readouts'][root]
            check(prefix+'_arithmetic_'+root,
                all(v in [0,1] for v in emitted) and all(math.isfinite(v) for v in volts)
                and sum(emitted)==r['spikeCount'] and window==r['stimulusSpikeCount']
                and abs(window/0.4-r['stimulusRateHz'])<1e-10
                and math.isclose(sum(volts)/600,r['voltageMean'],abs_tol=1e-10))
            summary_rows.append({'scenario':scenario['id'],'trial':trial['id'],'root_id':root,'label':name,
                'dose_hz':trial['doseHz'],'stimulus_spike_count':window,'stimulus_rate_hz':window/0.4,
                'voltage_min':min(volts),'voltage_max':max(volts),'first_spike_ms':r['firstSpikeMs']})
with (OUT/'readout_summary.csv').open('w',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(summary_rows[0]));writer.writeheader();writer.writerows(summary_rows)

scenarios={s['id']:s for s in data['scenarios']}
def rate(scenario,root,trial='reference'):
    return next(t for t in scenarios[scenario]['trials'] if t['id']==trial)['summary']['readouts'][root]['stimulusRateHz']
abn='720575940630907434';adn1='720575940616185531';adn2='720575940629806974';mnr='720575940660219265';mnl='720575940618238523'
findings=[
 {'id':'taste_order','status':'qualitative_model_pattern_present','claim':'Zucker aktiviert beideMN9 stärker als Wasser; Bitter allein erzeugt hier keineMN9-Spikes.',
  'evidence':{s:{'MN9_R_hz':rate(s,mnr),'MN9_L_hz':rate(s,mnl)} for s in ['sugar','water','bitter']},
  'limitation':'Literaturkompatibles qualitatives Muster unter diesen Parametern; kein quantitativ validierter Ersatz der veröffentlichten Experimente.'},
 {'id':'jo_selectivity','status':'failed_literature_pattern','claim':'JO-CE-versus-JO-F-Spezifität der absteigenden Putz-Auslese wird nicht reproduziert.',
  'evidence':{s:{'aBN1_hz':rate(s,abn),'aDN1_hz':rate(s,adn1),'aDN2_hz':rate(s,adn2)} for s in ['jo_ce','jo_f']},
  'reference':'Shiu SuppTable8 publiziert bei150Hz: CE→aDN1 13.40Hz/aDN2 19.03Hz; F→beide0.00Hz (v630). Hier F stärker alsCE an beiden Auslesen.',
  'limitation':'Version, Zellidentität, Dynamik und Reizprotokoll unterscheiden sich. Ursache mit diesem Test nicht isoliert.'},
 {'id':'abn1_dependency','status':'model_dependency_present','claim':'Stilllegung von aBN1 unterdrückt dieaDN-Antworten fürCE/F; beim gesamtenJO-Satz bleibt Restaktivität.',
  'evidence':{s:{t:{'aDN1_hz':rate(s,adn1,t),'aDN2_hz':rate(s,adn2,t)} for t in ['reference','upstream_ablated','upstream_sham']} for s in ['jo_ce','jo_f','jo_all']},
  'limitation':'Kausaler Eingriff in dieses Modell. Keine biologische Notwendigkeit/Suffizienz bewiesen; nur ein deterministisch gewählter gradangepassterSham.'},
]
data['findings']=findings
data['validation']={'checks':len(checks),'allPassed':True,'trialCount':42,'allTrialsComplete':True,
    'literatureAgreement':'mixed; JO-CE/JO-F selectivity failed','audit':'analysis/neuron_assays/audit.json'}
protocol['metadataCorrections']=['Stürner DOI aus lokalem Provenienznachweis korrigiert; widersprüchliche Seiten getrennt benannt. Keine Dynamik,Inputs,Readouts oder Zahlen geändert.']
def readable(value):
    if isinstance(value,list): return [readable(v) for v in value]
    if isinstance(value,dict): return {k:readable(v) for k,v in value.items()}
    if not isinstance(value,str): return value
    for old,new in {
        'alle139255Knoten/15091983gerichtetePaare':'alle 139.255 Knoten / 15.091.983 gerichtete Paare',
        'rows68/69':'Zeilen 68/69','v783-MN9 R/L, Target_Muscle9':'v783-MN9 R/L, Target_Muscle 9',
        'Eingang50Hz':'Eingang 50 Hz','Eingang150Hz':'Eingang 150 Hz',
        'Alle139255Originalknoten und15091983Paare':'Alle 139.255 Originalknoten und 15.091.983 Paare',
        '616Knoten':'616 Knoten','Eingangsspitzen,600ms,keine':'Eingangsspitzen, 600 ms, keine',
        'beideMN9':'beide MN9','keineMN9':'keine MN9','dieaDN':'die aDN',
        'JO-Satz':'JO-Satz','SuppTable8':'Supplement-Tabelle 8','bei150Hz':'bei 150 Hz',
        'aDN1 13.40Hz/aDN2 19.03Hz':'aDN1 13,40 Hz / aDN2 19,03 Hz',
        'F→beide0.00Hz':'F → beide 0,00 Hz','alsCE':'als CE',
        'Kontrollknoten':'Kontrollknoten','gradangepassterSham':'gradangepasster Sham',
        'Dynamik,Inputs,Readouts':'Dynamik, Inputs, Readouts',
        'Modulo1009':'Modulo 1009','super_class/top_nt/side':'super_class / top_nt / side',
    }.items(): value=value.replace(old,new)
    return value
data=readable(data);protocol=readable(protocol);findings=readable(findings)
save('analysis/neuron_assays/protocol.json',protocol)
save('app/data/neuron_assays.json',data)
save('analysis/neuron_assays/summary.json',{**data,'scenarios':[{**s,'trials':[{k:v for k,v in t.items() if k!='samples'} for t in s['trials']]} for s in data['scenarios']]})

# Exact-root response inventory. A response is a model measurement, not a new functional name.
responses=defaultdict(dict)
for r in count_rows:
    if r['trial']=='reference':
        responses[r['root_id']][r['scenario']]={'total':int(r['spike_count']),'forced':int(r['forced_input_count'])}
profiles=[]
for root,conditions in sorted(responses.items()):
    a=annotations[root]
    profile={'root_id':root,'cell_type':a.get('cell_type',''),'cell_class':a.get('cell_class',''),
             'evidence':'response_in_fixed_computational_model_only'}
    for s in scenarios:
        c=conditions.get(s,{'total':0,'forced':0})
        profile[s+'_all600ms_spikes']=c['total'];profile[s+'_forced_input_spikes']=c['forced']
    profiles.append(profile)
with (OUT/'model_response_profiles.csv').open('w',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(profiles[0]));writer.writeheader();writer.writerows(profiles)
audit={'schema':'fly.neuron-assay-audit.v1','checks':checks,'check_count':len(checks),'all_passed':True,
       'trials':42,'samples':42*600,'individual_readout_observations':42*600*len(readout_names),
       'reference_responsive_unique_neurons':len(profiles),'findings':findings,
       'results_sha256':sha(ROOT/'app/data/neuron_assays.json')}
save('analysis/neuron_assays/audit.json',audit)
print(json.dumps({k:audit[k] for k in ['check_count','all_passed','trials','samples','individual_readout_observations','reference_responsive_unique_neurons']}))
