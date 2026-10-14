"""Native marketplace smoke in isolated config homes, then SDK tests installed launchers."""
import argparse
import asyncio
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from mcp import Client
from mcp.client.stdio import StdioServerParameters

ROOT = Path(__file__).resolve().parents[1]


def run(command, env, cwd):
    result = subprocess.run(command, env=env, cwd=cwd, text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise RuntimeError('Native smoke command failed: ' + ' '.join(command[:3]))
    return result.stdout


async def smoke(source: str) -> dict:
    results = []
    with tempfile.TemporaryDirectory(prefix='mcp-mp-clients-') as tmp:
        for app, setting in [('codex', 'CODEX_HOME'), ('claude', 'CLAUDE_CONFIG_DIR')]:
            config_home = Path(tmp) / app; config_home.mkdir()
            env = os.environ.copy()
            # These are each client's documented config-directory overrides, never scratch variables.
            env[setting] = str(config_home)
            version = run([app, '--version'], env, tmp).strip()
            run([app, 'plugin', 'marketplace', 'add', source], env, tmp)
            install = run([app, 'plugin', 'add' if app == 'codex' else 'install', 'mcp-mp-catalog@mcp-mp'] +
                          (['--json'] if app == 'codex' else []), env, tmp)
            listing = json.loads(run([app, 'plugin', 'list', '--json'], env, tmp))
            if app == 'codex':
                listed = listing['installed']
                path = Path(json.loads(install)['installedPath'])
                server = json.loads((path / 'codex.mcp.json').read_text())['mcpServers']['mcp-mp-catalog']
                cwd = str(path)
            else:
                listed = listing
                path = Path(next(e['installPath'] for e in listed if e['id'] == 'mcp-mp-catalog@mcp-mp'))
                server = json.loads((path / '.mcp.json').read_text())['mcpServers']['mcp-mp-catalog']
                cwd = tmp
            if not any(e.get('enabled') and e.get('pluginId', e.get('id')) == 'mcp-mp-catalog@mcp-mp' for e in listed):
                raise RuntimeError('Installed plugin not enabled in readback')
            args = [a.replace('${CLAUDE_PLUGIN_ROOT}', str(path)) for a in server['args']]
            async with Client(StdioServerParameters(command=server['command'], args=args, cwd=cwd), read_timeout_seconds=30) as client:
                tools = await client.list_tools()
                found = {t.name for t in tools.tools}
                if found != {'catalog_search', 'catalog_get', 'catalog_export'}: raise RuntimeError('Tool discovery mismatch')
                result = await client.call_tool('catalog_search', {'query': '飞书'})
                if result.is_error or not any(e['id'] == 'workbuddy/feishu' for e in result.structured_content['entries']):
                    raise RuntimeError('Installed plugin search failed')
                results.append({'client': app, 'version': version, 'marketplace_discovery': 'passed',
                                'plugin_install_readback': 'passed', 'installed_launcher_sdk_handshake': 'passed',
                                'installed_search': 'passed', 'protocol_version': client.protocol_version,
                                'scope': 'native CLI install plus SDK transport; no model session or business tool invocation'})
            print(app + ': native marketplace install, readback, installed launcher and search passed')
    return {'checked_at': datetime.now(timezone.utc).isoformat(), 'source': 'github' if source == 'CharlesXu/mcp-mp' else 'local',
            'checks': results, 'cherry': {'status': 'configuration-only', 'desktop_ui': 'not-tested'}}


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--source', default=str(ROOT))
    p.add_argument('--output', type=Path, default=ROOT / 'reports/client-smoke.json')
    a = p.parse_args()
    report = asyncio.run(smoke(a.source))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
