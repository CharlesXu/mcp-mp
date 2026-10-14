"""Explicit, credential-free remote protocol probe. Never calls business tools."""
import argparse
import asyncio
import ipaddress
import json
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
import anyio
import httpx2 as httpx
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mcp.client.sse import sse_client

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ''): sys.path.insert(0, str(ROOT))
from scripts.import_workbuddy import restricted_url


class ProbePolicyError(ValueError):
    """A local safety policy prevented the request; not evidence of service failure."""


def check_public_url(url: str) -> None:
    if restricted_url(url): raise ProbePolicyError('Non-public target')
    u = urlsplit(url)
    addresses = socket.getaddrinfo(u.hostname, u.port or 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ProbePolicyError('Target DNS is not public')


async def public_request(request):
    await asyncio.to_thread(check_public_url, str(request.url))


def make_http_client(**kwargs):
    return httpx.AsyncClient(**kwargs)


def leaf_errors(exc):
    if isinstance(exc, BaseExceptionGroup):
        for child in exc.exceptions: yield from leaf_errors(child)
    else: yield exc


async def probe(entry: dict, timeout_seconds: float = 15) -> dict:
    connection = entry.get('connection') or {}
    result = {'id': entry['id'], 'checked_at': datetime.now(timezone.utc).isoformat(),
              'transport': connection.get('transport'), 'protocol': 'skipped', 'initialize': 'not-tested',
              'tools_list': 'not-tested', 'tool_count': None, 'business': 'not-tested', 'error_category': None}
    if entry.get('availability') != 'candidate' or not connection or entry.get('parameters') or connection.get('transport') == 'stdio':
        result['error_category'] = 'not-public-credential-free-remote-recipe'; return result
    observed_statuses = []
    async def observe_response(response):
        observed_statuses.append(response.status_code)
    try:
        with anyio.fail_after(timeout_seconds):
            await asyncio.to_thread(check_public_url, connection['url'])
            headers = connection.get('headers', {})
            # No automatic redirects or OAuth. Hooks also check any URL the SSE server advertises.
            options = {'headers': headers, 'timeout': timeout_seconds, 'follow_redirects': False,
                       'event_hooks': {'request': [public_request], 'response': [observe_response]}}
            async with make_http_client(**options) as http_client:
                if connection['transport'] == 'streamable-http':
                    transport = streamable_http_client(connection['url'], http_client=http_client)
                elif connection['transport'] == 'sse':
                    def factory(headers=None, timeout=None, auth=None, **kwargs):
                        return make_http_client(headers=headers or {}, timeout=timeout or timeout_seconds,
                                                follow_redirects=False, event_hooks={'request': [public_request], 'response': [observe_response]})
                    transport = sse_client(connection['url'], headers=headers, timeout=timeout_seconds,
                                           sse_read_timeout=timeout_seconds, httpx_client_factory=factory)
                else:
                    raise ValueError('Unknown transport')
                # Legacy mode specifically exercises initialize rather than treating discovery as a handshake.
                async with Client(transport, mode='legacy', read_timeout_seconds=timeout_seconds) as client:
                    result['initialize'] = 'passed'
                    count, cursor, seen = 0, None, set()
                    for _ in range(100):
                        listing = await client.list_tools(cursor=cursor, cache_mode='refresh')
                        count += len(listing.tools)
                        cursor = listing.next_cursor
                        if not cursor: break
                        if cursor in seen: raise ValueError('Repeated tools cursor')
                        seen.add(cursor)
                    else: raise ValueError('Tools pagination bound exceeded')
                    result.update(protocol='passed', tools_list='passed', tool_count=count)
    except Exception as exc:
        leaves = list(leaf_errors(exc))
        statuses = observed_statuses + [e.response.status_code for e in leaves if isinstance(e, httpx.HTTPStatusError)]
        timeout = any(isinstance(e, (TimeoutError, httpx.TimeoutException)) for e in leaves)
        blocked = any(isinstance(e, ProbePolicyError) for e in leaves)
        result['protocol'] = 'skipped' if blocked else ('needs-auth' if any(s in (401, 403) for s in statuses) else 'failed')
        result['error_category'] = 'network-policy-blocked' if blocked else ('authentication-required' if result['protocol'] == 'needs-auth' else ('timeout' if timeout else 'protocol-or-network-error'))
        # Do not expose response bodies, headers, exception messages, or tool definitions.
    return result


async def main():
    p = argparse.ArgumentParser(); p.add_argument('ids', nargs='+'); p.add_argument('--timeout', type=int, default=15)
    p.add_argument('--output', type=Path, default=ROOT / 'reports/verification.json')
    a = p.parse_args()
    if not 1 <= a.timeout <= 60: p.error('--timeout must be 1–60 seconds')
    entries = {e['id']: e for e in json.loads((ROOT / 'plugins/mcp-mp-catalog/catalog.json').read_text())}
    if any(id not in entries for id in a.ids): p.error('Unknown catalogue ID')
    gate = asyncio.Semaphore(4)
    async def selected(id):
        async with gate: return await probe(entries[id], a.timeout)
    checks = await asyncio.gather(*(selected(id) for id in a.ids))
    existing = json.loads(a.output.read_text()).get('checks', []) if a.output.exists() else []
    by_id = {c['id']: c for c in existing}
    for check in checks:
        if check['id'] in by_id:
            history = by_id[check['id']].get('history', []) + [{k: v for k, v in by_id[check['id']].items() if k != 'history'}]
            check['history'] = history
        by_id[check['id']] = check
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps({'scope': 'credential-free protocol only; no business tools called',
                                  'checks': sorted(by_id.values(), key=lambda c: c['id'])}, indent=2) + '\n')
    for check in checks: print(check['id'], check['protocol'], check['error_category'] or '', 'tools=', check['tool_count'])


if __name__ == '__main__':
    asyncio.run(main())
