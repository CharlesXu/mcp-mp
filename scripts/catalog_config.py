"""Generate a local clone's catalog MCP configuration without modifying a client."""
import argparse
import json
from pathlib import Path


def catalog_config(root: Path, client: str) -> str:
    plugin = root.resolve() / 'plugins/mcp-mp-catalog'
    args = ['run', '--frozen', '--directory', str(plugin), 'python', str(plugin / 'server.py')]
    if client == 'codex':
        return '[mcp_servers."mcp-mp-catalog"]\ncommand = "uv"\nargs = ' + json.dumps(args, ensure_ascii=False) + '\n'
    if client not in {'claude', 'cherry'}: raise ValueError('Unknown client')
    return json.dumps({'mcpServers': {'mcp-mp-catalog': {'type': 'stdio', 'command': 'uv', 'args': args}}}, ensure_ascii=False, indent=2) + '\n'


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--client', choices=['codex', 'claude', 'cherry'], required=True)
    a = p.parse_args(); print(catalog_config(Path(__file__).resolve().parents[1], a.client), end='')
