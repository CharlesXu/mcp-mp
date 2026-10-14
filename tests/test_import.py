import json
import unittest
from scripts.import_workbuddy import normalize


class ImportTests(unittest.TestCase):
    def row(self, **kw):
        return dict(name='sample', zh_name='示例', desc_zh='检索资料', kind='远程 MCP',
                    repo='https://github.com/example/sample', endpoint='', **kw)

    def test_cli_is_not_stdio(self):
        row = self.row(); row['kind'] = '本地 CLI (npm)'
        entry = normalize(row, {'mcpServers': {'x': {'command': 'npx', 'args': ['tool']}}})
        self.assertIsNone(entry['connection'])
        self.assertEqual(entry['availability'], 'not-mcp')

    def test_credentials_are_parameters(self):
        entry = normalize(self.row(), {'mcpServers': {'x': {
            'type': 'streamableHttp', 'url': 'https://example.com/mcp?token=PRIVATE&source=workbuddy',
            'headers': {'Authorization': 'Bearer PRIVATE', 'X-Client-Secret': 'PRIVATE'}}}})
        text = json.dumps(entry)
        self.assertNotIn('PRIVATE', text)
        self.assertIn('${WB_SAMPLE_QUERY_TOKEN}', entry['connection']['url'])
        self.assertEqual(entry['connection']['headers']['Authorization'], '${WB_SAMPLE_HEADER_AUTHORIZATION}')
        self.assertEqual(len(entry['parameters']), 3)

    def test_internal_endpoint_and_repo_hidden(self):
        row = self.row(); row['repo'] = 'https://git.woa.com/team/tool'
        entry = normalize(row, {'mcpServers': {'x': {'type': 'http', 'url': 'https://mcp.woa.com/mcp'}}})
        self.assertIsNone(entry['connection'])
        self.assertEqual(entry['availability'], 'restricted')
        self.assertNotIn('woa.com', json.dumps(entry))

    def test_unknown_transport_not_inferred(self):
        entry = normalize(self.row(), {'mcpServers': {'x': {'url': 'https://example.com/mcp'}}})
        self.assertIsNone(entry['connection'])
        self.assertEqual(entry['availability'], 'needs-review')

    def test_nested_paths_and_personal_status_not_published(self):
        row = self.row(); row.update(local_path='/Users/private/tool', status='已连接', enabled_at='yesterday')
        entry = normalize(row, {'mcpServers': {'x': {'type': 'stdio', 'command': '/Users/private/runner', 'args': []}}})
        text = json.dumps(entry)
        self.assertNotIn('/Users/', text)
        self.assertNotIn('enabled_at', text)
        self.assertIsNone(entry['connection'])

    def test_url_userinfo_redacted(self):
        e = normalize(self.row(), {'mcpServers': {'x': {'type': 'http', 'url': 'https://user:pass@example.com/mcp'}}})
        self.assertIsNone(e['connection'])
        self.assertNotIn('user:pass', json.dumps(e))

    def test_oauth_has_setup_requirement(self):
        row = self.row(); row['auth_mode'] = 'oauth'
        e = normalize(row, {'mcpServers': {'x': {'type': 'http', 'url': 'https://example.com/mcp'}}})
        self.assertIn('oauth', e['auth']['mode'])
        self.assertEqual(e['verification']['protocol'], 'not-tested')

    def test_multiple_servers_need_review(self):
        conf = {'mcpServers': {x: {'type': 'http', 'url': 'https://example.com/mcp'} for x in ['a', 'b']}}
        self.assertIsNone(normalize(self.row(), conf)['connection'])

    def test_internal_domain_in_description_redacted(self):
        row = self.row(); row['desc_zh'] = '连接 tapd.woa.com 的企业服务'
        entry = normalize(row, None)
        self.assertNotIn('.woa.com', json.dumps(entry))
