"""
Checks Solr status and legacy image redirects with made-up inputs.
"""

import json
import uuid
from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase, override_settings

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RequestKey
from vivo_app.lib.source_requests import status_key
from vivo_app.lib.source_status import NoSearchResultsError, status_data


class SourceStatusTests(TestCase):
    """Checks a positive source count and a controlled failure."""

    def read(self, key: RequestKey, mode: str) -> RecordedResponse:
        """
        Returns one made-up count for each mode.

        Called by: test_count_uses_same_request_in_live_and_replay()
        """
        self.calls.append((key, mode))
        body = {'responseHeader': {'status': 0}, 'response': {'numFound': getattr(self, 'source_count', 27), 'docs': []}}
        return RecordedResponse(200, (), json.dumps(body).encode())

    def test_count_uses_same_request_in_live_and_replay(self) -> None:
        """
        Checks both modes use a single count request and keep the result text.
        """
        self.calls: list[tuple[RequestKey, str]] = []
        self.assertEqual(status_data('live', self.read), {'status': 'OK', 'message': '27 records found.'})
        self.assertEqual(status_data('replay', self.read), {'status': 'OK', 'message': '27 records found.'})
        self.assertEqual(self.calls, [(status_key(), 'live'), (status_key(), 'replay')])

    @override_settings(PAGE_DATA_MODE='replay', UPSTREAM_RECORDING_MANIFEST='unused-in-this-test')
    def test_missing_count_returns_error_json(self) -> None:
        """
        Checks an unavailable recorded count cannot become a successful status.
        """
        with patch('vivo_app.views.status_data', side_effect=PageDataError('Missing recording.')):
            response = self.client.get('/status')
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(json.loads(response.content)['status'], 'ERROR')

    def test_empty_and_invalid_counts_remain_distinct(self) -> None:
        """
        Checks zero and negative counts identify an empty index, while an invalid count identifies a failed check.
        """
        self.calls: list[tuple[RequestKey, str]] = []
        self.source_count: int | None = 0
        for count in (0, -1):
            self.source_count = count
            with self.assertRaises(NoSearchResultsError):
                status_data('live', self.read)
        self.source_count = None
        with self.assertRaises(PageDataError) as raised:
            status_data('live', self.read)
        self.assertNotIsInstance(raised.exception, NoSearchResultsError)

    @override_settings(PAGE_DATA_MODE='live')
    def test_error_messages_and_logged_ids_match_reference(self) -> None:
        """
        Checks empty-index and source-exception responses use the reference text and a matching log ID.
        """
        identifier = uuid.UUID('00000000-0000-4000-8000-000000000001')
        cases = (
            (NoSearchResultsError('Made-up empty index.'), f'No search results were found ({identifier})'),
            (PageDataError('Made-up unavailable source.'), f'Exception was found. See the log file ({identifier}).'),
            (RuntimeError('Made-up failure.'), f'Exception was found. See the log file ({identifier}).'),
        )
        for error, message in cases:
            with (
                patch('vivo_app.views.status_data', side_effect=error),
                patch('vivo_app.lib.source_status.uuid.uuid4', return_value=identifier),
                self.assertLogs('vivo_app.views', level='ERROR') as logs,
            ):
                response = self.client.get('/status')
            assert isinstance(response, HttpResponse)
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response['Content-Type'], 'application/json')
            self.assertEqual(json.loads(response.content), {'status': 'ERROR', 'message': message})
            self.assertIn(str(identifier), logs.output[0])
            self.assertNotIn('Made-up', logs.output[0])

    @override_settings(PAGE_DATA_MODE='replay', UPSTREAM_RECORDING_MANIFEST='unused-in-this-test')
    def test_failures_receive_distinct_tracking_ids(self) -> None:
        """
        Checks separate failed requests receive distinct valid UUIDs.
        """
        identifiers: list[str] = []
        with (
            patch('vivo_app.views.status_data', side_effect=PageDataError('Made-up failure.')),
            self.assertLogs('vivo_app.views', level='ERROR'),
        ):
            for _ in range(2):
                response = self.client.get('/status')
                assert isinstance(response, HttpResponse)
                message = json.loads(response.content)['message']
                identifier = message.split('(')[1].split(')')[0]
                self.assertEqual(str(uuid.UUID(identifier)), identifier)
                identifiers.append(identifier)
        self.assertNotEqual(identifiers[0], identifiers[1])


@override_settings(PAGE_DATA_MODE='replay', UPSTREAM_RECORDING_MANIFEST='unused-in-this-test')
class OldImageTests(TestCase):
    """Checks legacy paths redirect locally only when valid."""

    def test_valid_image_redirects(self) -> None:
        """
        Checks the original route and three-digit image grouping.
        """
        response = self.client.get('/file/n12345/example.jpg')
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], '/source-images/profile-images/123/45/example.jpg')

    def test_invalid_image_is_missing(self) -> None:
        """
        Checks malformed identifiers and filenames do not redirect.
        """
        response = self.client.get('/file/1/example.jpg')
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 404)
