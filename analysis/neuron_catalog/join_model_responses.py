"""Attach names to measured model responses without assigning biological roles."""
from pathlib import Path
import csv
import hashlib
import json
from collections import Counter
import pyarrow.parquet as pq
import pyarrow as pa

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def main():
    profile = ROOT/'analysis/neuron_assays/model_response_profiles.csv'
    names = {r['root_id']: r for r in pq.read_table(OUT/'catalog_139255.parquet', columns=[
        'root_id','display_name','cell_type','hemibrain_type','harmonized_cell_type',
        'functional_role','harmonized_cell_function','published_names']).to_pylist()}
    with profile.open(encoding='utf8', newline='') as f:
        profiles = list(csv.DictReader(f))
    assert len(profiles) == len({r['root_id'] for r in profiles})
    assert {r['root_id'] for r in profiles} <= set(names)
    conditions = ('jo_ce','jo_f','jo_all','sugar','water','bitter')
    joined = []
    for p in profiles:
        row = {**names[p['root_id']], 'model_evidence': p['evidence']}
        assert row['model_evidence'] == 'response_in_fixed_computational_model_only'
        for condition in conditions:
            total = int(p[f'{condition}_all600ms_spikes'])
            forced = int(p[f'{condition}_forced_input_spikes'])
            assert total >= forced >= 0
            row[f'{condition}_all600ms_spikes'] = total
            row[f'{condition}_forced_input_spikes'] = forced
            row[f'{condition}_non_forced_spikes'] = total - forced
        row['max_non_forced_spikes'] = max(row[f'{c}_non_forced_spikes'] for c in conditions)
        row['max_response_conditions'] = '|'.join(c for c in conditions if row[f'{c}_non_forced_spikes'] == row['max_non_forced_spikes']) if row['max_non_forced_spikes'] else ''
        joined.append(row)
    joined.sort(key=lambda r: (-r['max_non_forced_spikes'], r['root_id']))
    pq.write_table(pa.Table.from_pylist(joined), OUT/'named_model_responses.parquet', compression='zstd')
    with (OUT/'named_model_responses.csv').open('w', encoding='utf8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(joined[0])); w.writeheader(); w.writerows(joined)
    summary = {'schema': 'fly.named-model-responses.v1', 'model_source': str(profile.relative_to(ROOT)).replace('\\','/'),
               'model_source_sha256': hashlib.sha256(profile.read_bytes()).hexdigest(), 'exact_joined_roots': len(joined),
               'missing_catalog_roots': 0, 'roots_with_non_forced_spikes': sum(r['max_non_forced_spikes'] > 0 for r in joined),
               'responsive_roots_without_published_function': sum(r['functional_role'] == 'unknown' for r in joined),
               'responsive_roots_without_any_name': sum(r['display_name'] == 'unbenannt' for r in joined),
               'conditions': list(conditions), 'all_biological_catalog_fields_unchanged': True,
               'interpretation': 'Responses of a fixed computational model. Non-forced means total minus imposed input spikes, not baseline-subtracted biological activity. Highest-condition labels describe this protocol only.',
               'top20_non_forced_responses': joined[:20]}
    (OUT/'model_response_join_audit.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps({k:v for k,v in summary.items() if k != 'top20_non_forced_responses'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
