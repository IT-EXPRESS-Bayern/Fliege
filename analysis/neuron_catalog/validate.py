"""Independent boundary checks for exported neuron identities and evidence."""
from pathlib import Path
from collections import Counter
import csv
import json
import numpy as np
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def main():
    browser = json.loads((ROOT/'app/data/neuron_catalog.json').read_text(encoding='utf8'))
    details = json.loads((ROOT/'app/data/neuron_catalog_claims.json').read_text(encoding='utf8'))
    claim_by_id = details['claims_by_id']
    roots = set(map(lambda v: str(int(v)), np.load(ROOT/'data/flywire_fafb_v783/proofread_root_ids_783.npy')))
    with (ROOT/'data/flywire_annotations_v2.1.0/Supplemental_file1_neuron_annotations.tsv').open(encoding='utf8') as f:
        original = {r['root_id']: r for r in csv.DictReader(f, delimiter='\t')}
    exported = pq.read_table(OUT/'catalog_139255.parquet').to_pylist()
    ids = [r['root_id'] for r in exported]
    assert len(ids) == len(set(ids)) == 139255
    assert set(ids) == roots
    # Cross-check every original field rather than only a sampled display name.
    assert all(all(r[k] == v for k, v in original[r['root_id']].items()) for r in exported)
    bindex = {c: i for i, c in enumerate(browser['columns'])}
    browser_ids = [r[bindex['root_id']] for r in browser['rows']]
    assert set(browser_ids) == roots and len(browser_ids) == len(roots)
    assert all(isinstance(x, str) and len(x) == 18 for x in browser_ids)
    for row in browser['rows']:
        assert len(row) == len(browser['columns'])
        for cid in filter(None, row[bindex['evidence_ids']].split('|')):
            assert cid in claim_by_id, cid
    claims = pq.read_table(OUT/'source_claims.parquet').to_pylist()
    assert len({r['claim_id'] for r in claims}) == len(claims)
    assert all((r['root_id'] in roots) == r['exact_v783_match'] for r in claims)
    assert all(c['root_id'] in roots for c in claims if c['claim_id'] in claim_by_id)
    assert {r['claim_id'] for r in claims if r['exact_v783_match']} == set(claim_by_id)
    source_ids = {s['id'] for s in browser['sources']}
    assert all(c['source_id'] in source_ids for c in claim_by_id.values())
    # Exact current MN9-L comes from Tastekin, not guessed from missing v630 ID.
    mn9l = [c for c in claims if c['root_id'] == '720575940618238523' and c['source_id'] == 'tastekin_2026']
    assert len(mn9l) == 1 and mn9l[0]['published_name'] == 'MN9' and mn9l[0]['source_row'] == 'MNs!69'
    assert '720575940645521262' not in roots
    assert any(c['root_id'] == '720575940645521262' and not c['exact_v783_match'] for c in claims)
    sets = json.loads((OUT/'assay_sets.json').read_text(encoding='utf8'))
    assert all(set(v) <= roots and len(v) == len(set(v)) for v in sets['groups'].values())
    assert sets['group_counts']['sugar_grn'] == 20
    assert sets['group_counts']['jon_ce'] == 69
    assert sets['group_counts']['jon_f'] == 60
    assert sets['group_counts']['mn9_v783_tastekin'] == 2
    # Physiological claims remain explicitly transferred by type; peptide evidence
    # never supplies a measured individual-root motor role.
    assert all(c['evidence_kind'] == 'published_experiment_type_transfer' for c in claims if c['source_id'] == 'steering_experiment_2024')
    assert all(not c['functional_role'] for c in claims if c['source_id'] == 'neuropeptide_type_projection')
    assert all(r['model_role'] == 'unassigned' for r in exported)
    result = {'status': 'passed', 'checked_root_rows': len(ids), 'checked_original_cells': sum(len(v) for v in original.values()),
              'checked_browser_claim_references': sum(len(list(filter(None, r[bindex['evidence_ids']].split('|')))) for r in browser['rows']),
              'source_claim_rows': len(claims), 'unmatched_claims_excluded': sum(not c['exact_v783_match'] for c in claims),
              'checks': ['full_original_field_equality','full_root_universe_and_uniqueness','browser_decimal_string_ids',
                         'every_browser_claim_reference_resolves','claim_source_reference_integrity','assay_group_membership_and_uniqueness',
                         'independently_sourced_current_MN9_left','absent_v630_id_not_replaced','type_evidence_not_promoted','no_automatic_motor_assignment']}
    (OUT/'validation.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
