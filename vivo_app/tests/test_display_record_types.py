"""
Checks display record selection and original VIVO responses using made-up records.
"""

import json
from unittest.mock import patch

from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings

from vivo_app.lib.page_errors import PageDataError
from vivo_app.lib.source_requests import profile_key, vitro_key
from vivo_app.lib.source_types import RequestKey, SourceResponse
from vivo_app.tests.source_fixtures import page_responses, solr_response


@override_settings(TURNSTILE_ENABLED=False, VIZ_ENABLED=False, DISPLAY_JSONLD_CACHE_TIMEOUT_SECONDS=0)
class DisplayRecordTypeTests(SimpleTestCase):
    def setUp(self) -> None:
        """
        Creates made-up responses and records all source requests.
        """
        self.responses = page_responses()
        self.requested: list[RequestKey] = []
        self.body = b'{\n  "@id": "urn:example:record", "label": "Example & record"\n}\n'

    def add_record(self, identifier: str, record_type: object) -> None:
        """
        Adds a made-up record using the canonical URI namespace from the shared examples.

        Called by: test methods
        """
        person = json.loads(self.responses[profile_key('invented-a')].body)['response']['docs'][0]
        namespace = person['id'].rsplit('/', 1)[0]
        doc = {
            'id': namespace + '/' + identifier,
            'record_type': record_type,
            'json_txt': json.dumps({'name': 'Example record'}),
            'display_name_s': 'Example record',
        }
        self.responses[profile_key(identifier)] = solr_response([doc], 1)
        self.responses[vitro_key(identifier, 'jsonld')] = SourceResponse(200, (), self.body)

    def read(self, key: RequestKey) -> SourceResponse:
        """
        Supplies made-up responses and fails instead of making network requests.

        Called by: get_display()
        """
        self.requested.append(key)
        response = self.responses.get(key)
        if response is None:
            raise PageDataError('Example source request failed.')
        return response

    def get_display(self, path: str, method: str = 'GET', prefix: str = '') -> HttpResponse:
        """
        Requests a display response with both source readers replaced by made-up data.

        Called by: test methods
        """
        with (
            patch('vivo_app.lib.source_pages.read_source', side_effect=self.read),
            patch('vivo_app.lib.page_data.read_source', side_effect=self.read),
        ):
            response = self.client.generic(method, path, SCRIPT_NAME=prefix)
        assert isinstance(response, HttpResponse)
        return response

    def test_other_record_types_return_original_jsonld(self) -> None:
        """
        Checks uncategorized and other non-person records retain VIVO bytes for both display URL forms.
        """
        for record_type in (['UNCATEGORIZED'], 'UNCATEGORIZED', ['EXAMPLE_OTHER_TYPE']):
            for suffix, prefix in (('', ''), ('/', ''), ('', '/mounted-app')):
                with self.subTest(record_type=record_type, suffix=suffix, prefix=prefix):
                    self.add_record('invented-other', record_type)
                    self.requested.clear()
                    response = self.get_display('/display/invented-other' + suffix, prefix=prefix)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.content, self.body)
                    self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
                    self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
                    self.assertEqual(self.requested, [profile_key('invented-other'), vitro_key('invented-other', 'jsonld')])

    def test_head_retains_headers_without_response_body(self) -> None:
        """
        Checks HEAD keeps the JSON content type and omits response bytes.
        """
        self.add_record('invented-other', ['UNCATEGORIZED'])
        response = self.get_display('/display/invented-other', method='HEAD')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'')
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')

    def test_html_selection_uses_record_type_instead_of_id_prefix(self) -> None:
        """
        Checks organization and person records select the right template regardless of their ID prefix.
        """
        cases = (
            ('invented-organization', ['ORGANIZATION'], 'display/organization_data.html'),
            ('org-invented-person', ['PEOPLE'], 'display/profile_data.html'),
        )
        for identifier, record_type, template in cases:
            with self.subTest(identifier=identifier):
                self.add_record(identifier, record_type)
                self.requested.clear()
                response = self.get_display('/display/' + identifier)
                self.assertContains(response, 'Example record')
                self.assertTemplateUsed(response, template)
                self.assertEqual(self.requested, [profile_key(identifier)])

    def test_missing_or_untyped_solr_records_remain_not_found(self) -> None:
        """
        Checks missing records and records without a type never request VIVO data.
        """
        for record_type in (None, [], ''):
            with self.subTest(record_type=record_type):
                self.add_record('invented-other', record_type)
                self.requested.clear()
                response = self.get_display('/display/invented-other')
                self.assertContains(response, 'Page not found', status_code=404)
                self.assertEqual(self.requested, [profile_key('invented-other')])
        self.responses[profile_key('invented-other')] = solr_response([], 0)
        self.requested.clear()
        response = self.get_display('/display/invented-other')
        self.assertContains(response, 'Page not found', status_code=404)
        self.assertEqual(self.requested, [profile_key('invented-other')])

    def test_invalid_identifiers_return_not_found_without_cache_or_source_reads(self) -> None:
        """
        Checks malformed display identifiers return 404 without being trimmed, decoded again, or fetched.
        """
        for identifier in ('invented-a%20', 'invented-a%2520', '%20invented-a', 'invented.a', 'a' * 81):
            with self.subTest(identifier=identifier), patch('vivo_app.views.cached_display_data') as cached:
                response = self.get_display('/display/' + identifier)
                self.assertContains(response, 'Page not found', status_code=404)
                self.assertNotIn('Location', response)
                cached.assert_not_called()
        self.assertEqual(self.requested, [])

    def test_invalid_identifiers_return_not_found_for_formats_and_aliases(self) -> None:
        """
        Checks malformed identifiers cannot enter any display format handler, including HEAD and mounted URLs.
        """
        with (
            patch('vivo_app.views.cached_display_data') as cached,
            patch('vivo_app.views.cached_display') as exports,
            patch('vivo_app.views.profile_json_data') as profile,
            patch('vivo_app.views.organization_json_data') as organization,
            patch('vivo_app.views.raw_record_json_data') as raw,
        ):
            for suffix in ('/', '.json', '.json_txt', '.csv', '.xml', '?format=json', '?format=json_txt', '?format=csv'):
                for method in ('GET', 'HEAD'):
                    with self.subTest(suffix=suffix, method=method):
                        response = self.get_display(
                            '/display/invented-other%2520' + suffix, method=method, prefix='/mounted-app'
                        )
                        self.assertEqual(response.status_code, 404)
                        self.assertNotIn('Location', response)
                        if method == 'HEAD':
                            self.assertEqual(response.content, b'')
            for handler in (cached, exports, profile, organization, raw):
                handler.assert_not_called()
        self.assertEqual(self.requested, [])

    def test_valid_identifier_length_boundaries_keep_working(self) -> None:
        """
        Checks one-character and eighty-character identifiers retain normal source lookups.
        """
        for identifier in ('a', 'Example_1-' + 'a' * 70):
            with self.subTest(identifier=identifier):
                self.add_record(identifier, ['UNCATEGORIZED'])
                self.requested.clear()
                response = self.get_display('/display/' + identifier)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, self.body)
                self.assertEqual(self.requested, [profile_key(identifier), vitro_key(identifier, 'jsonld')])

    def test_unrelated_solr_record_is_not_forwarded_to_vivo(self) -> None:
        """
        Checks a mismatched source ID remains an error instead of selecting a VIVO response.
        """
        self.add_record('invented-other', ['UNCATEGORIZED'])
        self.responses[profile_key('invented-requested')] = self.responses[profile_key('invented-other')]
        with self.assertLogs('vivo_app.views', level='ERROR'):
            response = self.get_display('/display/invented-requested')
        self.assertContains(response, 'Oops! Something went wrong', status_code=500)
        self.assertEqual(self.requested, [profile_key('invented-requested')])

    def test_vivo_not_found_retains_source_status_and_bytes(self) -> None:
        """
        Checks a VIVO 404 keeps the original response as Rails does.
        """
        self.add_record('invented-other', ['UNCATEGORIZED'])
        self.responses[vitro_key('invented-other', 'jsonld')] = SourceResponse(404, (), b'{"error":"missing"}')
        response = self.get_display('/display/invented-other')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, b'{"error":"missing"}')
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')

    def test_vivo_failure_keeps_shared_error_page(self) -> None:
        """
        Checks failed VIVO reads keep the display error page and hide source error details.
        """
        self.add_record('invented-other', ['UNCATEGORIZED'])
        del self.responses[vitro_key('invented-other', 'jsonld')]
        with self.assertLogs('vivo_app.views', level='ERROR'):
            response = self.get_display('/display/invented-other')
        self.assertContains(response, 'Oops! Something went wrong', status_code=500)
        self.assertNotContains(response, 'Example source request failed', status_code=500)

    def test_unrelated_query_does_not_change_source_requests(self) -> None:
        """
        Checks unrelated parameters leave the requested record and source requests unchanged.
        """
        self.add_record('invented-other', ['UNCATEGORIZED'])
        response = self.get_display('/display/invented-other?utm_source=example&id=other&url=example&fq=other')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.body)
        self.assertEqual(self.requested, [profile_key('invented-other'), vitro_key('invented-other', 'jsonld')])

    def test_tracking_parameter_keeps_profile_html(self) -> None:
        """
        Checks a tracking link renders the faculty profile with the same source request as a plain link.
        """
        self.add_record('invented-person', ['PEOPLE'])
        response = self.get_display('/display/invented-person?utm_source=example')
        self.assertContains(response, 'Example record')
        self.assertTemplateUsed(response, 'display/profile_data.html')
        self.assertEqual(self.requested, [profile_key('invented-person')])

    @override_settings(DATA_UPLOAD_MAX_NUMBER_FIELDS=2)
    def test_query_field_limit_remains_enforced(self) -> None:
        """
        Checks Django still rejects requests exceeding the configured query-field limit.
        """
        for path in ('/', '/display/invented-other'):
            with self.subTest(path=path):
                response = self.get_display(path + '?one=1&two=2&three=3')
                self.assertEqual(response.status_code, 400)
        self.assertEqual(self.requested, [])
