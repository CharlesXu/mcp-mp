"""Import a private inventory as public, parameterized catalogue metadata."""
import argparse
import hashlib
import ipaddress
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRANSPORTS = {'streamableHttp': 'streamable-http', 'streamable-http': 'streamable-http',
              'http': 'streamable-http', 'sse': 'sse', 'stdio': 'stdio'}
PRIVATE_SUFFIXES = ('.woa.com', '.ihr360.com', '.intsig.net', '.ninebot.com', '.local', '.internal', '.corp')
BENIGN_QUERY = {'source', 'format', 'includeTools'}
BENIGN_HEADERS = {'accept', 'content-type', 'x-skill-version'}


def restricted_url(value: str) -> bool:
    try:
        u = urlsplit(value)
        host = (u.hostname or '').lower()
        if not host or u.scheme != 'https' or u.username or u.password:
            return True
        if host == 'localhost' or host.endswith(PRIVATE_SUFFIXES) or '.' not in host:
            return True
        try:
            return not ipaddress.ip_address(host).is_global
        except ValueError:
            return False
    except ValueError:
        return True


def public_repo(value: str) -> str | None:
    if not value or restricted_url(value):
        return None
    # A repository address is evidence of a location, not a verified license or source equivalence.
    if urlsplit(value).hostname not in {'github.com', 'cnb.cool', 'codeup.aliyun.com'}:
        return None
    return value.split('?')[0].split('#')[0]


def normalize(row: dict, definition: dict | None) -> dict:
    slug = row['name']
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
        raise ValueError('Invalid connector slug')
    prefix = 'WB_' + slug.upper().replace('-', '_')
    parameters = []

    def parameter(location: str, key: str, hint: str = '') -> str:
        name = prefix + '_' + location.upper() + '_' + re.sub(r'[^A-Z0-9]', '_', key.upper())
        if not any(p['name'] == name for p in parameters):
            parameters.append({'name': name, 'location': location, 'key': key, 'required': True,
                               'description': hint or '从服务商独立获取并填写；不复用 WorkBuddy 私有凭据。'})
        return '${' + name + '}'

    description = str(row.get('desc_zh') or row.get('zh_name') or slug)
    description = re.sub(r'https?://\S+|/Users/\S+|/home/\S+', '', description)
    description = re.sub(r'[A-Za-z0-9._-]+(?:\.woa\.com|\.ihr360\.com|\.intsig\.net|\.ninebot\.com)', '受限来源', description)
    description = re.split(r'[。\n]', description)[0][:72].strip()
    entry = {'id': 'workbuddy/' + slug, 'slug': slug, 'harness': 'workbuddy',
             'name': row.get('zh_name') or slug, 'description': description or slug,
             'kind': row.get('kind', 'unknown'),
             'source_repository': public_repo(row.get('repo', '')),
             'source_status': 'reported-not-independently-verified',
             'provenance': {'source': 'workbuddy-connector-inventory', 'snapshot_date': '2026-10-14',
                            'definition': 'marketplace-mcp-json' if definition else 'inventory-only'},
             'connection': None, 'parameters': parameters,
             'auth': {'mode': row.get('auth_mode') or 'unknown',
                      'instructions': '需查阅服务商文档，独立申请凭据或完成 OAuth；未验证跨客户端授权。'},
             'availability': 'needs-review', 'reason': '缺少可移植 MCP 配方或明确的传输协议。',
             'verification': {'structure': 'pending', 'protocol': 'not-tested', 'business': 'not-tested'}}
    endpoint = row.get('endpoint', '')
    if endpoint and restricted_url(endpoint):
        entry.update(availability='restricted', reason='本机、内网、非公开或含 URL 身份信息的来源。')
        entry['source_repository'] = None
        return entry
    if row.get('kind') != '远程 MCP':
        entry.update(availability='not-mcp', reason='原清单标为 CLI 或 Skill；未证实其提供 MCP 协议。')
        return entry
    servers = (definition or {}).get('mcpServers', {})
    if len(servers) != 1:
        return entry
    config = next(iter(servers.values()))
    transport = TRANSPORTS.get(config.get('type'))
    if not transport:
        return entry
    if transport == 'stdio':
        # Do not republish or execute harness-specific launchers or ambiguous install recipes.
        entry['reason'] = '本地 MCP 启动配置需独立审核包版本和启动命令。'
        return entry
    url = config.get('url', '')
    if restricted_url(url):
        entry.update(availability='restricted', reason='本机、内网、非公开或含 URL 身份信息的来源。')
        entry['source_repository'] = None
        return entry
    u = urlsplit(url)
    query = [(k, v if k in BENIGN_QUERY and not re.search(r'\{\{|\$\{', v)
              else parameter('query', k)) for k, v in parse_qsl(u.query, keep_blank_values=True)]
    safe_url = urlunsplit((u.scheme, u.netloc, u.path, urlencode(query, safe='${}'), ''))
    headers = {}
    for key, value in {**config.get('staticHeaders', {}), **config.get('headers', {})}.items():
        if key.lower() in BENIGN_HEADERS and isinstance(value, str) and not re.search(r'\{\{|\$\{', value):
            headers[key] = value
        else:
            hint = '填写完整 Authorization 头值，包含 Bearer 前缀（若服务商要求）。' if key.lower() == 'authorization' else ''
            headers[key] = parameter('header', key, hint)
    entry['connection'] = {'transport': transport, 'url': safe_url, 'headers': headers}
    entry.update(availability='candidate', reason='来源配置已归一化；须独立验证协议、认证和客户端兼容性。')
    if parameters:
        entry['auth']['mode'] = 'parameters-required'
    return entry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('inventory', type=Path)
    parser.add_argument('--definitions', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=Path('workbuddy/catalog.json'))
    args = parser.parse_args()
    raw = args.inventory.read_bytes()
    rows = json.loads(raw)
    entries = []
    for row in rows:
        path = args.definitions / row['name'] / 'mcp.json'
        definition = json.loads(path.read_text()) if path.is_file() else None
        entry = normalize(row, definition)
        entry['provenance']['inventory_sha256'] = hashlib.sha256(raw).hexdigest()
        entries.append(entry)
    if len(entries) != 278 or len({e['id'] for e in entries}) != 278:
        raise ValueError('Expected 278 unique records from the approved snapshot')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(sorted(entries, key=lambda e: e['id']), ensure_ascii=False, indent=2) + '\n')
    from collections import Counter
    print('Imported:', len(entries), 'Availability:', dict(Counter(e['availability'] for e in entries)))


if __name__ == '__main__':
    main()
