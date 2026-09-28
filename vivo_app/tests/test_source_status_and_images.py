"""
Checks Solr status and legacy image redirects with made-up inputs.
"""

import json
from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase, override_settings

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RequestKey
from vivo_app.lib.source_requests import status_key
from vivo_app.lib.source_status import status_data


class SourceStatusTests(TestCase):
    """Checks a positive source count and a controlled failure."""

    def read(self, key: RequestKey, mode: str) -> RecordedResponse:
        """
        Returns one made-up count for each mode.

        Called by: test_count_uses_same_request_in_live_and_replay()
        """
        self.calls.append((key, mode))
        body = {'responseHeader': {'status': 0}, 'response': {'numFound': 27, 'docs': []}}
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
