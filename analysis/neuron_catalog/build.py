"""Build an exact-root catalog while retaining the evidence grain of each claim.

Run: analysis/.venv/Scripts/python.exe analysis/neuron_catalog/build.py
No graph, neuron annotation or biological function is changed by this script.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import openpyxl
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
APP = ROOT / 'app/data'
SOURCES = {}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def source(key, relative, url, grain, caveat=''):
    p = ROOT / relative
    SOURCES[key] = {'id': key, 'file': relative, 'url': url, 'sha256': digest(p),
                    'bytes': p.stat().st_size, 'grain': grain, 'caveat': caveat}
    return p


def read_csv(p):
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t' if p.suffix == '.tsv' else ','))


def write_json(p, data, compact=False):
    p.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':') if compact else None,
                           indent=None if compact else 2) + '\n', encoding='utf-8')


def write_rows(stem, rows):
    assert rows
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, OUT / f'{stem}.parquet', compression='zstd')
    with (OUT / f'{stem}.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT.mkdir(exist_ok=True)
    APP.mkdir(exist_ok=True)
    root_path = source('v783_roots', 'data/flywire_fafb_v783/proofread_root_ids_783.npy',
                       'https://doi.org/10.5281/zenodo.10676866', 'one proofread root per entry')
    ann_path = source('annotation_v2_1_0', 'data/flywire_annotations_v2.1.0/Supplemental_file1_neuron_annotations.tsv',
                     'https://github.com/flyconnectome/flywire_annotations/releases/tag/v2.1.0',
                     'one root annotation per row', 'Predicted top_nt is distinct from known_nt; blank type is unknown.')
    roots = sorted(str(int(v)) for v in np.load(root_path))
    rootset = set(roots)
    annotations = read_csv(ann_path)
    assert len(roots) == len(rootset) == 139255
    assert len(annotations) == len({r['root_id'] for r in annotations}) == len(roots)
    by_root = {r['root_id']: r for r in annotations}
    assert rootset == set(by_root)
    claims = []
    rootclaims = defaultdict(list)
    names = defaultdict(list)
    sides = []
    join_audits = []

    def claim(root, key, row, label, kind, name='', function='', hypothesis='', side='', extra=None):
        assert isinstance(root, str) and root.isdecimal() and len(root) == 18, (root, key, row)
        cid = f'{key}:{row}'
        item = {'claim_id': cid, 'root_id': root, 'source_id': key, 'source_row': str(row),
                'label': label, 'evidence_kind': kind, 'published_name': name,
                'functional_role': function, 'type_hypothesis': hypothesis, 'source_side': side,
                'exact_v783_match': root in rootset, 'details_json': json.dumps(extra or {}, ensure_ascii=False, sort_keys=True)}
        claims.append(item)
        if root in rootset:
            rootclaims[root].append(item)
            if name and name not in names[root]:
                names[root].append(name)
            normalized = {'L': 'left', 'R': 'right'}.get(side, side)
            if normalized in ('left', 'right') and by_root[root]['side'] not in ('', normalized):
                sides.append({'root_id': root, 'claim_id': cid, 'source_side': side,
                              'original_side': by_root[root]['side'], 'source_id': key,
                              'status': 'side_convention_or_identity_requires_review'})
        return item

    def audit_join(key, selected):
        ids = [r['root_id'] for r in selected]
        join_audits.append({'source': key, 'claim_rows': len(ids), 'unique_source_ids': len(set(ids)),
                           'matched_unique_roots': len(set(ids) & rootset),
                           'unmatched_root_ids': sorted(set(ids) - rootset)})

    # This table belongs to the BANC publication, but its key is explicitly FAFB
    # root_783. It therefore supplies same-specimen metadata, not imported BANC
    # neuron identities or synapses. Preserve it alongside the pinned annotation.
    key = 'banc2026_fafb_annotation'
    p = source(key, 'data/research_sources/other/banc_2026/supplemental_data_3.txt',
               'https://doi.org/10.1038/s41586-026-10735-w', 'one harmonized FAFB root_783 annotation per row',
               'Published curated function annotation; no physiological experiment on this individual root. FAFB metadata, not BANC root IDs.')
    harmonized_rows = read_csv(p)
    assert len(harmonized_rows) == len({r['root_783'] for r in harmonized_rows})
    assert all(r['dataset'] == 'FAFB' for r in harmonized_rows)
    harmonized = {r['root_783']: r for r in harmonized_rows}
    harmonized_source_rows = {r['root_783']: n for n, r in enumerate(harmonized_rows, 2)}
    def known(value):
        return str(value or '').strip() not in ('', 'NA', 'na', '-')
    added = []
    for n, r in enumerate(harmonized_rows, 2):
        root = r['root_783']
        if root not in rootset:
            continue
        fn = r['cell_function'] if known(r['cell_function']) else ''
        detail = r['cell_function_detailed'] if known(r['cell_function_detailed']) else ''
        new_name = r['cell_type'] if known(r['cell_type']) else ''
        new_alias = new_name and new_name not in (by_root[root]['cell_type'], by_root[root]['hemibrain_type'])
        if fn or detail or new_alias:
            label = fn + (': ' + detail if detail else '') if fn else detail or ('Zelltyp ' + new_name)
            c = claim(root, key, n, label, 'published_curated_function_annotation' if fn or detail else 'published_anatomical_identity',
                      new_name, function=label if fn or detail else '', side=r['side'], extra=r)
            added.append(c)
    audit_join(key, added)

    # Named identity tables are direct within-specimen root joins. DN/AN direction
    # and a published cell name do not establish a specific behavioral function.
    neck_dir = 'data/research_sources/other/stuerner_neckconnective/'
    neck_types = defaultdict(list)
    for key, file in [('stuerner_dn', 'Supplemental_file5_FAFB_DNs.tsv'),
                      ('stuerner_an_sa', 'Supplemental_file8_FAFB_ANs_SAs.tsv')]:
        p = source(key, neck_dir + file, 'https://doi.org/10.1038/s41586-025-08925-z', 'exact FAFB root identity',
                   'Source side is retained independently; direction does not identify behavior.')
        added = []
        for n, r in enumerate(read_csv(p), 2):
            direction = {'DN': 'absteigende Verbindung Gehirn–VNC', 'AN': 'aufsteigende Verbindung VNC–Gehirn',
                         'SA': 'aufsteigende sensorische Verbindung'}.get(r['class'], r['class'])
            c = claim(r['root_id'], key, n, direction, 'published_anatomical_identity', r['type'],
                      side=r['side'], extra={'class': r['class'], 'synonyms': r['synonyms'],
                      'confidence_in_source': r.get('confidence_LM_1_5', r.get('confidence', ''))})
            added.append(c)
            neck_types[r['type']].append(r)
        audit_join(key, added)

    # Primary physiology is reported at cell-type level, in other recorded flies.
    # Joining the type to FAFB is an explicit transfer hypothesis, not a recording.
    key = 'steering_experiment_2024'
    SOURCES[key] = {'id': key, 'file': '', 'url': 'https://doi.org/10.1016/j.cell.2024.08.033',
                    'sha256': None, 'bytes': None, 'grain': 'experimentally studied cell type in other animals',
                    'caveat': 'FAFB identity from Stürner; physiological role transferred by type, no recording in FAFB specimen.'}
    for typ, phrase in [('DNa02', 'Lenken beim Gehen; kürzere Schritte auf der Kurveninnenseite'),
                        ('DNg13', 'Lenken beim Gehen; längere Schritte auf der Kurvenaußenseite')]:
        for r in neck_types[typ]:
            claim(r['root_id'], key, f'{typ}_{r["side"]}', phrase, 'published_experiment_type_transfer',
                  typ, hypothesis=phrase, side=r['side'], extra={'identity_source': 'stuerner_dn'})

    key = 'tastekin_2026'
    p = source(key, 'data/research_sources/other/tastekin/tastekin_2026_cell_table_s1.xlsx',
               'https://doi.org/10.1016/j.cell.2026.08.016', 'exact FAFB v783 root after Connectome filter',
               'Motor target is anatomical; receptor preference or muscle force is not inferred from type name.')
    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    taste_added = []
    taste_mn9 = []
    for ws in wb:
        it = ws.iter_rows(values_only=True)
        headers = next(it)
        for n, values in enumerate(it, 2):
            r = {k: v for k, v in zip(headers, values) if k}
            if not str(r.get('Connectome', '')).startswith('FAFB'):
                continue
            root = r['Body_ID']
            assert isinstance(root, str), f'Lossy workbook ID at {ws.title}:{n}'
            details = {k: v for k, v in r.items() if k not in ('Body_ID', 'Connectome')}
            typ = '' if r['Type'] in (None, '-') else str(r['Type'])
            if ws.title == 'GRNs':
                label = f'Geschmackssensor: {r["Subclass"]}; Typ {typ or "unbestimmt"}'
            else:
                label = f'Motorneuron {typ}; Zielmuskel {r["Target_Muscle"]}'
            c = claim(root, key, f'{ws.title}!{n}', label, 'published_anatomical_identity', typ,
                      function=label, side=r['Root_Side'], extra=details)
            taste_added.append(c)
            if ws.title == 'MNs' and typ == 'MN9':
                taste_mn9.append({'root_id': root, 'name': 'MN9_' + r['Root_Side'], 'side': r['Root_Side'],
                                 'claim_id': c['claim_id']})
    wb.close()
    audit_join(key, taste_added)

    key = 'bristle_2026'
    p = source(key, 'data/research_sources/other/calle_schuler_bmn/Supplementary_file_1_BMNs.csv',
               'https://doi.org/10.7554/eLife.108044.3', 'exact v783 bristle mechanosensory root',
               'Head-region identity is not a calibrated touch-to-current mapping or grooming policy.')
    added = []
    bristle_sets = defaultdict(list)
    for n, r in enumerate(read_csv(p), 2):
        label = f'Borsten-Mechanosensor: {r["bmn_type"]}'
        c = claim(r['flywire_id_v783'], key, n, label, 'published_anatomical_identity', r['bmn_name'],
                  function=label, extra={'type': r['bmn_type'], 'nerve': r['nerve']})
        added.append(c)
        bristle_sets[r['bmn_type']].append(r['flywire_id_v783'])
    audit_join(key, added)

    key = 'shiu_2024'
    p = source(key, 'data/research_sources/shiu/derived/shiu_supplement_index.json',
               'https://doi.org/10.1038/s41586-024-07763-9', 'v630 workbook candidate with exact v783 root availability check',
               'Published model table v630; exact ID availability does not reproduce published rates in v783.')
    source('shiu_workbook', 'data/research_sources/shiu/supplementary_tables_1-12.xlsx',
           'https://doi.org/10.1038/s41586-024-07763-9', 'original supplementary workbook')
    shiu = json.loads(p.read_text(encoding='utf-8'))
    assert SOURCES['shiu_workbook']['sha256'] == shiu['workbook_sha256']
    group_labels = {'sugar_grn': 'Zucker-Geschmackssensor, Shiu-Reizgruppe',
                    'water_grn': 'Wasser-Geschmackssensor, Shiu-Reizgruppe',
                    'bitter_grn': 'Bitter-Geschmackssensor, Shiu-Reizgruppe',
                    'ir94e_grn': 'Ir94e-Geschmackssensor; Reizpräferenz offen',
                    'feeding_output': 'MN9-Auslese für Proboscis-Heben',
                    'grooming_circuit': 'Antennenputz-Schaltung; Seite gesondert prüfen'}
    shiu_sets = defaultdict(list)
    added = []
    for r in shiu['candidates']:
        label = group_labels.get(r['category'], 'Johnston-Organ: Antennen-Mechanosensorik, ' + r['category'])
        c = claim(r['source_root_id'], key, f'{r["source_sheet"]}!{r["source_excel_row"]}', label,
                  'published_model_cross_release_candidate', r['source_name'], hypothesis=label,
                  side='left' if r['source_name'].endswith('_l') else 'right' if r['source_name'].endswith('_r') else '',
                  extra={'category': r['category'], 'mapping_status': r['mapping_status'], 'paper_release': 'v630'})
        added.append(c)
        if r['v783_exact_root_present'] and r['shiu_v783_completeness_exact_root_present']:
            shiu_sets[r['category']].append(r['source_root_id'])
    audit_join(key, added)

    key = 'olfactory_type_projection'
    p = source(key, 'data/research_sources/other/olfaction/fafb_olfactory_root_id_crosswalk.csv',
               'https://doi.org/10.1038/s44319-025-00476-8', 'FAFB root to glomerulus/type to pooled receptor literature',
               'DoOR lacks FAFB IDs; receptor and odor response are type-level transfer hypotheses. Mapping status retained.')
    added = []
    for n, r in enumerate(read_csv(p), 2):
        label = f'Geruchseingang: Glomerulus {r["glomerulus"]}'
        hyp = f'Rezeptor-Kandidat {r["benton_2025_receptor"] or "unbekannt"}; {r["mapping_status"]}'
        added.append(claim(r['root_id'], key, n, label, 'type_level_transfer_hypothesis',
                           hypothesis=hyp, side=r['side'], extra=r))
    audit_join(key, added)

    key = 'neuropeptide_type_projection'
    p = source(key, 'data/research_sources/other/neuropeptides/fafb_neuropeptide_type_candidates.csv',
               'https://github.com/flyconnectome/drosophila_neuropeptides/tree/8df0b4506d28646ce6e77947515ba03246f5275d', 'type-matched peptide evidence from multiple specimens',
               'No measured peptide expression in the FAFB root; source-specific method and evidence confidence retained.')
    added = []
    for n, r in enumerate(read_csv(p), 2):
        label = f'Peptid-Hypothese: {r["peptide"]}'
        added.append(claim(r['root_id'], key, n, label, 'type_level_transfer_hypothesis',
                          hypothesis=label, extra=r))
    audit_join(key, added)

    # Catalog grain never changes: exactly one original root per row.
    catalog = []
    for root in roots:
        a = dict(by_root[root])
        rc = rootclaims[root]
        anatomy = list(dict.fromkeys(c['label'] for c in rc if c['evidence_kind'] == 'published_anatomical_identity'))
        roles = list(dict.fromkeys(c['functional_role'] for c in rc if c['functional_role']))
        experiment = list(dict.fromkeys(c['label'] for c in rc if c['evidence_kind'] == 'published_experiment_type_transfer'))
        hypothesis = list(dict.fromkeys(c['type_hypothesis'] for c in rc if c['type_hypothesis']))
        # Published root-specific names can supplement a missing official type;
        # never overwrite the pinned cell_type / hemibrain_type fields.
        a.update({'display_name': a['cell_type'] or a['hemibrain_type'] or (names[root][0] if names[root] else 'unbenannt'),
                  'published_names': '|'.join(names[root]), 'published_anatomical_roles': '|'.join(anatomy),
                  'functional_role': '|'.join(roles) or 'unknown',
                  'published_experimental_type_roles': '|'.join(experiment),
                  'type_function_hypotheses': '|'.join(hypothesis),
                  'evidence_ids': '|'.join(c['claim_id'] for c in rc),
                  'model_role': 'unassigned', 'model_role_note': 'No automatic runtime motor assignment; candidate assay sets are separate.'})
        h = harmonized.get(root, {})
        a.update({'harmonized_' + k: (h.get(k, '') if known(h.get(k, '')) else '')
                  for k in harmonized_rows[0] if k not in ('root_783', 'dataset')})
        a['harmonized_source_row'] = str(harmonized_source_rows.get(root, ''))
        catalog.append(a)
    write_rows('catalog_139255', catalog)
    write_rows('source_claims', claims)
    if sides:
        write_rows('side_conflicts', sides)
    unmatched = [r for r in claims if not r['exact_v783_match']]
    if unmatched:
        write_rows('unmatched_source_claims', unmatched)

    groups = {k: sorted(set(v)) for k, v in shiu_sets.items()}
    groups['jon_ce'] = sorted(set(groups.get('jon_c', []) + groups.get('jon_e', [])))
    groups['jon_all'] = sorted(set(sum([v for k, v in groups.items() if k in ('jon_c','jon_e','jon_f','jon_other')], [])))
    groups['mn9_v783_tastekin'] = sorted(r['root_id'] for r in taste_mn9)
    for typ in ('DNa02', 'DNg13'):
        groups[typ] = sorted(r['root_id'] for r in neck_types[typ])
    for k, v in bristle_sets.items():
        groups['bristle_' + k] = sorted(set(v))
    for ids in groups.values():
        assert len(ids) == len(set(ids)) and set(ids) <= rootset
    assay_sets = {'schema': 'fly.neuron-assay-sets.v1', 'dataset': 'FAFB v783', 'groups': groups,
        'group_counts': {k: len(v) for k, v in groups.items()}, 'mn9_current_source': taste_mn9,
        'steering_identity': {typ: [{'root_id': r['root_id'], 'source_side': r['side'],
            'original_annotation_side': by_root[r['root_id']]['side'],
            'lateralization_status': 'source_side_differs_from_original_annotation'} for r in neck_types[typ]] for typ in ('DNa02', 'DNg13')},
        'assays': [{'id': 'taste_to_MN9', 'input_groups': ['sugar_grn','water_grn','bitter_grn'], 'readout_groups': ['mn9_v783_tastekin'],
                    'source': SOURCES['shiu_2024']['url'], 'caveat': 'v630 published response is an external qualitative comparison; gains and response magnitudes in v783 must be tested.'},
                   {'id': 'antenna_to_grooming', 'input_groups': ['jon_ce','jon_f'], 'readout_root_ids': ['720575940630907434','720575940616185531','720575940629806974'],
                    'source': SOURCES['shiu_2024']['url'], 'caveat': 'aDN1/aDN2 source suffix _l conflicts with original side=right; exclude lateral motor assignment.'}],
        'limitations': ['Stuerner source-side labels differ from pinned original side for all four DNa02/DNg13 roots; do not collapse side conventions.',
                       'Stimulation and ablation measure the implemented model, not living-neuron function.',
                       'Direct stimulation of a readout mapped to a body action only tests that implementation; it is not independent evidence for the mapping.',
                       'All input-to-current and firing-to-body gains are model assumptions, requiring separate calibration.']}
    write_json(OUT / 'assay_sets.json', assay_sets)
    write_json(APP / 'neuron_catalog_assay_sets.json', assay_sets)

    cols = ['root_id','display_name','cell_type','hemibrain_type','super_class','cell_class','side','top_nt','known_nt','functional_role','evidence_ids','model_role','published_names']
    browser_claims = {c['claim_id']: {'label': c['label'], 'evidence_kind': c['evidence_kind'],
        'source_id': c['source_id'], 'source_row': c['source_row'],
        'functional_role': c['functional_role'], 'type_hypothesis': c['type_hypothesis']}
        for c in claims if c['exact_v783_match']}
    assert len({c['claim_id'] for c in claims}) == len(claims)
    write_json(APP / 'neuron_catalog_claims.json', {'schema': 'fly.neuron-catalog-claims.v1', 'claims_by_id': browser_claims, 'sources': list(SOURCES.values())}, compact=True)
    browser = {'schema': 'fly.neuron-catalog.v1', 'dataset': 'FAFB v783', 'columns': cols,
               'rows': [[r[c] for c in cols] for r in catalog], 'claims_url': './data/neuron_catalog_claims.json',
               'sources': list(SOURCES.values()), 'unknown_role': 'unknown', 'model_role': 'unassigned',
               'model_role_note': 'Assay participants are explicit in neuron_catalog_assay_sets.json; no automatic body control is inferred.'}
    write_json(APP / 'neuron_catalog.json', browser, compact=True)
    audit = {'schema': 'fly.neuron-catalog-audit.v1', 'built_utc': datetime.now(timezone.utc).isoformat(),
        'root_count': len(roots), 'catalog_rows': len(catalog), 'annotation_rows': len(annotations),
        'exact_root_join_complete': rootset == {r['root_id'] for r in catalog}, 'duplicate_root_ids': 0,
        'official_cell_type_present': sum(bool(r['cell_type']) for r in catalog),
        'official_cell_or_hemibrain_type_present': sum(bool(r['cell_type'] or r['hemibrain_type']) for r in catalog),
        'display_name_present': sum(r['display_name'] != 'unbenannt' for r in catalog),
        'unbenannt_roots': sum(r['display_name'] == 'unbenannt' for r in catalog),
        'roots_with_supplemental_evidence': len([r for r in roots if rootclaims[r]]),
        'roots_with_anatomical_role': sum(bool(r['published_anatomical_roles']) for r in catalog),
        'roots_with_source_role': sum(r['functional_role'] != 'unknown' for r in catalog),
        'roots_with_type_experimental_role': sum(bool(r['published_experimental_type_roles']) for r in catalog),
        'unknown_function_roots': sum(r['functional_role'] == 'unknown' for r in catalog),
        'source_claim_count': len(claims), 'claims_by_evidence_kind': dict(Counter(c['evidence_kind'] for c in claims)),
        'side_conflict_rows': len(sides), 'side_conflict_roots': len({s['root_id'] for s in sides}),
        'harmonized_fafb_rows': len(harmonized_rows), 'harmonized_exact_matched_roots': len(set(harmonized) & rootset),
        'harmonized_missing_original_roots': sorted(rootset - set(harmonized)),
        'harmonized_rows_outside_original_root_universe': len(set(harmonized) - rootset),
        'harmonized_function_annotated_roots': sum(known(harmonized[r]['cell_function']) for r in roots if r in harmonized),
        'joins': join_audits, 'group_counts': assay_sets['group_counts'],
        'checks': {'root_ids_all_strings': all(isinstance(r['root_id'], str) for r in catalog),
                   'all_assay_ids_in_v783': all(set(v) <= rootset for v in groups.values()),
                   'all_claim_ids_unique': len({c['claim_id'] for c in claims}) == len(claims),
                   'original_annotation_fields_unchanged': all(all(r[k] == by_root[r['root_id']][k] for k in by_root[r['root_id']]) for r in catalog),
                   'unmatched_claims_not_attached': all(c['exact_v783_match'] for c in claims if c['claim_id'] in browser_claims)},
        'sources': list(SOURCES.values()),
        'outputs': {p.name: {'bytes': p.stat().st_size, 'sha256': digest(p)} for p in [OUT/'catalog_139255.parquet', OUT/'source_claims.parquet', APP/'neuron_catalog.json']}}
    assert all(audit['checks'].values())
    write_json(OUT / 'audit.json', audit)
    print(json.dumps({k: audit[k] for k in ['root_count','display_name_present','unbenannt_roots','roots_with_supplemental_evidence','roots_with_source_role','side_conflict_rows','checks','outputs']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
