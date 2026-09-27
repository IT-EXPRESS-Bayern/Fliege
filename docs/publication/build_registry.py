# SPDX-License-Identifier: MIT
"""Package existing provenance and audits for publication; never run a simulation.

Run from the repository root: python docs/publication/build_registry.py
Writes only this directory. Original input data and audit outputs remain unchanged.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
DAY = '2026-09-27'


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8-sig'))


def sha(relative):
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if k != 'root'}
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, str):
        value = value.replace(str(ROOT), '.').replace(ROOT.as_posix(), '.')
        return value
    return value


def save(name, value):
    text = json.dumps(clean(value), ensure_ascii=False, indent=2) + '\n'
    assert not re.search(r'[A-Za-z]:[\\/](?:Users|Documents)[\\/]', text)
    assert 'chatgpt.com/c/' not in text and 'codex://threads/' not in text
    (OUT / name).write_text(text, encoding='utf-8')


def assessment(item):
    key = item['id']
    url = item.get('source_url', '') or ''
    path = item['path']
    result = {'status': 'retained_source_note_not_newly_cleared',
              'rule': 'Retain source-specific rights; the project code/docs license does not replace them.'}
    if '22260924' in url or key == 'pugliese_cpg_archived_replicate0_parameters':
        result = {'status': 'verified_original_data_license', 'license': 'CC-BY-4.0',
                  'authority': 'https://zenodo.org/api/records/22260924',
                  'rule': 'Pugliese original data attribution; extraction/adaptation must be indicated.'}
    elif '10676866' in url or '10877326' in url or key in ('flywire_ids', 'flywire_edges'):
        result = {'status': 'record_license_verified_general_platform_conflict', 'license': 'CC-BY-4.0 in specific Zenodo metadata',
                  'conflicting_general_policy': 'CC-BY-NC-4.0 at https://flywire.ai/guidelines',
                  'rule': 'Keep exact release/source and both statements; no blanket commercial-use clearance.'}
    elif 'princeton' in key or 'codex.flywire.ai' in url or 'flywire-data/codex' in url:
        result = {'status': 'general_official_policy_conservative', 'license': 'CC-BY-NC-4.0',
                  'authority': 'https://flywire.ai/guidelines',
                  'rule': 'Keep attribution and noncommercial condition; no project-license override.'}
    elif key == 'flywire_annotations' or 'flywire_annotations' in url:
        result = {'status': 'exact_release_license_unresolved',
                  'rule': 'No standalone license located for pinned v2.1.0 TSV; do not infer from a different archive.'}
    elif '7WTH1N' in url or key.startswith('banc_') or key.startswith('sensorimotor_'):
        result = {'status': 'dataset_license_verified_derived_claims_remain_separate', 'license': 'CC-BY-4.0',
                  'authority': 'https://doi.org/10.7910/DVN/7WTH1N',
                  'rule': 'Credit BANC authors and version v3.0/v888; identify project transformations and separate literature claims.'}
    elif url == 'https://male-cns.janelia.org/download/' or key in ('malecns_v1_traced_edges', 'malecns_v1_annotations', 'malecns_v1_transmitters', 'malecns_v1_roles'):
        result = {'status': 'official_dataset_license_verified', 'license': 'CC-BY-4.0',
                  'authority': 'https://male-cns.janelia.org/download/',
                  'rule': 'Credit MaleCNS/FlyEM and publication, version and adaptations; separate supplemental repository rights.'}
    elif 'DoOR.data' in url or key == 'fafb_olfactory_crosswalk':
        result = {'status': 'pinned_source_declaration_verified', 'license': 'CC-BY-SA-4.0 for DoOR-derived content',
                  'rule': 'Preserve attribution and share-alike obligations; review other joined sources separately.'}
    elif key == 'eon_nodes' or 'eonsystemspbc' in url:
        result = {'status': 'repository_declaration_verified', 'license': 'GPL-2.0-or-later except identified third-party components',
                  'rule': 'Do not treat this code license as a new license for underlying FlyWire data.'}
    elif key in ('shiu_nodes', 'shiu_edges'):
        result = {'status': 'repository_code_license_verified_dataset_rights_separate', 'license': 'MIT for Shiu code',
                  'rule': 'Underlying connectivity data retains its own attribution/license; do not clear data solely from code license.'}
    elif 'smpuglie/Pugliese_2026' in url:
        result = {'status': 'upstream_README_MIT_declaration_verified_full_notice_not_in_local_subset',
                  'license': 'MIT declared for repository code; BANC data remains CC-BY-4.0',
                  'rule': 'Obtain/preserve full copyright and MIT notice before vendoring original code.'}
    elif key.startswith('pugliese_cpg_'):
        result = {'status': 'derived_original_model_output',
                  'license': 'Original data CC-BY-4.0; upstream code MIT declaration; project code separately licensed',
                  'rule': 'Credit Pugliese/BANC, describe CPU port and original replicate 0. Do not call output an original saved trajectory.'}
    elif key == 'flybody_trained_policies':
        result = {'status': 'figshare_API_verified', 'license': 'GPL-3.0-or-later',
                  'authority': 'https://api.figshare.com/v2/articles/25309105',
                  'rule': 'Distinct from Apache-2.0 FlyBody repository; do not bundle policies under Apache or MIT.'}
    elif 'flygym' in url.lower() or 'TuragaLab/flybody' in url:
        result = {'status': 'repository_license_verified', 'license': 'Apache-2.0 for repository code',
                  'rule': 'Preserve license, applicable NOTICE and changes; separately downloaded datasets retain separate licenses.'}
    elif 'drosophila_neuropeptides' in url:
        result = {'status': 'pinned_repository_license_verified', 'license': 'CC-BY-4.0',
                  'rule': 'Preserve attribution; cross-specimen projections remain hypotheses.'}
    elif 'visual-system-parts-list' in url:
        result = {'status': 'pinned_repository_license_verified', 'license': 'Apache-2.0',
                  'rule': 'Preserve Apache notices and underlying FlyWire data attribution/terms.'}
    elif key.startswith('stuerner_') or key.startswith('tastekin_') or key == 'malecns_flywire_author_type_mapping':
        result = {'status': 'exact_source_redistribution_unresolved',
                  'rule': 'Cite original; no blanket redistribution or project-license claim for mixed derived tables.'}
    elif not url and (key.startswith('fafb_') or key.startswith('malecns_')):
        result = {'status': 'mixed_derived_sources_require_claim_level_review',
                  'rule': 'Follow each source and join; the derived filename or project license is not independent clearance.'}
    result['checked_on'] = DAY
    return result


def attribution(item):
    key, url = item['id'], item.get('source_url', '') or ''
    line = 'Project analysis by IT-EXPRESS Bayern; biological-source authors remain credited through the input audits and joins.'
    if key in ('flywire_ids', 'flywire_edges') or '10676866' in url or 'princeton' in key:
        line = 'FlyWire Consortium; Dorkenwald et al. (2024); detector-specific contributors identified by the original release.'
    elif 'annotation' in key and 'fafb_' not in key and 'malecns' not in key and 'banc_' not in key:
        line = 'Schlegel et al. (2024), Dorkenwald et al. (2024), and contributors listed by flyconnectome/flywire_annotations at the pinned release.'
    elif key.startswith('banc_') or key.startswith('sensorimotor_') or '7WTH1N' in url:
        line = 'Bates et al. (2026) and the BANC reconstruction/annotation contributors; project selection, path analysis and model assumptions by IT-EXPRESS Bayern.'
    elif 'malecns' in key or 'male-cns.janelia.org' in url:
        line = 'Berg et al. (2026); HHMI Janelia FlyEM, Cambridge/MRC LMB and Google Research contributors; exact supplemental authors in the original source.'
    elif 'pugliese' in key:
        line = 'Pugliese et al.; BANC data contributors. Project CPU-port analyses and interventions are separate from original published simulation outputs.'
    elif key.startswith('shiu_'):
        line = 'Shiu et al. (2024); original code copyright Philip Shiu and Nico Spiller; FlyWire data contributors.'
    elif key.startswith('eon_'):
        line = 'Eon Systems PBC and repository contributors; separately attributed Shiu/MIT and FlyWire components.'
    elif key.startswith('stuerner_'):
        line = 'Stürner, Brooks et al.; Comparative connectomics of Drosophila descending and ascending neurons (2025).'
    elif key.startswith('tastekin_'):
        line = 'Tastekin, de Haan Vicente et al.; The complete gustatory connectome of adult Drosophila reveals how taste guides feeding, foraging, and social behavior (2026).'
    elif key.startswith('calle_'):
        line = 'Calle-Schuler, Santana-Cruz et al.; eLife 108044 (2026), original mechanosensory/grooming supplementary tables.'
    elif 'DoOR.data' in url or key.startswith('door_'):
        line = 'Daniel Münch, C. Giovanni Galizia and DoOR.data contributors; underlying experimental studies credited in the source package.'
    elif 'neuropeptide' in key:
        line = 'Contributors to flyconnectome/drosophila_neuropeptides and the original experimental studies listed in its CITATIONS.md; project type-level projections remain hypotheses.'
    elif 'visual-system-parts-list' in url:
        line = 'Matsliah et al. (2024), Murthy laboratory and visual-system-parts-list contributors; FlyWire reconstruction contributors.'
    elif 'flybody' in key:
        line = 'FlyBody authors and Turaga laboratory contributors; original article and Figshare dataset authors credited at the linked sources.'
    elif 'flygym' in key:
        line = 'NeuroMechFly/FlyGym authors and NeLy-EPFL contributors; separate kinematic dataset creators credited in its Dataverse record.'
    elif url:
        line = 'Authors and contributors of the exact linked source; the source credit is not replaced by project or AI attribution.'
    return {'credit_line': line, 'exact_source_url': url or None,
            'instruction': 'Retain original author/copyright notices, exact source version and adaptation notice; this short line is not a replacement for full source citations.'}


def main():
    pack_path = 'analysis/model_integration_pack.json'
    pack = read(pack_path)
    assert len(pack['inputs']) == 160 and len(pack['joins']) == 46
    inputs = []
    for original in pack['inputs']:
        entry = clean(original)
        relative = entry['path']
        assert not Path(relative).is_absolute() and '..' not in Path(relative).parts
        entry['publication_license_assessment'] = assessment(entry)
        entry['publication_attribution'] = attribution(entry)
        entry['bundled_in_public_release'] = None
        entry['bundled_in_public_release_note'] = 'Inventory is independent of Git inclusion; see release file tree.'
        inputs.append(entry)
    assert len({i['id'] for i in inputs}) == 160
    registry = {
        'schema': 'fly.publication-source-registry.v1', 'as_of': DAY,
        'scope': 'All 160 registered integration inputs and all 46 joins; not 160 independent papers and not a bundle manifest.',
        'source_manifest': {'path': pack_path, 'sha256': sha(pack_path)},
        'id_policy': pack['id_policy'], 'specimen_namespaces': pack.get('specimen_namespaces'),
        'version_gate': pack['version_gate'], 'input_count': len(inputs), 'join_count': len(pack['joins']),
        'license_note_policy': 'Original license_note strings retained as provenance, not newly verified blanket permissions. publication_license_assessment takes precedence for this release review.',
        'inputs': inputs, 'joins': pack['joins'],
    }
    save('source_registry.json', registry)
    lines = ['# Vollständiger Quellenindex', '',
             f'Stand: {DAY}. 160 registrierte Eingaben, 46 Join-Regeln. Originale und Ableitungen sind beide enthalten; Originaldateien müssen nicht Teil des Git-Releases sein.', '',
             'Vollständige Felder und Verknüpfungsregeln: [source_registry.json](source_registry.json). Lizenzdetails: [REUSE_AND_LICENSES.md](REUSE_AND_LICENSES.md).', '',
             '| Nr. | Eingabe | Relativer Forschungspfad | Originalquelle | Rechteprüfung |',
             '|---:|---|---|---|---|']
    for idx, i in enumerate(inputs, 1):
        url = i.get('source_url')
        source = f'[Quelle]({url})' if url else 'Projektableitung; Herkunft über Audit/Joins'
        lines.append(f"| {idx} | `{i['id']}` | `{i['path']}` | {source} | `{i['publication_license_assessment']['status']}` |")
    (OUT / 'SOURCE_INDEX.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')

    status = read('analysis/research_session_status.json')
    catalog = read('analysis/neuron_catalog/audit.json')
    audit_paths = ['analysis/neuron_catalog/audit.json', 'analysis/model_original_edge_comparison.json',
                   'analysis/neuron_assays/audit.json', 'analysis/neuron_assays/jo_diagnostic.json',
                   'analysis/motor_output_atlas/audit.json', 'analysis/sensorimotor_mapping/audit.json',
                   'app/data/sensorimotor_audit.json', 'analysis/cpg_reproduction/result_verification.json',
                   'analysis/cpg_reproduction/run33241778_replicate0/summary.json',
                   'analysis/flight_control_mapping/audit.json', 'app/data/flight_audit.json']
    snapshot = {'schema': 'fly.publication-evidence-snapshot.v1', 'as_of': DAY,
                'new_simulations_run_for_publication': False,
                'audits': [{'path': p, 'sha256': sha(p)} for p in audit_paths],
                'catalog': {k: catalog[k] for k in ('root_count', 'duplicate_root_ids', 'display_name_present', 'roots_with_source_role', 'unknown_function_roots')},
                'metrics': {k: status[k] for k in (
                    'neural_main_trials', 'neural_diagnostic_trials', 'neural_reference_responsive_roots', 'jo_selectivity',
                    'motor_output_atlas_ids', 'sensorimotor_trials', 'sensorimotor_transfer_probes', 'sensorimotor_integration_steps',
                    'sensorimotor_findings', 'cpg_cpu_conditions', 'cpg_result_checks_passed', 'cpg_original_trajectory_comparison_complete',
                    'flight_roll_trials', 'flight_roll_integration_steps', 'flight_neural_propagation_simulated',
                    'flight_sensor_to_motor_edges_simulated', 'autonomous_flight', 'flight_free_translation',
                    'full_brain_closed_autonomy', 'sensory_partial_neural_propagation', 'original_graph_modified')},
                'graph_comparison': {'directed_pairs': pack['audit']['original_vs_shiu_pair_count'],
                                     'synapse_count_mismatches': pack['audit']['original_vs_shiu_synapse_count_mismatches']},
                'interpretation': 'Counts are from frozen model/audit outputs. They do not demonstrate biological reconstruction or validate physiological parameters.'}
    save('evidence_snapshot.json', snapshot)
    literature_paths = ['analysis/motor_control_sources.json', 'analysis/flight_control_mapping/sources.json']
    save('literature_registry.json', {
        'schema': 'fly.publication-literature-registry.v1', 'as_of': DAY,
        'scope': 'Two existing motor/flight primary-source registers preserved in full; related sensory/function sources are additionally registered in source_registry.json.',
        'historical_register_policy': 'Original per-source records retain their own acquisition and interpretation dates. Current run/download status is in source_registry.json and evidence_snapshot.json; repository notebook availability is not evidence of a reproduced published run.',
        'registers': [{'path': p, 'sha256': sha(p), 'content': read(p)} for p in literature_paths]})
    save('publication_registry_audit.json', {
        'schema': 'fly.publication-registry-audit.v1', 'as_of': DAY,
        'input_count': len(inputs), 'unique_input_ids': len({i['id'] for i in inputs}),
        'join_count': len(pack['joins']), 'all_registered_paths_present_in_research_workspace': all((ROOT/i['path']).is_file() for i in inputs),
        'original_inputs_preserved': all({k:v for k,v in i.items() if not k.startswith('publication_') and not k.startswith('bundled_')} == clean(orig) for i,orig in zip(inputs,pack['inputs'])),
        'license_review_status_counts': dict(Counter(i['publication_license_assessment']['status'] for i in inputs)),
        'original_graph_modified': False, 'simulations_executed': 0,
        'output_hashes': {p: hashlib.sha256((OUT/p).read_bytes()).hexdigest() for p in ('source_registry.json','SOURCE_INDEX.md','evidence_snapshot.json','literature_registry.json')},
        'caveat': 'Path presence refers to the private research workspace at publication preparation; it does not assert that original datasets are included in the public repository.'})
    print(json.dumps({'registered_inputs':len(inputs), 'join_rules':len(pack['joins']), 'simulation_runs':0}))


if __name__ == '__main__':
    main()
