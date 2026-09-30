"""
Checks the public advanced search form and its fielded search redirect.
"""

from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings
from django.urls import get_script_prefix, set_script_prefix

from vivo_app.lib.advanced_search import advanced_search_query


@override_settings(PAGE_DATA_MODE='live', SOLR_URL='http://example.invalid/solr/example')
class AdvancedSearchTests(SimpleTestCase):
    """Checks advanced search without contacting a source service."""

    def test_form_and_blank_submission(self) -> None:
        """
        Checks the live form has the two Rails fields and a blank search stays on the form.
        """
        with patch('vivo_app.lib.source_requests.read_source') as read:
            page = self.client.get('/search/advanced/')
            self.assertContains(page, 'Researcher Name')
            self.assertContains(page, 'Researcher Title')
            self.assertContains(page, 'action="/search/advanced/"')
            blank = self.client.get('/search/advanced/?name_t=+&title_t=&search=true')
            self.assertContains(blank, 'Advanced Search')
            read.assert_not_called()

    def test_submission_redirects_to_mounted_search(self) -> None:
        """
        Checks the entered title and name reach the mounted search as one fielded term.
        """
        prefix = '/mounted-app'
        previous_prefix = get_script_prefix()
        set_script_prefix(prefix)
        try:
            response = self.client.get(
                '/search/advanced/',
                {'name_t': 'Fairbrother', 'title_t': 'Professor', 'search': 'true'},
                SCRIPT_NAME=prefix,
            )
            assert isinstance(response, HttpResponse)
            self.assertEqual(response.status_code, 302)
            destination = urlsplit(response['Location'])
            self.assertEqual(destination.path, prefix + '/search')
            self.assertEqual(parse_qs(destination.query), {'q': ['title_t:"Professor" AND name_t:"Fairbrother"']})
            legacy_path = self.client.get('/search/advanced', SCRIPT_NAME=prefix)
            self.assertContains(legacy_path, 'Advanced Search')
        finally:
            set_script_prefix(previous_prefix)

    def test_quoted_input_stays_within_one_field(self) -> None:
        """
        Checks quotes inside entered values remain part of those values.
        """
        self.assertEqual(advanced_search_query('Professor "A"', '  '), 'title_t:"Professor \\"A\\""')

    def test_department_submission_joins_the_fielded_search(self) -> None:
        """
        Checks a department supplied in the URL joins the public fielded search.
        """
        response = self.client.get(
            '/search/advanced/',
            {'title_t': 'Professor', 'department_t': 'Biology', 'name_t': 'Example', 'search': 'true'},
        )
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            parse_qs(urlsplit(response['Location']).query),
            {'q': ['title_t:"Professor" AND department_t:"Biology" AND name_t:"Example"']},
        )
