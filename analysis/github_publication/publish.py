"""Build a reviewed public-file manifest or copy it to a publication checkout.

This program never runs Git, downloads data, or runs scientific simulations.
Default mode only writes its manifest under analysis/github_publication.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'analysis/github_publication'
LIMIT = 10_000_000
APP_LIMIT = 40_000_000
SKIP_DIRS = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.cache', '.openai', '.codex', 'logs', 'dist'}
TEXT = {'.py', '.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx', '.html', '.css', '.json', '.jsonl', '.md', '.txt', '.csv', '.tsv', '.yaml', '.yml', '.toml', '.ps1', '.sh', '.svg', '.lock'}
CODE_DOC = TEXT - {'.csv', '.tsv', '.jsonl'}
PRIVATE = {'CLOUD_HANDOFF.md', 'app/cpg-download.html', 'app/data/cpg_download_status.json'}
BOOTSTRAP = {'publish.py', 'check_publication.py', 'README.md', 'license_review.json', 'PUBLICATION_NOTES.md'}
CPG = 'data/research_sources/other/pugliese_cpg_2026/'
CPG_INPUTS = {
    'W_20260217.npz', 'wTable_20260217_fullData.csv', 'wTable_20260217_fullData_consistentColumns.csv',
    'configs/neuron_params/default.yaml', 'configs/sim/default.yaml',
    'run33241778/logs/run_config.yaml', 'run33241778/.hydra/config.yaml', 'run33241778/.hydra/overrides.yaml',
    'run33241778/original_parameters_replicate0.npz',
}
PERSONAL_HOME = re.compile(r'[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s"\'<>]+|/(?:home|Users)/[^/\s"\'<>]+', re.I)
SECRET = [
    ('private_key', re.compile(r'-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----')),
    ('service_token', re.compile(r'\b(?:sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}|gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[A-Z0-9]{16})\b')),
]
SESSION_URL = re.compile(r'https?://chatgpt\.com/c/[a-f0-9-]{16,}[^\s"<>]*|codex://threads/[a-f0-9-]{16,}[^\s"<>]*', re.I)
LOCAL_URL = re.compile(r'https?://(?:localhost|127\.0\.0\.1)(?::\d+)?[^\s"<>)]*')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp-' + uuid.uuid4().hex)
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def scientific_config(path):
    return path.startswith(CPG) and path[len(CPG):] in CPG_INPUTS


def choice(rel, size):
    parts = Path(rel).parts
    name = parts[-1].lower()
    ext = Path(name).suffix
    if rel in PRIVATE or rel.startswith('analysis/cloud_transfer/'):
        return False, 'private_cloud_or_download_session'
    if name == '.env' or name.startswith('.env.') or name in {'.npmrc', '.pypirc', '.netrc', '.git-credentials', 'credentials.json', 'token.json'} or ext in {'.pem', '.key', '.p12', '.pfx'}:
        return False, 'credential_or_environment_filename'
    if rel.startswith('analysis/research_report_app/'):
        editable = rel.startswith('analysis/research_report_app/src/content/') or rel in {'analysis/research_report_app/src/data.json', 'analysis/research_report_app/src/theme.css'}
        return editable, 'authored_report_content_only' if editable else 'protected_Data_runtime_or_build_excluded'
    if any(p.lower() in SKIP_DIRS or p.startswith('.venv-') for p in parts[:-1]) and not scientific_config(rel):
        return False, 'environment_cache_or_runtime_directory'
    if ext in {'.log', '.pyc', '.pyo', '.part', '.crdownload', '.tmp'}:
        return False, 'runtime_or_incomplete_file'
    if rel.startswith('app/'):
        if ext in {'.png', '.jpg', '.jpeg', '.webp'}:
            return False, 'local_browser_screenshot_not_required'
        return (True, 'complete_app_and_replay_data') if size <= APP_LIMIT else (False, 'oversized_app_asset_review_required')
    if rel.startswith('brain/graph-'):
        return False, 'external_full_graph_rebuild_required'
    if rel.startswith('data/'):
        if scientific_config(rel):
            return size <= LIMIT, 'pinned_CPG_reproduction_input' if size <= LIMIT else 'oversized_original'
        if ext == '.json' and size <= LIMIT:
            return True, 'scientific_source_metadata_or_provenance'
        return False, 'original_dataset_download_separately'
    if rel.startswith('references/'):
        return rel == 'references/shiu-source/LICENSE', 'upstream_attribution_notice' if rel == 'references/shiu-source/LICENSE' else 'third_party_source_download_separately'
    if ext in {'.parquet', '.feather', '.arrow', '.bin', '.npy', '.zip', '.h5', '.hdf5', '.pdf', '.xlsx'}:
        return False, 'large_or_external_binary_not_in_source_publication'
    if size > LIMIT:
        return False, 'large_analysis_output_reproduce_or_download'
    if ext in CODE_DOC or rel in {'.gitignore', '.gitattributes', 'LICENSE', 'LICENSE.md', 'LICENSE.txt', 'CITATION.cff'}:
        return True, 'project_code_documentation_or_metadata'
    if rel.startswith('analysis/') and ext in {'.csv', '.tsv', '.npz'}:
        return True, 'bounded_derived_scientific_result'
    return False, 'outside_explicit_publication_scope'


def walk():
    """Skip runtime trees, inventory individual scientific files without reading big data."""
    records = []
    for folder, dirs, files in os.walk(ROOT, followlinks=False):
        base = Path(folder)
        keep = []
        for d in sorted(dirs):
            p = base / d
            rel = p.relative_to(ROOT).as_posix()
            if p == HERE or rel.startswith('analysis/cloud_transfer') or d in SKIP_DIRS or d.startswith('.venv-'):
                # Archive run configuration is a source, despite its logs directory.
                if rel == CPG + 'run33241778/logs':
                    keep.append(d)
                else:
                    records.append({'path': rel + '/', 'included': False, 'reason': 'excluded_directory_tree', 'kind': 'directory'})
            elif p.is_symlink() or getattr(p, 'is_junction', lambda: False)():
                records.append({'path': rel + '/', 'included': False, 'reason': 'directory_link_not_followed', 'kind': 'directory'})
            else:
                keep.append(d)
        dirs[:] = keep
        for name in sorted(files):
            p = base / name
            rel = p.relative_to(ROOT).as_posix()
            if p.is_symlink():
                records.append({'path': rel, 'included': False, 'reason': 'file_link_not_followed'})
                continue
            size = p.stat().st_size
            include, reason = choice(rel, size)
            records.append({'path': rel, 'source_bytes': size, 'included': include, 'reason': reason})
    for name in sorted(BOOTSTRAP):
        p = HERE / name
        if p.exists():
            records.append({'path': p.relative_to(ROOT).as_posix(), 'source_bytes': p.stat().st_size, 'included': True, 'reason': 'publication_method_and_attribution'})
    return sorted(records, key=lambda r:r['path'])


def public_bytes(path):
    original = path.read_bytes()
    transformations = []
    warnings = []
    if path.suffix.lower() not in TEXT:
        return original, original, transformations, warnings
    text = original.decode('utf-8-sig')
    for label, regex in SECRET:
        if regex.search(text):
            raise RuntimeError('Potential secret in included file: ' + path.relative_to(ROOT).as_posix() + ' [' + label + ']')
    if SESSION_URL.search(text):
        # Session identities are not scientific provenance. Never preserve their values in reports.
        text, n = SESSION_URL.subn('<PRIVATE_SESSION_URL_REMOVED>', text)
        transformations.append({'kind': 'remove_private_session_url', 'occurrences': n})
    text, n = PERSONAL_HOME.subn('<USER_HOME>', text)
    if n:
        transformations.append({'kind': 'replace_personal_home_prefix', 'replacement': '<USER_HOME>', 'occurrences': n})
    if path.suffix.lower() == '.html' and path.is_relative_to(ROOT / 'app'):
        for port, preferred, fallback in [
            ('4180', 'docs/publication/README.md', 'analysis/report.md'),
            ('8765', 'docs/publication/SOURCES.md', 'analysis/github_publication/PUBLICATION_NOTES.md'),
        ]:
            target = preferred if (ROOT / preferred).is_file() else fallback
            if not (ROOT / target).is_file():
                raise RuntimeError('Public link target missing: ' + target)
            replacement = 'https://github.com/IT-EXPRESS-Bayern/Fliege/blob/main/' + target
            pattern = re.compile(r'(?<=href=")http://(?:127\.0\.0\.1|localhost):' + port + r'/[^"<>]*')
            text, n = pattern.subn(replacement, text)
            if n:
                transformations.append({'kind': 'replace_local_navigation_link', 'port': port, 'target': target, 'occurrences': n})
    local = sorted(set(LOCAL_URL.findall(text)))
    if local:
        warnings.append({'kind': 'local_service_references', 'count': len(local), 'values': local[:10]})
    published = text.encode('utf-8') if transformations else original
    if path.suffix.lower() == '.json':
        json.loads(published)
    return original, published, transformations, warnings


def build():
    records = walk()
    for r in records:
        if not r['included']:
            continue
        src, pub, changes, warnings = public_bytes(ROOT / r['path'])
        r.update(source_bytes=len(src), source_sha256=sha(src), published_bytes=len(pub), published_sha256=sha(pub), transformations=changes)
        if warnings:
            r['review_notes'] = warnings
    included = [r for r in records if r['included']]
    names = {r['path'] for r in included}
    required = ['app/cpg.html', 'app/data/cpg_replay.json', 'app/data/neuron_assays.json', 'app/vendor/THREE-LICENSE.txt', 'analysis/cpg_reproduction/run.py', 'analysis/neuron_assays/README.md', 'analysis/github_publication/PUBLICATION_NOTES.md']
    missing = [x for x in required if x not in names]
    if missing:
        raise RuntimeError('Required publication artifacts missing: ' + ', '.join(missing))
    inv = {
        'schema': 'fly.github-publication-manifest.v1', 'created_utc': datetime.now(timezone.utc).isoformat(),
        'repository': 'IT-EXPRESS-Bayern/Fliege', 'contains_git_actions': False, 'contains_simulation_actions': False,
        'file_paths': 'project-relative POSIX; included paths form the explicit copy allowlist',
        'limits': {'ordinary_file_bytes': LIMIT, 'app_file_bytes': APP_LIMIT},
        'summary': {'included_files': len(included), 'published_bytes': sum(r['published_bytes'] for r in included),
                    'excluded_entries': len(records)-len(included), 'excluded_reasons': dict(Counter(r['reason'] for r in records if not r['included'])),
                    'transformed_files': sum(bool(r['transformations']) for r in included)},
        'scientific_integrity': 'Source SHA256 and published SHA256 are separate. Personal path/session redactions are explicit; embedded scientific input/output checksums are retained. A derived JSON with redacted provenance has a different publication checksum.',
        'runtime_exclusion': 'Data protected runtime, hosting config and its built distribution are excluded. Only authored report content is included as readable source.',
        'files': records,
    }
    return inv


def stage(inv, target):
    target = target.resolve()
    if target == ROOT or ROOT in target.parents and HERE not in target.parents:
        raise RuntimeError('Publication destination must be a separate checkout or a child of this publication folder')
    target.mkdir(parents=True, exist_ok=True)
    for r in inv['files']:
        if not r['included']:
            continue
        src, pub, changes, _ = public_bytes(ROOT / r['path'])
        if sha(src) != r['source_sha256'] or sha(pub) != r['published_sha256'] or changes != r['transformations']:
            raise RuntimeError('Source changed during staging: ' + r['path'])
        dest = target / r['path']
        if not dest.resolve().is_relative_to(target):
            raise RuntimeError('Destination escaped publication tree: ' + r['path'])
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + '.publication-tmp-' + uuid.uuid4().hex)
        tmp.write_bytes(pub)
        os.replace(tmp, dest)
        if sha(dest.read_bytes()) != r['published_sha256']:
            raise RuntimeError('Staged checksum mismatch: ' + r['path'])
    out = target / 'analysis/github_publication'
    dump(out / 'manifest.json', inv)
    sums = ''.join(r['published_sha256'] + '  ' + r['path'] + '\n' for r in inv['files'] if r['included'])
    (out / 'SHA256SUMS').write_text(sums, encoding='utf-8', newline='\n')
    print(json.dumps({'stage': 'completed', 'files': inv['summary']['included_files'], 'published_bytes': inv['summary']['published_bytes'], 'git_actions': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', action='store_true', help='Generate explicit allowlist/checksums (default)')
    parser.add_argument('--stage', type=Path, help='Copy allowlisted files into a separate publication checkout; no Git actions')
    args = parser.parse_args()
    inv = build()
    dump(HERE / 'manifest.json', inv)
    if args.stage:
        stage(inv, args.stage)
    else:
        print(json.dumps(inv['summary'], indent=2))


if __name__ == '__main__':
    main()
