"""
Checks public facet JSON encoding with made-up values and no source access.
"""

import json
from unittest.mock import patch

from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings

from vivo_app.lib.prepared_data import PageDataError


@override_settings(PAGE_DATA_MODE='live')
class SearchFacetFormatTests(SimpleTestCase):
    """Checks the array response, empty results and source failure."""

    def test_facet_json_keeps_unicode_types_and_escaped_links(self) -> None:
        """
        Checks compact UTF-8 output preserves order, null values and escaped HTML characters.
        """
        values: list[dict[str, object]] = [
            {
                'text': 'Café <Example>',
                'count': 2,
                'remove_url': None,
                'add_url': '/search?q=Example&fq=affiliations%7CExample',
                'range_start': None,
                'range_end': None,
            },
            {'text': 'Area B', 'count': 0},
        ]
        expected = (
            '[{"text":"Café \\u003cExample\\u003e","count":2,"remove_url":null,'
            '"add_url":"/search?q=Example\\u0026fq=affiliations%7CExample",'
            '"range_start":null,"range_end":null},{"text":"Area B","count":0}]'
        ).encode()
        with patch('vivo_app.views.facet_values_data', return_value=values) as read:
            response = self.client.get('/search_facets?q=Example&f_name=affiliations')
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEqual(response.content, expected)
        self.assertEqual(json.loads(response.content), values)
        read.assert_called_once_with([('q', 'Example'), ('f_name', 'affiliations')], 'live')

    def test_empty_facet_json_stays_an_array(self) -> None:
        """
        Checks an empty source result remains a JSON array with the reference charset.
        """
        with patch('vivo_app.views.facet_values_data', return_value=[]):
            response = self.client.get('/search_facets?q=Example&f_name=affiliations')
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEqual(response.content, b'[]')

    def test_source_failure_retains_the_unavailable_response(self) -> None:
        """
        Checks a source failure does not become a successful empty facet array.
        """
        with patch('vivo_app.views.facet_values_data', side_effect=PageDataError('Example source is unavailable.')):
            response = self.client.get('/search_facets?q=Example&f_name=affiliations')
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 503)
        self.assertContains(response, 'Page data unavailable', status_code=503)
