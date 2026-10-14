import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from mcp import Client
from mcp.client.stdio import StdioServerParameters

PLUGIN = Path(__file__).resolve().parents[1] / 'plugins/mcp-mp-catalog'


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_stdio_search_get_export_and_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'plugin'
            shutil.copytree(PLUGIN, target, ignore=shutil.ignore_patterns('.venv', '__pycache__'))
            params = StdioServerParameters(command=sys.executable, args=[str(target / 'server.py')], cwd=tmp)
            async with Client(params, read_timeout_seconds=10) as client:
                tools = await client.list_tools()
                self.assertEqual({t.name for t in tools.tools}, {'catalog_search', 'catalog_get', 'catalog_export'})
                result = await client.call_tool('catalog_search', {'query': '飞书'})
                self.assertFalse(result.is_error)
                data = result.structured_content
                self.assertIn('workbuddy/feishu', [e['id'] for e in data['entries']])
                result = await client.call_tool('catalog_get', {'id': 'workbuddy/feishu'})
                self.assertEqual(result.structured_content['availability'], 'not-mcp')
                result = await client.call_tool('catalog_export', {'id': 'workbuddy/baidu-netdisk', 'client': 'claude', 'allow_candidate': True})
                self.assertEqual(json.loads(result.structured_content['config'])['mcpServers']['workbuddy-baidu-netdisk']['type'], 'sse')
                for tool, args in [('catalog_get', {'id': '../escape'}), ('catalog_search', {'query': '', 'limit': 0}),
                                   ('catalog_export', {'id': 'workbuddy/baidu-netdisk', 'client': 'invalid', 'allow_candidate': True})]:
                    self.assertTrue((await client.call_tool(tool, args)).is_error)

    async def test_pagination_preserves_all_entries(self):
        params = StdioServerParameters(command=sys.executable, args=[str(PLUGIN / 'server.py')])
        async with Client(params, read_timeout_seconds=10) as client:
            ids = []
            for offset in range(0, 278, 100):
                result = await client.call_tool('catalog_search', {'query': '', 'limit': 100, 'offset': offset})
                ids += [e['id'] for e in result.structured_content['entries']]
            self.assertEqual(len(ids), 278)
            self.assertEqual(len(set(ids)), 278)
