"""
Checks VIVO representation routes with made-up upstream bytes.
"""

from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase

from vivo_app.lib.page_errors import PageDataError
from vivo_app.lib.source_requests import vitro_key
from vivo_app.lib.source_types import RequestKey, SourceResponse


class SourceRepresentationTests(TestCase):
    """Checks exact requests, original bytes, redirects, and absent source responses."""

    def setUp(self) -> None:
        """
        Creates three distinct made-up response bodies.
        """
        self.responses = {
            vitro_key('invented-a', 'jsonld'): b'{"id":"invented-a"}',
            vitro_key('invented-a', 'ttl'): b'@prefix ex: <https://example.invalid/> .\n',
            vitro_key('invented-a', 'rdf'): b'<rdf:RDF/>',
        }
        self.requested: list[RequestKey] = []

    def read(
        self,
        key: RequestKey,
    ) -> SourceResponse:
        """
        Reads only a matching made-up representation.

        Called by: test_exports_retain_bytes(), test_missing_source_response_fails()
        """
        self.requested.append(key)
        body = self.responses.get(key)
        if body is None:
            raise PageDataError('The requested source response is missing.')
        return SourceResponse(200, (), body)

    def test_exports_retain_bytes(self) -> None:
        """
        Checks all three formats keep bytes and use distinct upstream headers.
        """
        with patch('vivo_app.views.read_source', side_effect=self.read):
            for fmt, content_type in (
                ('jsonld', 'application/json'),
                ('ttl', 'text/turtle'),
                ('rdf', 'application/rdf+xml'),
            ):
                response = self.client.get(f'/individual/invented-a/invented-a.{fmt}')
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, self.responses[vitro_key('invented-a', fmt)])
                self.assertTrue(response['Content-Type'].startswith(content_type))
        self.assertEqual(list(self.requested), list(self.responses))

    def test_redirects_use_exact_accept_values(self) -> None:
        """
        Checks format Accept values select 303 exports and ordinary Accept selects HTML.
        """
        for accept, suffix in (
            ('application/json', 'jsonld'),
            ('text/turtle', 'ttl'),
            ('application/rdf+xml', 'rdf'),
        ):
            response = self.client.get('/individual/invented-a', HTTP_ACCEPT=accept)
            assert isinstance(response, HttpResponse)
            self.assertEqual(response.status_code, 303)
            self.assertTrue(response['Location'].endswith(f'/individual/invented-a/invented-a.{suffix}'))
        html = self.client.get('/individual/invented-a', HTTP_ACCEPT='text/html')
        assert isinstance(html, HttpResponse)
        self.assertEqual(html.status_code, 303)
        self.assertTrue(html['Location'].endswith('/display/invented-a'))

    def test_missing_source_response_fails(self) -> None:
        """
        Checks an absent export never substitutes public or sample data.
        """
        with patch('vivo_app.views.read_source', side_effect=self.read):
            self.responses.pop(vitro_key('invented-a', 'ttl'))
            missing = self.client.get('/individual/invented-a/invented-a.ttl')
            mismatch = self.client.get('/individual/invented-a/other.rdf')
        assert isinstance(missing, HttpResponse) and isinstance(mismatch, HttpResponse)
        self.assertEqual(missing.status_code, 503)
        self.assertEqual(mismatch.status_code, 503)
        with self.assertRaises(PageDataError):
            vitro_key('invented-a', 'unsupported')
