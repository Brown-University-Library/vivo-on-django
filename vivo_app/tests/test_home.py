"""
Home page tests for Django VIVO app.

Verifies that the homepage renders and includes key structural markers and links
that we aim to keep aligned with production.
"""

import json
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import reverse

from vivo_app.lib.source_types import SourceResponse


@override_settings(BOOK_COVER_BASE_PATH='/book-images')
class HomePageTests(TestCase):
    """Tests homepage rendering and primary elements."""

    def setUp(self) -> None:
        """
        Supplies made-up book rows without opening the source database.
        """
        rows = [
            {
                'shortID': 'example',
                'firstname': 'Example',
                'lastname': 'Author',
                'title': 'Example Book',
                'image': 'example.jpg',
            }
        ]
        reader = patch(
            'vivo_app.lib.source_books.read_source', return_value=SourceResponse(200, (), json.dumps(rows).encode())
        )
        reader.start()
        self.addCleanup(reader.stop)

    def test_homepage_renders_ok(self) -> None:
        """
        Checks primary sections and the reference's single main landmark.
        """
        resp = self.client.get('/')
        assert isinstance(resp, HttpResponse)
        self.assertEqual(resp.status_code, 200)
        # Key headings/markers
        self.assertContains(resp, 'role="main"', count=1)
        self.assertNotContains(resp, '<main')
        self.assertNotContains(resp, 'Welcome to Researchers@Brown')
        self.assertContains(resp, 'Recent faculty books')
        self.assertContains(resp, 'Search for a Researcher')
        self.assertContains(resp, 'Did You Know?')
        self.assertContains(resp, 'Get a Brown ORCID Identifier!')

    def test_homepage_links(self):
        """
        Contains expected navigation and quick link URLs.
        """
        resp = self.client.get('/')
        assert isinstance(resp, HttpResponse)
        self.assertEqual(resp.status_code, 200)

        # Manage profile link visible on home page
        self.assertContains(resp, 'Manage your profile')

        # Search form target
        self.assertContains(resp, f'action="{reverse("search")}"')

        # Advanced search link text and URL
        self.assertContains(resp, 'Advanced search&hellip;')
        self.assertContains(resp, reverse('advanced_search'))

        # Quick links
        self.assertContains(resp, reverse('people'))
        self.assertContains(resp, reverse('organizations'))
        self.assertContains(resp, reverse('publications'))

        # Footer
        self.assertContains(resp, reverse('terms'))
        self.assertContains(resp, 'vivoweb.org')

    def test_homepage_includes_carousel_markup(self):
        """
        Book carousel renders data-src attributes for lazy loading and anchors.
        """
        resp = self.client.get('/')
        assert isinstance(resp, HttpResponse)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'id="books-carousel"')
        self.assertContains(resp, 'class="book-cover"')
        self.assertContains(resp, 'data-src="/book-images/example.jpg"')

    def test_alias_parameter_redirects_to_search(self):
        """
        Alias parameter redirects to search with the formatted query.
        """
        response = self.client.get('/', {'alias': 'Nicole_Nugent'})
        assert isinstance(response, HttpResponse)
        expected_location: str = f'{reverse("search")}?q=Nicole+Nugent'
        self.assertRedirects(response, expected_location, fetch_redirect_response=False)

    def test_unrelated_query_parameters_do_not_change_homepage_data(self) -> None:
        """
        Checks unrelated parameters render the homepage without reaching the book-source request.
        """
        with patch('vivo_app.lib.source_books.read_source', return_value=SourceResponse(200, (), b'[]')) as source:
            plain = self.client.get('/')
            assert isinstance(plain, HttpResponse)
            self.assertEqual(plain.status_code, 200)
            expected = source.call_args
            for query in ('id=example&r=1', 'rest_route=example', 'utm_source=example&url=other', 'alias='):
                with self.subTest(query=query):
                    source.reset_mock()
                    response = self.client.get('/?' + query)
                    self.assertContains(response, 'Search for a Researcher')
                    source.assert_called_once()
                    self.assertEqual(source.call_args, expected)

    def test_alias_stays_an_encoded_local_search_with_extra_parameters(self) -> None:
        """
        Checks alias text stays inside the local search query and unrelated parameters are discarded.
        """
        alias = 'Example_Name & Other'
        response = self.client.get('/', {'alias': alias, 'utm_source': 'example', 'next': 'other'})
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 302)
        location = urlsplit(response['Location'])
        self.assertEqual(location.scheme, '')
        self.assertEqual(location.netloc, '')
        self.assertEqual(location.path, reverse('search'))
        self.assertEqual(parse_qs(location.query), {'q': ['Example Name & Other']})
