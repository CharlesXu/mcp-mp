"""Export a selected recipe, never install it or expand credentials."""
import json
import re

VARIABLE = re.compile(r'\$\{([A-Z][A-Z0-9_]*)\}')


def export_entry(entry: dict, client: str, allow_candidate: bool = False) -> str:
    if client not in {'codex', 'claude', 'cherry'}:
        raise ValueError('client 必须是 codex、claude 或 cherry。')
    connection = entry.get('connection')
    if entry.get('availability') != 'candidate' or not connection:
        raise ValueError('该条目没有可导出的 MCP 配方；请查看 availability 和 reason。')
    if not allow_candidate and entry['verification']['protocol'] != 'passed':
        raise ValueError('候选配方未验证，需明确 allow_candidate=true；输出只是模板。')
    name = entry['id'].replace('/', '-')
    if not re.fullmatch(r'[a-z0-9-]+', name):
        raise ValueError('Invalid server name')
    transport = connection['transport']
    if transport not in {'stdio', 'streamable-http', 'sse'}:
        raise ValueError('未知 MCP 传输协议。')
    config = {k: v for k, v in connection.items() if k != 'transport'}
    if client != 'codex':
        config['type'] = ('http' if client == 'claude' else 'streamableHttp') if transport == 'streamable-http' else transport
        return json.dumps({'mcpServers': {name: config}}, ensure_ascii=False, indent=2) + '\n'
    if transport == 'sse':
        raise ValueError('Codex 不直接导出旧式 SSE；请向服务商获取 Streamable HTTP 配方。')
    if transport != 'stdio' and VARIABLE.search(config['url']):
        raise ValueError('Codex URL 不展开此类占位符；需先独立配置完整 URL，不能直接导入此模板。')
    quote = lambda value: json.dumps(value, ensure_ascii=False)
    lines = ['# MCP 配置模板；协议/认证通过不等于业务调用验证。', f'[mcp_servers.{quote(name)}]']
    if transport == 'stdio':
        if VARIABLE.search(json.dumps(config)):
            raise ValueError('Codex stdio 配方含未解析占位符，不能直接导入。')
        lines += [f'command = {quote(config["command"])}', 'args = ' + quote(config.get('args', []))]
        if config.get('env'):
            lines.append(f'[mcp_servers.{quote(name)}.env]')
            lines += [f'{quote(k)} = {quote(v)}' for k, v in config['env'].items()]
    else:
        lines.append(f'url = {quote(config["url"])}')
        static, dynamic = {}, {}
        for key, value in config.get('headers', {}).items():
            match = VARIABLE.fullmatch(value)
            if match: dynamic[key] = match.group(1)
            elif VARIABLE.search(value): raise ValueError('动态认证头必须引用完整环境变量值。')
            else: static[key] = value
        for table, values in [('http_headers', static), ('env_http_headers', dynamic)]:
            if values:
                lines.append(f'[mcp_servers.{quote(name)}.{table}]')
                lines += [f'{quote(k)} = {quote(v)}' for k, v in values.items()]
    return '\n'.join(lines) + '\n'
