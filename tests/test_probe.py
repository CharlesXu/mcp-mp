import json
import unittest
from unittest.mock import patch
import httpx2 as httpx
from scripts.probe import probe, check_public_url


def entry():
    return {'id': 'workbuddy/example', 'availability': 'candidate', 'parameters': [],
            'connection': {'transport': 'streamable-http', 'url': 'https://example.com/mcp', 'headers': {}}}


class ProbeTests(unittest.IsolatedAsyncioTestCase):
    async def simulate(self, handler, timeout=1):
        def factory(**kwargs): return httpx.AsyncClient(transport=httpx.MockTransport(handler), **kwargs)
        with patch('scripts.probe.check_public_url', return_value=None), patch('scripts.probe.make_http_client', factory):
            return await probe(entry(), timeout)

    async def test_html_200_not_protocol_success(self):
        r = await self.simulate(lambda req: httpx.Response(200, text='PRIVATE', headers={'content-type': 'text/html'}))
        self.assertEqual(r['protocol'], 'failed')
        self.assertNotIn('PRIVATE', json.dumps(r))

    async def test_401_needs_auth_without_credentials(self):
        r = await self.simulate(lambda req: httpx.Response(401, text='PRIVATE'))
        self.assertEqual(r['protocol'], 'needs-auth')
        self.assertNotIn('PRIVATE', json.dumps(r))

    async def test_timeout_is_bounded(self):
        async def handler(req):
            import asyncio
            await asyncio.sleep(1)
            return httpx.Response(200)
        r = await self.simulate(handler, timeout=0.05)
        self.assertEqual(r['error_category'], 'timeout')

    async def test_paginated_tools_list(self):
        def handler(req):
            if req.method != 'POST': return httpx.Response(405)
            data = json.loads(req.content)
            if 'id' not in data: return httpx.Response(202)
            if data['method'] == 'initialize':
                result = {'protocolVersion': '2025-03-26', 'capabilities': {'tools': {}},
                          'serverInfo': {'name': 'fixture', 'version': '1'}}
            elif data['method'] == 'tools/list':
                cursor = data.get('params', {}).get('cursor')
                result = {'tools': [{'name': 'second' if cursor else 'first', 'inputSchema': {'type': 'object'}}]}
                if not cursor: result['nextCursor'] = 'next'
            else: return httpx.Response(400)
            return httpx.Response(200, json={'jsonrpc': '2.0', 'id': data['id'], 'result': result})
        r = await self.simulate(handler)
        self.assertEqual(r['protocol'], 'passed')
        self.assertEqual(r['tool_count'], 2)
        self.assertEqual(r['business'], 'not-tested')

    async def test_mismatched_response_id_not_success(self):
        r = await self.simulate(lambda req: httpx.Response(200, json={'jsonrpc': '2.0', 'id': 999,
            'result': {'protocolVersion': '2025-03-26', 'capabilities': {}, 'serverInfo': {'name': 'fixture', 'version': '1'}}}), timeout=0.1)
        self.assertNotEqual(r['protocol'], 'passed')

    async def test_parameters_and_restricted_are_not_contacted(self):
        e = entry(); e['parameters'] = [{'name': 'TOKEN'}]
        self.assertEqual((await probe(e))['protocol'], 'skipped')
        e = entry(); e['availability'] = 'restricted'
        self.assertEqual((await probe(e))['protocol'], 'skipped')

    def test_private_urls_rejected(self):
        for url in ['http://127.0.0.1/mcp', 'https://192.168.1.1/mcp', 'https://u:p@example.com/mcp', 'https://mcp.woa.com/mcp']:
            with self.assertRaises(ValueError): check_public_url(url)

    async def test_network_policy_block_is_not_service_failure(self):
        from scripts.probe import ProbePolicyError
        with patch('scripts.probe.check_public_url', side_effect=ProbePolicyError('blocked')):
            result = await probe(entry())
        self.assertEqual(result['protocol'], 'skipped')
        self.assertEqual(result['error_category'], 'network-policy-blocked')
