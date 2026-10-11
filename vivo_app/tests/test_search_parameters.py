"""
Checks Rails-compatible search parameter selection before Solr requests.
"""

from html import escape
from unittest.mock import call, patch
from urllib.parse import urlencode

from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings

from vivo_app.lib.page_errors import PageDataError
from vivo_app.lib.source_pages import search_inputs
from vivo_app.lib.source_requests import search_key
from vivo_app.tests.source_fixtures import page_responses


@override_settings(
    SOLR_URL='https://example.invalid/solr',
    TURNSTILE_ENABLED=False,
    CONTACT_US_URL_TEMPLATE='',
    SESSION_ENGINE='django.contrib.sessions.backends.signed_cookies',
)
class SearchParameterTests(SimpleTestCase):
    def test_unknown_parameters_preserve_search_responses_and_solr_requests(self) -> None:
        """
        Checks extra options leave HTML, JSON, facets, pagination and repeated filters unchanged.
        """
        source_response = page_responses()[search_key('Example', 1, [])]
        cases = [
            ('/search', [('q', 'biology')], 1, [], 11),
            ('/search', [('q', 'biology'), ('format', 'json')], 1, [], 11),
            ('/search_facets', [('q', 'biology'), ('f_name', 'affiliations')], 1, [], -1),
            (
                '/search',
                [('q', 'biology'), ('page', '2'), ('fq', 'record_type|PEOPLE'), ('fq_1', 'research_areas|Science')],
                2,
                [('record_type', 'PEOPLE'), ('research_areas', 'Science')],
                11,
            ),
        ]
        for path, pairs, page, filters, facet_limit in cases:
            with self.subTest(path=path, pairs=pairs):
                expected = search_key('biology', page, filters, facet_limit)
                extra_pairs = [*pairs, ('unexpected', '1'), ('unexpected', ''), ('fl', 'ignored'), ('wt', 'xml')]
                with patch('vivo_app.lib.source_pages.read_source', return_value=source_response) as reader:
                    baseline = self.client.get(path, pairs)
                    with self.assertLogs('vivo_app.lib.source_pages', level='WARNING') as logs:
                        response = self.client.get(path, extra_pairs)
                assert isinstance(baseline, HttpResponse) and isinstance(response, HttpResponse)
                self.assertEqual(baseline.status_code, 200)
                self.assertEqual(response.status_code, 200)
                ## Rails keeps the original query string in the Advanced search link.
                old_link = escape('/search/advanced?' + urlencode(pairs)).encode()
                new_link = escape('/search/advanced?' + urlencode(extra_pairs)).encode()
                self.assertEqual(response.content, baseline.content.replace(old_link, new_link))
                self.assertEqual(
                    {key: value for key, value in response.items() if key != 'Content-Length'},
                    {key: value for key, value in baseline.items() if key != 'Content-Length'},
                )
                self.assertEqual(reader.call_args_list, [call(expected), call(expected)])
                self.assertEqual(len(logs.records), 1)
                self.assertEqual(
                    logs.records[0].getMessage(),
                    'Dropped unsupported search parameters; parameter_names, ``["unexpected", "fl", "wt"]``',
                )

    def test_rails_parameter_names_keep_filters_and_fixed_page_size(self) -> None:
        """
        Checks Rails filter-prefix handling and its fixed page size despite a supplied rows value.
        """
        pairs = [('q', 'biology'), ('page', '2'), ('rows', '999'), ('fq_named', 'record_type|PEOPLE')]
        with self.assertNoLogs('vivo_app.lib.source_pages', level='WARNING'):
            query, page, filters = search_inputs(pairs)
        self.assertEqual((query, page, filters), ('biology', 2, [('record_type', 'PEOPLE')]))
        request = search_key(query, page, filters)
        self.assertEqual(dict(request.query)['rows'], '20')
        self.assertEqual(dict(request.query)['start'], '20')
        self.assertIn(('fq', 'record_type:"PEOPLE"'), request.query)
        self.assertEqual(pairs[2], ('rows', '999'))

    def test_unknown_parameters_alone_keep_the_default_search(self) -> None:
        """
        Checks empty and unknown-only queries both produce the default search.
        """
        with self.assertLogs('vivo_app.lib.source_pages', level='WARNING'):
            result = search_inputs([('unexpected', '')])
        self.assertEqual(result, search_inputs([]))

    def test_dropped_parameter_log_escapes_names_and_omits_values(self) -> None:
        """
        Checks one log line names dropped parameters without including their values.
        """
        with self.assertLogs('vivo_app.lib.source_pages', level='WARNING') as logs:
            search_inputs([('unexpected\nname', 'private-example-value'), ('another', 'second-private-value')])
        message = logs.records[0].getMessage()
        self.assertIn('unexpected\\nname', message)
        self.assertIn('another', message)
        self.assertNotIn('\n', message)
        self.assertNotIn('private', message)
        self.assertIn('Dropped', message)

    def test_invalid_supported_values_still_fail_before_source_requests(self) -> None:
        """
        Checks dropping unknown names does not bypass page, query or filter-field validation.
        """
        for pairs in (
            [('page', '0')],
            [('q', 'one'), ('q', 'two')],
            [('fq', 'unknown_field|Example')],
            [('fq_named', 'missing-separator')],
        ):
            with self.subTest(pairs=pairs), self.assertRaises(PageDataError):
                search_inputs(pairs)
