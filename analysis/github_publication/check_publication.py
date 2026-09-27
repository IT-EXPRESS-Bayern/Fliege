"""Validate a publication checkout without running a scientific simulation."""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import re
import subprocess

def main():
    p = argparse.ArgumentParser()
    p.add_argument('checkout', type=Path)
    p.add_argument('--node', required=True)
    args = p.parse_args()
    root = args.checkout.resolve()
    manifest = json.loads((root / 'analysis/github_publication/manifest.json').read_text(encoding='utf-8'))
    checks = {'files': 0, 'python_syntax': 0, 'javascript_syntax': 0, 'json': 0, 'entry_doc_links': 0}
    errors = []
    for f in manifest['files']:
        if not f['included']:
            continue
        path = root / f['path']
        data = path.read_bytes()
        checks['files'] += 1
        if hashlib.sha256(data).hexdigest() != f['published_sha256']:
            errors.append('hash: ' + f['path'])
        if path.suffix == '.json':
            json.loads(data)
            checks['json'] += 1
        elif path.suffix == '.py':
            ast.parse(data.decode('utf-8-sig'), filename=f['path'])
            checks['python_syntax'] += 1
        elif path.suffix in {'.js', '.mjs'} and f['path'].startswith(('app/', 'brain/')):
            r = subprocess.run([args.node, '--check', str(path)], capture_output=True, text=True)
            checks['javascript_syntax'] += 1
            if r.returncode:
                errors.append('syntax: ' + f['path'] + ': ' + r.stderr[-1000:])
    for rel in ['README.md', 'LICENSES.md', 'CONTRIBUTING.md', 'app/data/README.md']:
        path = root / rel
        text = path.read_text(encoding='utf-8')
        for link in re.findall(r'\]\(([^\s)]+)', text):
            if re.match(r'^(https?:|#|mailto:)', link):
                continue
            target = (path.parent / link.split('#')[0]).resolve()
            checks['entry_doc_links'] += 1
            if not target.exists():
                errors.append('link: ' + rel + ' -> ' + link)
    result = {'checks': checks, 'errors': errors, 'passed': not errors,
              'scientific_simulations_executed': False,
              'scope': 'Publication file hashes, syntax, JSON parsing and entry-document relative links only; no biological or visual validation.'}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
