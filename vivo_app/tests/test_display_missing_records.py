"""
Checks display pages and JSON distinguish missing records from failed or inconsistent source reads.
"""

from unittest.mock import patch

from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings

from vivo_app.lib.page_errors import PageDataError
from vivo_app.lib.source_requests import profile_export_key, profile_key
from vivo_app.lib.source_types import RequestKey, SourceResponse
from vivo_app.tests.source_fixtures import page_responses, solr_response
from vivo_app.tests.test_display_exports import person_doc


@override_settings(TURNSTILE_ENABLED=False, VIZ_ENABLED=False, DISPLAY_JSONLD_CACHE_TIMEOUT_SECONDS=0)
class DisplayMissingRecordTests(SimpleTestCase):
    def setUp(self) -> None:
        """
        Checks each request against isolated made-up source responses.
        """
        self.responses = page_responses()
        self.responses[profile_export_key('invented-a')] = solr_response(
            [person_doc('invented-a', uri='http://vivo.brown.edu/individual/invented-a')], 1
        )
        self.requested: list[RequestKey] = []
        self.enterContext(patch('vivo_app.lib.source_pages.read_source', side_effect=self.read))
        self.enterContext(patch('vivo_app.lib.source_formats.read_source', side_effect=self.read))

    def read(self, key: RequestKey) -> SourceResponse:
        """
        Supplies one made-up response and records every requested lookup.

        Called by: source readers in tests
        """
        self.requested.append(key)
        if key not in self.responses:
            raise PageDataError('Example source failure.')
        return self.responses[key]

    def get_display(self, identifier: str, suffix: str, method: str = 'GET') -> HttpResponse:
        """
        Requests a display representation through Django.

        Called by: test methods
        """
        response = self.client.generic(method, '/display/' + identifier + suffix)
        assert isinstance(response, HttpResponse)
        return response

    def test_missing_records_return_404_for_html_and_json_forms(self) -> None:
        """
        Checks missing people and organizations return 404 without logging a display exception.
        """
        for identifier in ('invented-a', 'org-example'):
            self.responses[profile_key(identifier)] = solr_response([], 0)
            self.responses[profile_export_key(identifier)] = solr_response([], 0)
            for suffix in ('', '.json', '?format=json', '.json_txt', '?format=json_txt'):
                for method in ('GET', 'HEAD'):
                    with (
                        self.subTest(identifier=identifier, suffix=suffix, method=method),
                        patch('vivo_app.views.logger.exception') as error,
                    ):
                        self.requested.clear()
                        response = self.get_display(identifier, suffix, method)
                        self.assertEqual(response.status_code, 404)
                        if method == 'HEAD':
                            self.assertEqual(response.content, b'')
                        else:
                            self.assertContains(response, 'Page not found', status_code=404)
                        self.assertEqual(len(self.requested), 1)
                        error.assert_not_called()

    def test_new_record_is_visible_on_next_request_after_missing_response(self) -> None:
        """
        Checks a newly available person or organization appears immediately in every JSON form.
        """
        for identifier in ('invented-a', 'org-example'):
            for suffix in ('.json', '?format=json', '.json_txt', '?format=json_txt'):
                with self.subTest(identifier=identifier, suffix=suffix):
                    original = dict(self.responses)
                    self.responses[profile_key(identifier)] = solr_response([], 0)
                    self.responses[profile_export_key(identifier)] = solr_response([], 0)
                    self.assertEqual(self.get_display(identifier, suffix).status_code, 404)
                    self.responses = original
                    response = self.get_display(identifier, suffix)
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response['Content-Type'].startswith('application/json'))

    def test_inconsistent_or_unrelated_results_remain_errors(self) -> None:
        """
        Checks incorrect counts, duplicate documents, and mismatched IDs cannot become successful or missing responses.
        """
        doc = person_doc('invented-a')
        cases = (([], 1), ([doc], 0), ([doc], 2), ([doc, doc], 1), ([person_doc('invented-other')], 1))
        for docs, total in cases:
            for suffix in ('', '.json', '.json_txt'):
                with self.subTest(total=total, documents=len(docs), suffix=suffix):
                    self.responses[profile_key('invented-a')] = solr_response(docs, total)
                    self.responses[profile_export_key('invented-a')] = solr_response(docs, total)
                    with self.assertLogs('vivo_app.views', level='WARNING'):
                        response = self.get_display('invented-a', suffix)
                    self.assertContains(response, 'Oops! Something went wrong', status_code=500)

    def test_source_failures_remain_errors(self) -> None:
        """
        Checks a failed request or invalid source JSON never becomes a missing-record response.
        """
        for identifier in ('invented-a', 'org-example'):
            for suffix in ('', '.json', '.json_txt'):
                for response in (None, SourceResponse(200, (), b'{invalid')):
                    with self.subTest(identifier=identifier, suffix=suffix, response=response):
                        for key in (profile_key(identifier), profile_export_key(identifier)):
                            if response is None:
                                self.responses.pop(key, None)
                            else:
                                self.responses[key] = response
                        with self.assertLogs('vivo_app.views', level='WARNING'):
                            self.assertEqual(self.get_display(identifier, suffix).status_code, 500)
