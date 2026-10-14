"""Deterministically build individual records and a self-contained plugin catalogue."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def encode(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def collect(root: Path) -> list[dict]:
    entries, seen = [], set()
    for harness in json.loads((root / 'harnesses.json').read_text())['harnesses']:
        name = harness['id']
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
            raise ValueError('Invalid harness ID')
        path = (root / harness['path']).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError('Source path escapes repository')
        rows = json.loads(path.read_text())
        if len(rows) != harness['expected_count']:
            raise ValueError('Snapshot count mismatch: ' + name)
        for entry in rows:
            slug = entry['slug']
            if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
                raise ValueError('Invalid slug')
            if entry['id'] != f'{name}/{slug}' or entry['harness'] != name or entry['id'] in seen:
                raise ValueError('Duplicate or inconsistent ID')
            seen.add(entry['id']); entries.append(entry)
    return sorted(entries, key=lambda entry: entry['id'])


def outputs(root: Path) -> dict[Path, str]:
    entries = collect(root)
    result = {}
    for entry in entries:
        result[root / entry['harness'] / 'entries' / entry['slug'] / 'entry.json'] = encode(entry)
    index = {'schema_version': 1, 'count': len(entries), 'entries': [
        {'id': e['id'], 'name': e['name'], 'availability': e['availability'],
         'path': f"{e['harness']}/entries/{e['slug']}/entry.json"} for e in entries]}
    result[root / 'catalog/index.json'] = encode(index)
    result[root / 'plugins/mcp-mp-catalog/catalog.json'] = encode(entries)
    report = root / 'reports/verification.json'
    result[root / 'plugins/mcp-mp-catalog/verification.json'] = encode(json.loads(report.read_text()) if report.exists() else {'checks': []})
    return result


def build(root: Path, check: bool = False) -> None:
    for path, content in outputs(root).items():
        if check:
            if not path.is_file() or path.read_text() != content:
                raise ValueError('Generated output is stale: ' + str(path.relative_to(root)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    # Reject obsolete individual records rather than silently leaving them in the public tree.
    expected = set(outputs(root))
    for harness in json.loads((root / 'harnesses.json').read_text())['harnesses']:
        for path in (root / harness['id'] / 'entries').glob('*/entry.json'):
            if path not in expected:
                raise ValueError('Obsolete entry must be explicitly removed: ' + str(path.relative_to(root)))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--check', action='store_true')
    a = p.parse_args(); build(ROOT, a.check)
    print('Build consistency passed' if a.check else 'Built catalogue and plugin data')
