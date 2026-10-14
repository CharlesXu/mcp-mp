"""Publication checks; a pass here does not establish live MCP availability."""
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit
import sys
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jsonschema import Draft202012Validator
from scripts.build import ROOT, build, collect
from scripts.import_workbuddy import BENIGN_QUERY, restricted_url

PLACEHOLDER = re.compile(r'\$\{([A-Z][A-Z0-9_]*)\}')


def validate(root: Path) -> list[str]:
    errors = []
    try:
        entries = collect(root)
        schema = json.loads((root / 'schemas/entry.schema.json').read_text())
        validator = Draft202012Validator(schema)
        for entry in entries:
            label = entry['id']
            errors += [label + ': schema ' + error.message for error in validator.iter_errors(entry)]
            text = json.dumps(entry, ensure_ascii=False)
            if re.search(r'/Users/|/home/|\.woa\.com|BEGIN .*PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{20,}', text):
                errors.append(label + ': private data detected')
            connection = entry['connection']
            if connection:
                if entry['availability'] != 'candidate':
                    errors.append(label + ': connection on non-candidate entry')
                if connection['transport'] != 'stdio':
                    if restricted_url(connection['url']): errors.append(label + ': non-public endpoint')
                    for key, value in parse_qsl(urlsplit(connection['url']).query, keep_blank_values=True):
                        if key not in BENIGN_QUERY and not PLACEHOLDER.fullmatch(value):
                            errors.append(label + ': unparameterized query value')
                refs = set(PLACEHOLDER.findall(json.dumps(connection)))
                declared = [p['name'] for p in entry['parameters']]
                if refs != set(declared) or len(declared) != len(set(declared)):
                    errors.append(label + ': parameter declaration mismatch')
                if '{{' in json.dumps(connection): errors.append(label + ': harness-only placeholder')
                for key, value in connection.get('headers', {}).items():
                    if key.lower() not in {'accept', 'content-type', 'x-skill-version'} and not PLACEHOLDER.fullmatch(value):
                        errors.append(label + ': unparameterized header')
            if entry['availability'] == 'restricted' and (connection or entry['source_repository']):
                errors.append(label + ': restricted source has configuration or repository')
        build(root, check=True)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        errors.append('Catalogue consistency error: ' + type(exc).__name__)
    return errors


if __name__ == '__main__':
    import sys
    # Supports both `python -m scripts.validate` and `python scripts/validate.py` through wrapper path.
    result = validate(ROOT)
    print('\n'.join(result) if result else 'Publication structure checks passed')
    sys.exit(bool(result))
