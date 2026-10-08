"""
Checks data routes when Django runs beneath a public URL prefix.
"""

from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase, override_settings


class ScriptPrefixTests(TestCase):
    """Checks the public prefix does not change a route's data lookup path."""

    @override_settings(PAGE_DATA_MODE='live', SOLR_URL='https://example.invalid/solr/example')
    def test_live_homepage_accepts_deployment_prefix(self) -> None:
        """
        Checks the public URL prefix does not become a homepage data variation.
        """
        books = {'backgrounds': ['/static/example.jpg'], 'book_covers_paginated': []}
        with patch('vivo_app.lib.source_books.homepage_books', return_value=books) as source:
            response = self.client.get('/', SCRIPT_NAME='/vivo_on_django')
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'alt="Researchers at Brown"')
        self.assertContains(response, 'role="main"', count=1)
        self.assertNotContains(response, '<main')
        self.assertContains(response, 'Manage your profile')
        source.assert_called_once_with('live')
