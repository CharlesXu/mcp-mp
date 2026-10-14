import copy
import json
import tempfile
import unittest
from pathlib import Path
from scripts.build import build
from scripts.validate import validate
from scripts.import_workbuddy import normalize

ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'schemas').mkdir()
        (self.root / 'schemas/entry.schema.json').write_bytes((ROOT / 'schemas/entry.schema.json').read_bytes())
        (self.root / 'workbuddy').mkdir()
        self.entry = normalize({'name': 'sample', 'zh_name': '示例', 'kind': '远程 MCP'},
                               {'mcpServers': {'x': {'type': 'http', 'url': 'https://example.com/mcp'}}})
        self.save([self.entry])

    def save(self, entries):
        (self.root / 'harnesses.json').write_text(json.dumps({'harnesses': [{'id': 'workbuddy', 'path': 'workbuddy/catalog.json', 'expected_count': len(entries)}]}))
        (self.root / 'workbuddy/catalog.json').write_text(json.dumps(entries))

    def test_deterministic_build_and_matching_references(self):
        build(self.root)
        self.assertEqual(validate(self.root), [])
        before = (self.root / 'catalog/index.json').read_bytes()
        build(self.root)
        self.assertEqual(before, (self.root / 'catalog/index.json').read_bytes())
        (self.root / 'workbuddy/entries/sample/entry.json').unlink()
        self.assertTrue(validate(self.root))

    def test_duplicate_id_rejected(self):
        self.save([self.entry, self.entry])
        with self.assertRaises(ValueError): build(self.root)

    def test_path_traversal_rejected(self):
        self.entry['slug'] = '../escape'; self.save([self.entry])
        with self.assertRaises(ValueError): build(self.root)

    def test_credentials_and_undeclared_parameters_rejected(self):
        self.entry['connection']['url'] += '?token=PRIVATE'
        self.save([self.entry]); build(self.root)
        self.assertTrue(validate(self.root))
        self.entry['connection']['url'] = 'https://example.com/mcp?token=${UNKNOWN}'
        self.save([self.entry]); build(self.root)
        self.assertTrue(validate(self.root))

    def test_add_second_harness(self):
        other = copy.deepcopy(self.entry); other.update(id='other/sample', harness='other')
        (self.root / 'other').mkdir(); (self.root / 'other/catalog.json').write_text(json.dumps([other]))
        config = json.loads((self.root / 'harnesses.json').read_text())
        config['harnesses'].append({'id': 'other', 'path': 'other/catalog.json', 'expected_count': 1})
        (self.root / 'harnesses.json').write_text(json.dumps(config))
        build(self.root)
        self.assertEqual(validate(self.root), [])
        self.assertEqual(json.loads((self.root / 'catalog/index.json').read_text())['count'], 2)
