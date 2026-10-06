"""
Checks demonstrated reference search failures using made-up publication annotations.
"""

from unittest.mock import patch

from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings

from vivo_app.lib.search_errors import ReferenceSearchError, check_reference_filter_markup
from vivo_app.lib.source_pages import search_inputs
from vivo_app.lib.source_requests import search_key


class ReferenceSearchErrorTests(SimpleTestCase):
    def test_publication_annotation_failure_preserves_filters_and_ordinary_quoting(self) -> None:
        """
        Checks repeated filter input and ordinary values without changing source-query quoting.
        """
        annotation = 'Example <html_ent glyph="@amp;" ascii="&amp;"/> Journal'
        for key in ('fq', 'fq_0'):
            with self.subTest(key=key), self.assertRaises(ReferenceSearchError):
                search_inputs([('fq', 'record_type|PEOPLE'), (key, 'published_in|' + annotation)])
        ordinary = [('published_in', 'Example &amp; Journal'), ('published_in', 'Example "quoted" Journal')]
        check_reference_filter_markup(ordinary)
        check_reference_filter_markup([('research_areas', annotation)])
        key = search_key('', 1, ordinary)
        filters = [value for name, value in key.query if name == 'fq']
        self.assertIn('published_in:"Example &amp; Journal"', filters)
        self.assertIn('published_in:"Example \\"quoted\\" Journal"', filters)

    @override_settings(
        SOLR_URL='https://example.invalid/solr/example',
        UPSTREAM_RECORDING_MANIFEST='unused-example-manifest.json',
        TURNSTILE_ENABLED=False,
        CONTACT_US_URL_TEMPLATE='https://example.invalid/feedback?url={LINK}',
    )
    def test_live_and_replay_failures_keep_reference_response_and_search_recovery(self) -> None:
        """
        Checks HTML, search JSON and facet failures without contacting a data source.
        """
        filters = {'fq': 'published_in|Example <html_ent glyph="@amp;" ascii="&amp;"/> Journal'}
        for mode in ('live', 'replay'):
            with (
                self.subTest(mode=mode),
                override_settings(PAGE_DATA_MODE=mode),
                patch('vivo_app.lib.source_pages.read_source') as reader,
            ):
                response = self.client.get('/search', filters)
                assert isinstance(response, HttpResponse)
                self.assertContains(response, 'Oops! Something went wrong', status_code=500)
                self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
                self.assertContains(response, 'name="q"', status_code=500)
                self.assertContains(response, 'action="/search"', status_code=500)
                self.assertContains(response, 'autofocus', status_code=500)
                self.assertNotContains(response, '<html_ent ', status_code=500)
                search_json = self.client.get('/search', {**filters, 'format': 'json'})
                assert isinstance(search_json, HttpResponse)
                self.assertEqual(search_json.status_code, 500)
                self.assertEqual(search_json.content, b'{"status":500,"error":"Internal Server Error"}')
                self.assertEqual(search_json['Content-Type'], 'application/json; charset=UTF-8')
                facets = self.client.get('/search_facets', {**filters, 'f_name': 'published_in'})
                assert isinstance(facets, HttpResponse)
                self.assertEqual(facets.status_code, 500)
                self.assertEqual(facets.content, b'null')
                self.assertEqual(facets['Content-Type'], 'application/json; charset=utf-8')
                reader.assert_not_called()
