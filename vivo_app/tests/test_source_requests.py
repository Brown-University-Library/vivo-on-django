"""
Checks source failure diagnostics without contacting a service or logging record content.
"""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RequestKey
from vivo_app.lib.source_requests import read_source


class SourceRequestDiagnosticsTests(SimpleTestCase):
    """Checks useful failure metadata and private request and response content."""

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
