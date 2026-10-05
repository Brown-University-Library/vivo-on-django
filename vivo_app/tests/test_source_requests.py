"""
Checks source failure diagnostics without contacting a service or logging record content.
"""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RequestKey
from vivo_app.lib.source_requests import read_source


class SourceRequestDiagnosticsTests(SimpleTestCase):
    """Checks useful failure metadata and private request and response content."""

    @override_settings(IMAGES_URL='https://source.invalid', SOLR_URL='https://source.invalid/core')
    def test_images_allow_larger_bodies_without_expanding_solr_limit(self) -> None:
        """
        Checks a portrait can exceed the Solr size limit while Solr still rejects that size.
        """
        response = MagicMock()
        response.status_code = 200
        response.headers = {'content-type': 'image/jpeg'}
        response.iter_bytes.return_value = [b'x' * 150]
        with (
            patch('vivo_app.lib.source_requests.MAX_RESPONSE_BYTES', 100),
            patch('vivo_app.lib.source_requests.MAX_IMAGE_BYTES', 200),
            patch('vivo_app.lib.source_requests.httpx2.Client') as client,
        ):
            client.return_value.__enter__.return_value.stream.return_value.__enter__.return_value = response
            result = read_source(RequestKey('images', '/profile-images/abc/portrait.jpg'), 'live')
            self.assertEqual(result.body, b'x' * 150)
            with self.assertRaisesRegex(PageDataError, 'exceeds the configured size limit'):
                read_source(RequestKey('solr', '/select'), 'live')

    @override_settings(IMAGES_URL='https://source.invalid')
    def test_image_stream_still_stops_at_image_limit(self) -> None:
        """
        Checks streamed image chunks cannot exceed the separate image size limit.
        """
        response = MagicMock()
        response.status_code = 200
        response.headers = {'content-type': 'image/jpeg'}
        response.iter_bytes.return_value = [b'x' * 150, b'y' * 51]
        with (
            patch('vivo_app.lib.source_requests.MAX_IMAGE_BYTES', 200),
            patch('vivo_app.lib.source_requests.httpx2.Client') as client,
        ):
            client.return_value.__enter__.return_value.stream.return_value.__enter__.return_value = response
            with self.assertRaisesRegex(PageDataError, 'exceeds the configured size limit'):
                read_source(RequestKey('images', '/profile-images/abc/portrait.jpg'), 'live')

    @override_settings(UPSTREAM_RECORDING_MANIFEST='unused-recording.json')
    def test_recorded_images_use_the_same_separate_limit(self) -> None:
        """
        Checks recorded portraits retain their bytes and reject bodies beyond the image limit.
        """
        key = RequestKey('images', '/profile-images/abc/portrait.jpg')
        with (
            patch('vivo_app.lib.source_requests.MAX_RESPONSE_BYTES', 100),
            patch('vivo_app.lib.source_requests.MAX_IMAGE_BYTES', 200),
            patch('vivo_app.lib.source_requests.load_recordings') as load,
        ):
            load.return_value.data_kind = 'recorded'
            load.return_value.get.return_value = RecordedResponse(200, (('content-type', 'image/jpeg'),), b'x' * 150)
            self.assertEqual(read_source(key, 'replay').body, b'x' * 150)
            load.return_value.get.return_value = RecordedResponse(200, (('content-type', 'image/jpeg'),), b'x' * 201)
            with (
                self.assertLogs('vivo_app.lib.source_requests', level='WARNING'),
                self.assertRaisesRegex(PageDataError, 'images source returned an unusable response'),
            ):
                read_source(key, 'replay')

    @override_settings(SOLR_URL='https://source.invalid/core')
    def test_rejected_response_logs_metadata_without_private_values(self) -> None:
        """
        Checks an upstream rejection logs its status and sizes while keeping content out of the log.
        """
        response = MagicMock()
        response.status_code = 414
        response.headers = {'content-type': 'text/plain'}
        response.iter_bytes.return_value = [b'invented private response']
        key = RequestKey('solr', '/select', (('q', 'invented private query'),))
        with (
            patch('vivo_app.lib.source_requests.httpx2.Client') as client,
            self.assertLogs('vivo_app.lib.source_requests', level='WARNING') as logs,
        ):
            client.return_value.__enter__.return_value.stream.return_value.__enter__.return_value = response
            with self.assertRaisesRegex(PageDataError, '^solr source returned an unusable response.$'):
                read_source(key, 'live')
        message = '\n'.join(logs.output)
        self.assertIn('status, ``414``', message)
        self.assertIn('query_bytes, ``24``', message)
        self.assertIn('response_bytes, ``25``', message)
        for private_value in ('source.invalid', '/select', 'invented private query', 'invented private response'):
            self.assertNotIn(private_value, message)

    @override_settings(SOLR_URL='https://source.invalid/core')
    def test_successful_response_stays_unchanged_without_failure_log(self) -> None:
        """
        Checks a successful response keeps its exact status, headers and body without a failure log.
        """
        response = MagicMock()
        response.status_code = 200
        response.headers = {'content-type': 'application/json'}
        response.iter_bytes.return_value = [b'{"response":{}}']
        with (
            patch('vivo_app.lib.source_requests.httpx2.Client') as client,
            self.assertNoLogs('vivo_app.lib.source_requests', level='WARNING'),
        ):
            client.return_value.__enter__.return_value.stream.return_value.__enter__.return_value = response
            result = read_source(RequestKey('solr', '/select'), 'live')
        self.assertEqual(result.status, 200)
        self.assertEqual(result.headers, (('content-type', 'application/json'),))
        self.assertEqual(result.body, b'{"response":{}}')
