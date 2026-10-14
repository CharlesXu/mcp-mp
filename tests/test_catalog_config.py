import importlib.util
import json
import tempfile
import tomllib
import unittest
from pathlib import Path
PATH = Path(__file__).resolve().parents[1] / 'scripts/catalog_config.py'
spec = importlib.util.spec_from_file_location('catalog_config', PATH)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

class ConfigTests(unittest.TestCase):
    def test_clone_path_with_spaces_is_not_shell_command(self):
        with tempfile.TemporaryDirectory(prefix='clone with spaces ') as tmp:
            root = Path(tmp)
            for client in ['codex', 'claude', 'cherry']:
                result = mod.catalog_config(root, client)
                if client == 'codex': c = tomllib.loads(result)['mcp_servers']['mcp-mp-catalog']
                else: c = json.loads(result)['mcpServers']['mcp-mp-catalog']
                self.assertEqual(c['command'], 'uv')
                self.assertEqual(Path(c['args'][3]).resolve(), root.resolve() / 'plugins/mcp-mp-catalog')
                self.assertEqual(Path(c['args'][-1]).resolve(), root.resolve() / 'plugins/mcp-mp-catalog/server.py')
                self.assertEqual(len(c['args']), 6)
