"""Print one selected client recipe. Does not write client configuration."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'plugins/mcp-mp-catalog'))
from adapter import export_entry

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('id'); p.add_argument('--client', required=True, choices=['codex', 'claude', 'cherry'])
    p.add_argument('--allow-candidate', action='store_true')
    a = p.parse_args()
    entries = {e['id']: e for e in json.loads((ROOT / 'plugins/mcp-mp-catalog/catalog.json').read_text())}
    try:
        e = entries[a.id]
        print(export_entry(e, a.client, a.allow_candidate), end='')
        print('Template only. Required parameters: ' + ', '.join(p['name'] for p in e['parameters']), file=sys.stderr)
    except (KeyError, ValueError) as exc:
        p.exit(2, 'Export refused: ' + ('Unknown ID' if isinstance(exc, KeyError) else str(exc)) + '\n')
