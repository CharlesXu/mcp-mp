import importlib.util
import json
import tomllib
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / 'plugins/mcp-mp-catalog/adapter.py'
spec = importlib.util.spec_from_file_location('adapter', PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
export_entry = module.export_entry


def entry(transport='streamable-http'):
    return {'id': 'workbuddy/sample', 'slug': 'sample', 'harness': 'workbuddy', 'availability': 'candidate',
            'verification': {'protocol': 'not-tested'}, 'parameters': [],
            'connection': {'transport': transport, 'url': 'https://example.com/mcp', 'headers': {}}}


class AdapterTests(unittest.TestCase):
    def test_candidate_requires_opt_in(self):
        with self.assertRaises(ValueError): export_entry(entry(), 'claude')

    def test_json_types_match_clients(self):
        for client, transport, expected in [('claude', 'streamable-http', 'http'),
                                             ('cherry', 'streamable-http', 'streamableHttp'),
                                             ('claude', 'sse', 'sse'), ('cherry', 'sse', 'sse')]:
            c = json.loads(export_entry(entry(transport), client, True))['mcpServers']['workbuddy-sample']
            self.assertEqual(c['type'], expected)
            self.assertEqual(c['url'], 'https://example.com/mcp')

    def test_codex_toml_and_environment_headers(self):
        e = entry(); e['connection']['headers'] = {'Authorization': '${WB_SAMPLE_HEADER_AUTHORIZATION}'}
        c = tomllib.loads(export_entry(e, 'codex', True))['mcp_servers']['workbuddy-sample']
        self.assertEqual(c['env_http_headers'], {'Authorization': 'WB_SAMPLE_HEADER_AUTHORIZATION'})
        self.assertEqual(c['url'], 'https://example.com/mcp')

    def test_codex_sse_and_dynamic_url_refused(self):
        with self.assertRaises(ValueError): export_entry(entry('sse'), 'codex', True)
        e = entry(); e['connection']['url'] += '?token=${WB_TOKEN}'
        with self.assertRaises(ValueError): export_entry(e, 'codex', True)

    def test_non_mcp_unknown_and_restricted_refused(self):
        for availability in ['not-mcp', 'restricted', 'needs-review']:
            e = entry(); e['availability'] = availability; e['connection'] = None
            with self.assertRaises(ValueError): export_entry(e, 'claude', True)
        with self.assertRaises(ValueError): export_entry(entry(), 'unknown', True)

    def test_stdio_and_quoting(self):
        e = entry(); e['connection'] = {'transport': 'stdio', 'command': 'python3',
                                      'args': ['path with spaces/server.py'], 'env': {'NAME': 'value"\\x'}}
        for client in ['codex', 'claude', 'cherry']:
            text = export_entry(e, client, True)
            if client == 'codex': c = tomllib.loads(text)['mcp_servers']['workbuddy-sample']
            else: c = json.loads(text)['mcpServers']['workbuddy-sample']
            self.assertEqual(c['args'], ['path with spaces/server.py'])
            self.assertEqual(c['env']['NAME'], 'value"\\x')
