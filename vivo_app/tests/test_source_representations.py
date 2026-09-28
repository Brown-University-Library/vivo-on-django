"""
Checks VIVO representation routes with made-up upstream bytes.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase, override_settings

from tools.source_capture import capture_vivo_exports
from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RequestKey
from vivo_app.lib.source_requests import read_source, vitro_key


@override_settings(PAGE_DATA_MODE='replay', UPSTREAM_RECORDING_MANIFEST='unused-in-this-test')
class SourceRepresentationTests(TestCase):
    """Checks exact requests, original bytes, redirects, and absent recordings."""

    def setUp(self) -> None:
        """
        Creates three distinct made-up response bodies.
        """
        self.responses = {
            vitro_key('invented-a', 'jsonld'): b'{"id":"invented-a"}',
            vitro_key('invented-a', 'ttl'): b'@prefix ex: <https://example.invalid/> .\n',
            vitro_key('invented-a', 'rdf'): b'<rdf:RDF/>',
        }
        self.requested: list[tuple[RequestKey, str]] = []

    def read(self, key: RequestKey, mode: str) -> RecordedResponse:
        """
        Reads only a matching made-up representation.

        Called by: test_exports_retain_bytes(), test_missing_recording_fails()
        """
        self.requested.append((key, mode))
        body = self.responses.get(key)
        if body is None:
            raise PageDataError('The requested recording is missing.')
        return RecordedResponse(200, (), body)

    def read_live(self, key: RequestKey, mode: str) -> RecordedResponse:
        """
        Supplies one made-up live representation to the bounded capture.

        Called by: test_capture_replays_the_same_three_requests_offline()
        """
        if mode != 'live' or key not in self.responses:
            raise PageDataError('The requested response is unavailable.')
        return RecordedResponse(200, (('content-type', 'text/plain'),), self.responses[key])

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
        self.assertEqual([key for key, _ in self.requested], list(self.responses))
        self.assertEqual({mode for _, mode in self.requested}, {'replay'})

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

    def test_missing_recording_fails(self) -> None:
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

    def test_capture_replays_the_same_three_requests_offline(self) -> None:
        """
        Checks bounded VIVO capture saves three original responses for exact replay.
        """
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'exports'
            with (
                patch('tools.source_capture.read_source', side_effect=self.read_live),
                patch('tools.source_capture.time.sleep'),
            ):
                count = capture_vivo_exports('invented-a', output)
            self.assertEqual(count, 3)
            with override_settings(
                UPSTREAM_RECORDING_MANIFEST=str(output / 'manifest.json'), UPSTREAM_RECORDING_CASE='vivo-exports'
            ):
                for key, body in self.responses.items():
                    self.assertEqual(read_source(key, 'replay').body, body)
