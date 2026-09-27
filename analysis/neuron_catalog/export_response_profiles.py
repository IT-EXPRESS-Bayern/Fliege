"""Export sparse per-root reference responses for the browser, with exact checks.

Inputs are read-only. The sparse absence rule is validated against full-graph
count archives and all six completed reference-trial network totals.
"""
from pathlib import Path
from collections import defaultdict
import csv
import gzip
import hashlib
import json
import numpy as np
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
TARGET = ROOT/'app/data/neuron_response_profiles.json'
CONDITIONS = ('jo_ce','jo_f','jo_all','sugar','water','bitter')
LABELS = ('Johnston-Organ C/E','Johnston-Organ F','Johnston-Organ gesamt','Zucker','Wasser','Bitter')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(4*1024*1024), b''):
            h.update(part)
    return h.hexdigest()


def read_rows(path):
    with path.open(encoding='utf8', newline='') as f:
        return list(csv.DictReader(f))


def main():
    named_path = OUT/'named_model_responses.csv'
    raw_profile_path = ROOT/'analysis/neuron_assays/model_response_profiles.csv'
    counts_path = ROOT/'analysis/neuron_assays/neuron_spike_counts.csv.gz'
    summary_path = ROOT/'analysis/neuron_assays/summary.json'
    roots_path = ROOT/'data/flywire_fafb_v783/proofread_root_ids_783.npy'
    catalog_path = OUT/'catalog_139255.parquet'
    named = read_rows(named_path)
    raw_profiles = {r['root_id']: r for r in read_rows(raw_profile_path)}
    roots = {str(int(x)) for x in np.load(roots_path)}
    catalog_roots = set(pq.read_table(catalog_path, columns=['root_id'])['root_id'].to_pylist())
    assert roots == catalog_roots and len(roots) == 139255
    assert len(named) == len({r['root_id'] for r in named}) == len(raw_profiles) == 7048
    assert {r['root_id'] for r in named} == set(raw_profiles) <= roots
    count_map = {condition: {} for condition in CONDITIONS}
    with gzip.open(counts_path, 'rt', encoding='utf8', newline='') as f:
        for r in csv.DictReader(f):
            if r['trial'] != 'reference':
                continue
            assert r['scenario'] in CONDITIONS
            assert r['root_id'] in roots
            assert r['root_id'] not in count_map[r['scenario']]
            total, forced = int(r['spike_count']), int(r['forced_input_count'])
            assert total > 0 and 0 <= forced <= total
            count_map[r['scenario']][r['root_id']] = [total, forced, total-forced]
    active_union = set().union(*(set(v) for v in count_map.values()))
    assert active_union == set(raw_profiles)
    profiles = {}
    for r in sorted(named, key=lambda x: x['root_id']):
        rid = r['root_id']
        assert isinstance(rid, str) and len(rid) == 18 and rid.isdecimal()
        assert r['model_evidence'] == 'response_in_fixed_computational_model_only'
        profile = []
        for condition in CONDITIONS:
            values = [int(r[f'{condition}_all600ms_spikes']), int(r[f'{condition}_forced_input_spikes']),
                      int(r[f'{condition}_non_forced_spikes'])]
            assert 0 <= values[1] <= values[0] <= 600
            assert values[2] == values[0]-values[1]
            assert values == count_map[condition].get(rid, [0,0,0])
            assert values[:2] == [int(raw_profiles[rid][f'{condition}_all600ms_spikes']),
                                  int(raw_profiles[rid][f'{condition}_forced_input_spikes'])]
            profile.append(values)
        assert any(v[0] > 0 for v in profile)
        profiles[rid] = profile
    summary = json.loads(summary_path.read_text(encoding='utf8'))
    assert summary['status'] == 'complete' and summary['graph']['nodes'] == len(roots)
    reference_totals = {}
    for condition in CONDITIONS:
        scenario = next(s for s in summary['scenarios'] if s['id'] == condition)
        reference = next(t for t in scenario['trials'] if t['id'] == 'reference')
        assert reference['durationMs'] == 600 and reference['doseHz'] == 150
        assert reference['stimulusWindowMs'] == [100,500]
        stats = reference['summary']
        assert stats['status'] == 'complete' and stats['completedSteps'] == 600
        total = sum(v[0] for v in count_map[condition].values())
        forced = sum(v[1] for v in count_map[condition].values())
        assert total == stats['networkSpikeCount'] and forced == stats['forcedInputCount']
        assert len(count_map[condition]) == stats['uniqueActiveNeurons']
        reference_totals[condition] = {'total_spikes': total, 'forced_input_spikes': forced,
                                       'non_forced_spikes': total-forced,
                                       'roots_with_spikes': len(count_map[condition])}
    source = {'file': str(named_path.relative_to(ROOT)).replace('\\','/'), 'sha256': sha(named_path)}
    inputs = [{'file': str(p.relative_to(ROOT)).replace('\\','/'), 'sha256': sha(p)}
              for p in (raw_profile_path, counts_path, summary_path, roots_path, catalog_path)]
    profiles_sha = hashlib.sha256(json.dumps(profiles, separators=(',', ':'), sort_keys=True).encode('utf8')).hexdigest()
    payload = {'schema': 'fly.neuron-response-profiles.v1', 'dataset': 'FAFB v783 original graph',
        'conditions': list(CONDITIONS), 'condition_labels': dict(zip(CONDITIONS, LABELS)),
        'window_ms': 600, 'stimulus_window_ms': [100,500], 'stimulus_duration_ms': 400,
        'input_frequency_hz': 150, 'value_order': ['total_spikes','forced_input_spikes','non_forced_spikes'],
        'profiles_by_id': profiles, 'source': source, 'provenance_inputs': inputs,
        'profile_count': len(profiles), 'catalog_root_count': len(roots), 'profiles_sha256': profiles_sha,
        'checksum_encoding': 'SHA-256 of UTF-8 JSON profiles_by_id with sorted keys and separators comma/colon, no whitespace',
        'evidence': 'response_in_fixed_computational_model_only',
        'interpretation': 'Spikezahlen dieses festgelegten Rechenmodells über jeweils 600 ms. Nicht direkt erzwungen = Gesamtspikes minus vorgegebene Eingangsspikes; keine biologische Funktionsmessung.',
        'absence_rule': {'status': 'known_catalog_id_absent_means_zero_spikes_in_these_six_reference_trials',
            'known_catalog_only': True, 'zeros': [[0,0,0] for _ in CONDITIONS],
            'description': 'Eine bekannte ID des 139255-Root-Katalogs ohne Eintrag hatte in allen sechs vollständig aufgezeichneten Referenzläufen null Spikes. Das sagt nichts über andere Reize, unterschwellige Spannung oder die biologische Funktion. Für unbekannte IDs gilt diese Nullregel nicht.'},
        'validation': {'all_7048_profiles_exactly_match_sources': True, 'all_ids_exact_catalog_members': True,
            'all_six_trials_complete_600_steps': True, 'all_raw_reference_active_roots_included': True,
            'all_six_network_spike_totals_reconciled': True}, 'reference_totals': reference_totals}
    TARGET.write_text(json.dumps(payload, ensure_ascii=False, separators=(',',':'))+'\n', encoding='utf8')
    reread = json.loads(TARGET.read_text(encoding='utf8'))
    assert reread['profiles_by_id'] == profiles and reread['source'] == source
    audit = {'schema': 'fly.response-browser-export-audit.v1', 'status': 'passed',
             'output': str(TARGET.relative_to(ROOT)).replace('\\','/'), 'output_sha256': sha(TARGET),
             'output_bytes': TARGET.stat().st_size, 'profiles_sha256': profiles_sha, 'source': source,
             'provenance_inputs': inputs, 'exported_roots': len(profiles), 'catalog_roots': len(roots),
             'implicit_zero_profile_roots': len(roots)-len(profiles), 'checked_numeric_cells': len(profiles)*len(CONDITIONS)*3,
             'reference_totals': reference_totals, 'checks': payload['validation']}
    (OUT/'response_browser_export_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps({k:audit[k] for k in ['status','exported_roots','implicit_zero_profile_roots','checked_numeric_cells','output_bytes','output_sha256','checks']}, indent=2))


if __name__ == '__main__':
    main()
