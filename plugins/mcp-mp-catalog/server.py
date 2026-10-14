"""Read-only marketplace MCP. Discovery and templates, no downstream proxy."""
import json
from pathlib import Path
from typing import Any
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from adapter import export_entry

HERE = Path(__file__).resolve().parent
ENTRIES = json.loads((HERE / 'catalog.json').read_text())
BY_ID = {entry['id']: entry for entry in ENTRIES}
checks_path = HERE / 'verification.json'
CHECKS = {c['id']: c for c in json.loads(checks_path.read_text()).get('checks', [])} if checks_path.exists() else {}
READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
mcp = MCPServer('mcp-mp-catalog', instructions=(
    'Search entries before recommending installation. Imported MCP recipes are candidates, not verified business tools. '
    'Read parameters, auth, availability, latest_protocol_check and reason. Do not install all entries. '
    'Never treat a CLI or Skill as MCP. This server only returns metadata/configuration, never proxies tools.'))


@mcp.tool(annotations=READ_ONLY, structured_output=True)
def catalog_search(query: str, harness: str = '', limit: int = 20, offset: int = 0) -> dict[str, Any]:
    """搜索 MCP/CLI/Skill 目录；分页返回摘要，不连接下游服务。"""
    if not 1 <= limit <= 100 or offset < 0 or len(query) > 500:
        raise ToolError('limit 应为 1–100，offset 非负，query 不超过 500 字符。')
    words = query.casefold().split()
    matches = [e for e in ENTRIES if (not harness or e['harness'] == harness) and
               all(word in (e['id'] + ' ' + e['name'] + ' ' + e['description']).casefold() for word in words)]
    fields = ['id', 'name', 'description', 'availability', 'kind']
    return {'total': len(matches), 'offset': offset, 'limit': limit,
            'entries': [{k: e[k] for k in fields} for e in matches[offset:offset + limit]]}


@mcp.tool(annotations=READ_ONLY, structured_output=True)
def catalog_get(id: str) -> dict[str, Any]:
    """查看来源、连接配方、所需参数和验证边界；ID 是 harness/slug。"""
    if id not in BY_ID:
        raise ToolError('没有此条目；请先 catalog_search。')
    result = dict(BY_ID[id])
    result['latest_protocol_check'] = CHECKS.get(id)
    return result


@mcp.tool(annotations=READ_ONLY, structured_output=True)
def catalog_export(id: str, client: str, allow_candidate: bool = False) -> dict[str, Any]:
    """导出 codex/claude/cherry 配置模板；不填凭据、不执行命令、不安装。"""
    entry = catalog_get(id)
    try:
        config = export_entry(entry, client, allow_candidate)
    except ValueError as exc:
        raise ToolError(str(exc)) from None
    return {'id': id, 'client': client, 'config': config, 'parameters': entry['parameters'],
            'notice': '候选配置模板。独立申请认证并验证；Cherry 需手动替换占位符后导入。',
            'latest_protocol_check': entry['latest_protocol_check']}


if __name__ == '__main__':
    mcp.run(transport='stdio')
