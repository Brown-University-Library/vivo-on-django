"""
Checks profile HTML uses source data and preserves search-return navigation.
"""

from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase

from vivo_app.tests.source_fixtures import page_responses


class DisplayShowTests(TestCase):
    def test_profile_content_and_search_return(self) -> None:
        """
        Checks direct visits and search visits retain the same profile with the appropriate return link.
        """
        responses = page_responses()
        with patch('vivo_app.lib.source_pages.read_source', side_effect=responses.__getitem__):
            direct = self.client.get('/display/invented-a')
            search_visit = self.client.get('/display/invented-a', HTTP_REFERER='http://testserver/search?q=Example')
        for response in (direct, search_visit):
            self.assertContains(response, 'Invented Researcher')
            self.assertContains(response, 'Example publication')
            self.assertTemplateUsed(response, 'display/profile_data.html')
        self.assertContains(direct, 'href="/search" class="back-to-search"')
        self.assertContains(search_visit, 'href="javascript: history.go(-1)" class="back-to-search"')

    def test_search_session_preserves_cache_headers(self) -> None:
        """
        Checks a successful search keeps its session and cookie-dependent response header.
        """
        responses = page_responses()
        with patch('vivo_app.lib.source_pages.read_source', side_effect=responses.__getitem__):
            response = self.client.get('/search?q=Example')
        assert isinstance(response, HttpResponse)
        self.assertContains(response, 'Invented Researcher')
        self.assertEqual(self.client.session['search_url'], '/search?q=Example')
        self.assertIn('Cookie', response.headers.get('Vary', ''))
