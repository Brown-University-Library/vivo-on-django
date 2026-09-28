"""
Checks the first source-backed journey with made-up records and no network.
"""

import json
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.http import HttpResponse
from django.test import TestCase, override_settings

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RequestKey
from vivo_app.lib.source_pages import publication_html
from vivo_app.lib.source_requests import image_key, profile_key, search_key


@override_settings(
    PAGE_DATA_MODE='live',
    SOLR_URL='http://example.invalid/solr/example',
    IMAGES_URL='http://example.invalid',
)
class SourcePageTests(TestCase):
    """Exercises source parsing, rendering, images, and explicit failures."""

    def setUp(self) -> None:
        """
        Creates response bytes for one invented search-to-profile journey.
        """
        person = {
            'id': 'http://vivo.brown.edu/individual/invented-a',
            'name': 'Invented Researcher',
            'title': 'Example Professor',
            'email': 'invented@example.invalid',
            'overview': '<p>Invented &amp; tested.</p>',
            'affiliations': [{'uri': 'http://vivo.brown.edu/individual/org-example', 'name': 'Example Department'}],
            'on_the_web': [{'url': 'https://example.invalid/person', 'text': 'Website'}],
            'contributor_to': [
                {
                    'type': 'http://vivo.brown.edu/ontology/citation#Article',
                    'title': 'Example publication',
                    'authors': 'Researcher, Invented',
                    'date': '2024-01-01',
                    'published_in': 'Invented Journal',
                    'doi': '10.0000/example',
                }
            ],
            'education': [{'date': '2001', 'degree': 'PhD', 'school_name': 'Example University'}],
            'appointments': [{'name': 'Editor', 'org_name': 'Example Journal', 'start_date': '2020-01-01'}],
            'teacher_for': ['EXMP 1000 - Example Course'],
        }
        person_doc = {
            'id': person['id'],
            'record_type': ['PEOPLE'],
            'json_txt': [json.dumps(person)],
            'display_name_s': 'Invented Researcher',
            'thumbnail_file_path_s': '/file/n1234/portrait.jpg',
        }
        organization_doc = {
            'id': 'http://vivo.brown.edu/individual/org-example',
            'record_type': ['ORGANIZATION'],
            'thumbnail_file_path_s': '/file/n5678/logo.png',
        }
        facets: dict[str, object] = {
            'facet_fields': {
                'record_type': ['PEOPLE', 1],
                'affiliations': ['Example Department', 1],
                'research_areas': [],
                'published_in': ['Invented Journal', 1],
            }
        }
        highlights: dict[str, object] = {
            'vitroIndividual:http://vivo.brown.edu/individual/invented-a': {
                'short_id_s': ['<strong>Example</strong> <script>unsafe</script>']
            }
        }
        self.responses = {
            search_key('Example', 1, []): self.solr_response([person_doc], 1, facets, highlights),
            search_key('Example', 1, [('record_type', 'PEOPLE')]): self.solr_response([person_doc], 1, facets, highlights),
            profile_key('invented-a'): self.solr_response([person_doc], 1),
            profile_key('org-example'): self.solr_response([organization_doc], 1),
            image_key('/profile-images/123/4/portrait.jpg'): RecordedResponse(
                200, (('content-type', 'image/jpeg'),), b'invented-portrait'
            ),
            image_key('/profile-images/567/8/logo.png'): RecordedResponse(
                200, (('content-type', 'image/png'),), b'invented-logo'
            ),
        }

    def solr_response(
        self,
        docs: list[dict[str, object]],
        count: int,
        facets: dict[str, object] | None = None,
        highlights: dict[str, object] | None = None,
    ) -> RecordedResponse:
        """
        Makes a complete Solr response from invented documents.

        Called by: setUp()
        """
        data: dict[str, object] = {'responseHeader': {'status': 0}, 'response': {'numFound': count, 'docs': docs}}
        if facets is not None:
            data['facet_counts'] = facets
        if highlights is not None:
            data['highlighting'] = highlights
        return RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(data).encode())

    def read(self, key: RequestKey, mode: str) -> RecordedResponse:
        """
        Supplies one exact invented response and fails on any other request.

        Called by: test methods through the source modules
        """
        self.assertEqual(mode, 'live')
        if key not in self.responses:
            raise PageDataError('No invented response matches this request.')
        return self.responses[key]

    def get_page(self, url: str) -> HttpResponse:
        """
        Requests a local page with the configured accepted host.

        Called by: test methods
        """
        response = self.client.get(url, SERVER_NAME='127.0.0.1')
        assert isinstance(response, HttpResponse)
        return response

    def test_search_profile_and_images_use_only_invented_responses(self) -> None:
        """
        Checks a search, person page, affiliation lookup, and both images without network access.
        """
        with (
            patch('vivo_app.lib.source_pages.read_source', side_effect=self.read),
            patch('vivo_app.views.read_source', side_effect=self.read),
            patch('socket.socket.connect', side_effect=AssertionError('Unexpected network connection')),
        ):
            search = self.get_page('/search?q=Example')
            self.assertContains(search, 'Invented Researcher')
            self.assertContains(search, '/display/invented-a')
            self.assertContains(search, 'Example Department')
            self.assertContains(search, 'Search matches')
            self.assertNotContains(search, '<script>unsafe</script>')
            filtered = self.get_page('/search?q=Example&fq=record_type%7CPEOPLE')
            self.assertContains(filtered, 'Remove filter PEOPLE')
            profile = self.get_page('/display/invented-a')
            self.assertContains(profile, 'Example publication')
            self.assertContains(profile, 'Example University')
            self.assertContains(profile, 'EXMP 1000')
            self.assertContains(profile, '/source-images/profile-images/567/8/logo.png')
            picture = self.get_page('/source-images/profile-images/123/4/portrait.jpg')
            self.assertEqual(picture.content, b'invented-portrait')
            self.assertEqual(picture['Content-Type'], 'image/jpeg')
            self.assertEqual(self.get_page('/source-images/profile-images/567/8/logo.png').status_code, 200)

    def test_missing_response_and_unsupported_option_do_not_fall_back(self) -> None:
        """
        Checks missing source data and unsupported requests fail without sample content.
        """
        with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
            self.assertEqual(self.get_page('/search?q=Other').status_code, 503)
            self.assertEqual(self.get_page('/search?q=Example&format=json').status_code, 503)
            self.assertEqual(self.get_page('/display/other').status_code, 503)
            self.assertEqual(self.get_page('/display/invented-a/publications/').status_code, 503)
            self.assertEqual(self.get_page('/').status_code, 503)

    def test_publication_title_joins_venue_without_extra_comma(self) -> None:
        """
        Checks source citation punctuation matches the public display format.
        """
        markup = publication_html({'title': 'Example work', 'published_in': 'Invented Journal', 'date': '2024'})
        self.assertIn('"Example work." <i>Invented Journal</i>, 2024.', markup)

    def test_capture_requires_profile_in_search_results(self) -> None:
        """
        Checks capture rejects an unrelated profile before writing any files.
        """
        with (
            patch('vivo_app.management.commands.capture_solr_journey.read_source', side_effect=self.read),
            patch('vivo_app.management.commands.capture_solr_journey.write_capture') as writer,
        ):
            with self.assertRaises(CommandError) as caught:
                call_command('capture_solr_journey', query='Example', id='other', output=Path('/tmp/unused-capture'))
            self.assertIn('not in the captured search results', str(caught.exception))
            writer.assert_not_called()
