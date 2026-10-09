"""
Checks the first source-backed journey with made-up records and no network.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import get_script_prefix, set_script_prefix
from django.utils import translation

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RequestKey
from vivo_app.lib.source_formats import (
    faculty_item_from_doc,
    organization_json_data,
    profile_json_data,
    profile_json_text,
    publication_entries,
)
from vivo_app.lib.source_graph import visualization_key
from vivo_app.lib.source_pages import (
    entries,
    facet_values_data,
    match_html,
    organization_data,
    organization_publications_data,
    profile_data,
    profile_sections,
    profile_year_range,
    publication_citation,
    publication_export_type,
    publication_html,
    publications,
    safe_match_text,
    search_data,
    search_json_data,
    selected_highlights,
    thumbnail_url,
)
from vivo_app.lib.source_requests import (
    community_research_members_key,
    document_key,
    image_key,
    member_details_key,
    member_key,
    profile_export_key,
    profile_key,
    search_key,
    team_member_key,
)
from vivo_app.lib.source_teams import custom_organization_members, team_data


@override_settings(
    PAGE_DATA_MODE='live',
    SOLR_URL='http://example.invalid/solr/example',
    IMAGES_URL='http://example.invalid',
    DOCUMENTS_URL='https://example.invalid',
    VIZ_ENABLED=True,
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
            'overview': '<p>Invented &amp; tested. <a href="https://example.invalid/lab">Example lab</a></p>',
            'affiliations': [{'uri': 'http://vivo.brown.edu/individual/org-example', 'name': 'Example Department'}],
            'research_areas': ['liver', 'Excretion', 'absorption'],
            'on_the_web': [{'url': 'https://example.invalid/person', 'text': 'Website'}],
            'contributor_to': [
                {
                    'type': 'http://vivo.brown.edu/ontology/citation#Article',
                    'title': 'Example publication',
                    'authors': 'Researcher, Invented',
                    'date': '2024-01-01',
                    'published_in': 'Invented Journal',
                    'doi': '10.0000/example',
                    'pub_med_id': '12345678',
                }
            ],
            'education': [{'date': '2001', 'degree': 'PhD', 'school_name': 'Example University'}],
            'awards': '<ul><li>Example <a href="https://example.invalid/award">Award</a></li></ul>',
            'appointments': [{'name': 'Editor', 'org_name': 'Example Journal', 'start_date': '2020-01-01'}],
            'teacher_for': ['EXMP 1000 - Example Course'],
            'cv': [{'cv_link': 'http://example.invalid/docs/i/invented_cv.pdf?dt=1'}],
        }
        person_doc = {
            'id': person['id'],
            'record_type': ['PEOPLE'],
            'json_txt': [json.dumps(person)],
            'display_name_s': 'Invented Researcher',
            'show_visualizations_s': 'true',
            'thumbnail_file_path_s': '/file/n1234/portrait.jpg',
        }
        organization_doc = {
            'id': 'http://vivo.brown.edu/individual/org-example',
            'record_type': ['ORGANIZATION'],
            'thumbnail_file_path_s': '/file/n5678/logo.png',
            'json_txt': [
                json.dumps(
                    {
                        'name': 'Example Department',
                        'overview': '<p><strong>Invented department</strong></p><script>unsafe()</script>',
                        'people': [
                            {
                                'faculty_uri': person['id'],
                                'label': 'Researcher, Invented',
                                'specific_position': 'Example Professor',
                                'general_position': 'http://vivoweb.org/ontology/core#FacultyPosition',
                            }
                        ],
                        'web_pages': [{'url': 'https://example.invalid/department', 'text': 'Department website'}],
                    }
                )
            ],
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
            search_key('Example', 1, [], -1): self.solr_response([person_doc], 1, facets, highlights),
            search_key('Example', 1, [('record_type', 'PEOPLE')], -1): self.solr_response(
                [person_doc], 1, facets, highlights
            ),
            search_key('none', 1, []): self.solr_response(
                [],
                0,
                {'facet_fields': {field: [] for field in ('record_type', 'affiliations', 'research_areas', 'published_in')}},
            ),
            search_key('none', 1, [], -1): self.solr_response(
                [],
                0,
                {'facet_fields': {field: [] for field in ('record_type', 'affiliations', 'research_areas', 'published_in')}},
            ),
            search_key('Example', 2, []): self.solr_response([person_doc], 21, facets),
            search_key(
                'Example', 1, [('record_type', 'PEOPLE'), ('affiliations', 'Example Department')]
            ): self.solr_response([person_doc], 1, facets),
            profile_key('invented-a'): self.solr_response([person_doc], 1),
            visualization_key('coauthors'): RecordedResponse(
                200, (('content-type', 'application/json'),), json.dumps({person['id']: True}).encode()
            ),
            profile_key('org-example'): self.solr_response([organization_doc], 1),
            member_key(['invented-a']): self.solr_response([person_doc], 1),
            member_details_key(['invented-a']): self.solr_response([person_doc], 1),
            team_member_key(['invented-a']): self.solr_response([person_doc], 1),
            image_key('/profile-images/123/4/portrait.jpg'): RecordedResponse(
                200, (('content-type', 'image/jpeg'),), b'invented-portrait'
            ),
            image_key('/profile-images/567/8/logo.png'): RecordedResponse(
                200, (('content-type', 'image/png'),), b'invented-logo'
            ),
            document_key('/docs/i/invented_cv.pdf', (('dt', '1'),)): RecordedResponse(
                200, (('content-type', 'application/pdf'),), b'%PDF-1.7 invented document'
            ),
            document_key('/docs/i/invented_cv.pdf'): RecordedResponse(
                301,
                (('content-type', 'text/html'), ('location', 'https://example.invalid/docs/i/invented_cv.pdf?dt=1')),
                b'',
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

    def read_replay(self, key: RequestKey, mode: str) -> RecordedResponse:
        """
        Reads the same exact responses while checking replay failures.

        Called by: test_profile_still_loads_when_coauthor_list_is_unavailable(), test_sparse_profile_json_uses_graph_availability()
        """
        self.assertEqual(mode, 'replay')
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

    def test_profile_lookup_requests_visualization_setting(self) -> None:
        """
        Checks Solr is asked for the field that controls the coauthor link.
        """
        fields = dict(profile_key('invented-a').query)['fl'].split(',')
        self.assertIn('show_visualizations_s', fields)

    def test_hidden_profile_marks_name_inactive(self) -> None:
        """
        Checks the public inactive marker appears only for hidden profiles.
        """
        with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
            visible = self.get_page('/display/invented-a')
        self.assertNotContains(visible, 'Invented Researcher [Inactive]')
        key = profile_key('invented-a')
        response = json.loads(self.responses[key].body)
        person = json.loads(response['response']['docs'][0]['json_txt'][0])
        person['hidden'] = True
        response['response']['docs'][0]['json_txt'] = [json.dumps(person)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
            inactive = self.get_page('/display/invented-a')
        self.assertContains(inactive, 'Invented Researcher [Inactive]')

    def test_background_shows_training_rows(self) -> None:
        """
        Checks training appears newest first, with organization and location text safely escaped.
        """
        item: dict[str, object] = {
            'training': [
                {'name': 'Earlier training', 'start_date': '2001-01-01', 'end_date': '2003-01-01'},
                {
                    'name': 'Later training',
                    'start_date': '2010-01-01T00:00:00',
                    'org_name': 'Example University',
                    'hospital_name': 'Example Hospital',
                    'city': 'Providence',
                    'state': '<Unsafe>',
                },
                {'name': 'Undated training'},
                {'name': 'Another undated training'},
            ]
        }
        background = next(
            section['html'] for section in profile_sections(item, 'live', self.read, 0, '') if section['id'] == 'Background'
        )
        self.assertIn('Postdoctoral/Other Training', background)
        self.assertLess(background.index('Later training'), background.index('Earlier training'))
        self.assertLess(background.index('Earlier training'), background.index('Another undated training'))
        self.assertLess(background.index('Another undated training'), background.index('Undated training'))
        self.assertIn('Example University, Example Hospital', background)
        self.assertIn('2010-</td><td>Providence, &lt;Unsafe&gt;', background)
        self.assertIn('2001-2003', background)
        self.assertNotIn('<Unsafe>', background)

    def test_background_reverses_education_rows_with_same_year(self) -> None:
        """
        Checks degrees in the same year appear in the order shown by Rails.
        """
        item: dict[str, object] = {
            'education': [
                {'date': '2001', 'degree': 'BS', 'school_name': 'Example University'},
                {'date': '2001', 'degree': 'MS', 'school_name': 'Example University'},
                {'date': '2005', 'degree': 'PhD', 'school_name': 'Another University'},
            ]
        }
        background = next(
            section['html'] for section in profile_sections(item, 'live', self.read, 0, '') if section['id'] == 'Background'
        )
        self.assertLess(background.index('PhD'), background.index('MS'))
        self.assertLess(background.index('MS'), background.index('BS'))

    def test_background_trims_school_names_and_search_links(self) -> None:
        """
        Checks a padded school name appears cleanly in both the table and its search link.
        """
        item: dict[str, object] = {'education': [{'date': '2001', 'degree': 'PhD', 'school_name': '  Example University  '}]}
        background = next(
            section['html'] for section in profile_sections(item, 'live', self.read, 0, '') if section['id'] == 'Background'
        )
        self.assertIn('q=alumni_of%3A%22Example+University%22', background)
        self.assertIn('>Example University</a>', background)
        self.assertNotIn('  Example University  ', background)

    def test_organization_trims_website_urls_and_labels(self) -> None:
        """
        Checks organization website links have the same trimmed values as Rails.
        """
        key = profile_key('org-example')
        response = json.loads(self.responses[key].body)
        item = json.loads(response['response']['docs'][0]['json_txt'][0])
        item['web_pages'] = [{'url': '  https://example.invalid/department  ', 'text': '  Department website  '}]
        response['response']['docs'][0]['json_txt'] = [json.dumps(item)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        organization = organization_data('org-example', 'live', self.read)
        self.assertEqual(
            organization['website_links'], [{'url': 'https://example.invalid/department', 'label': 'Department website'}]
        )

    def test_organization_keeps_empty_overview_paragraph(self) -> None:
        """
        Checks an empty organization overview retains the paragraph used by Rails for spacing.
        """
        key = profile_key('org-example')
        response = json.loads(self.responses[key].body)
        item = json.loads(response['response']['docs'][0]['json_txt'][0])
        item['overview'] = ''
        response['response']['docs'][0]['json_txt'] = [json.dumps(item)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        organization = organization_data('org-example', 'live', self.read)
        self.assertEqual(organization['overview_html'], '<p></p>')
        with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
            result = self.get_page('/display/org-example')
        self.assertContains(result, '<div class="organization-overview"><p></p></div>', html=True)

    def test_organization_preview_preserves_coordinate_precision(self) -> None:
        """
        Checks the rendered decorative SVG retains full reference decimals in either locale.
        """
        for language in ('en', 'fr'):
            with self.subTest(language=language), translation.override(language):
                with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
                    result = self.get_page('/display/org-example')
                self.assertContains(
                    result,
                    '<line x1="502.673652104801" y1="350.68520459323065" '
                    'x2="402.7251593479398" y2="416.5887723542673" '
                    'style="stroke: rgb(204, 204, 204); stroke-width: 1;"></line>',
                    html=True,
                )
                self.assertContains(result, 'transform="translate(429.54751433822946,302.8619812431097)"')

    def test_organization_websites_preserve_source_order(self) -> None:
        """
        Checks organization website links keep source order even when ranks differ.
        """
        key = profile_key('org-example')
        response = json.loads(self.responses[key].body)
        item = json.loads(response['response']['docs'][0]['json_txt'][0])
        item['web_pages'] = [
            {'rank': '2', 'url': 'https://example.invalid/later'},
            {'rank': '1', 'url': 'https://example.invalid/earlier'},
        ]
        response['response']['docs'][0]['json_txt'] = [json.dumps(item)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        organization = organization_data('org-example', 'live', self.read)
        websites = organization['website_links']
        self.assertIsInstance(websites, list)
        if not isinstance(websites, list):
            self.fail('Organization websites were not a list.')
        self.assertEqual(
            [row['url'] for row in websites], ['https://example.invalid/later', 'https://example.invalid/earlier']
        )

    def test_research_keeps_source_formatting(self) -> None:
        """
        Checks the Research text keeps paragraphs, emphasis, and web links while discarding active markup.
        """
        item: dict[str, object] = {
            'research_overview': '<p>Studies <em>RNA</em> at the <a href="https://example.invalid/lab">lab</a>.</p>',
            'research_statement': '<p>Second paragraph.</p><script>unsafe()</script>',
        }
        research = next(
            section['html'] for section in profile_sections(item, 'live', self.read, 0, '') if section['id'] == 'Research'
        )
        self.assertIn('<p>Studies <em>RNA</em> at the <a href="https://example.invalid/lab">lab</a>.</p>', research)
        self.assertIn('<p>Second paragraph.</p>', research)
        self.assertNotIn('unsafe()', research)

    def test_profile_websites_follow_saved_rank(self) -> None:
        """
        Checks website links follow rank, including decimal ranks and ties.
        """
        item: dict[str, object] = {
            'on_the_web': [
                {'url': 'https://example.invalid/last', 'text': 'Last website', 'rank': '3'},
                {'url': 'https://example.invalid/first', 'text': 'First website', 'rank': '0.25'},
                {'url': 'https://example.invalid/tied', 'text': 'Tied website', 'rank': 0},
                {'url': 'https://example.invalid/middle', 'text': 'Middle website', 'rank': '1'},
            ]
        }
        overview = next(
            section['html'] for section in profile_sections(item, 'live', self.read, 0, '') if section['id'] == 'Overview'
        )
        self.assertLess(overview.index('First website'), overview.index('Tied website'))
        self.assertLess(overview.index('Tied website'), overview.index('Middle website'))
        self.assertLess(overview.index('Middle website'), overview.index('Last website'))

    def test_profile_websites_trim_saved_urls_and_labels(self) -> None:
        """
        Checks website URLs and labels lose outer spaces before appearing in a profile.
        """
        item: dict[str, object] = {
            'on_the_web': [
                {'url': '  https://example.invalid/web  ', 'text': ' Example link  '},
                {'url': 'https://example.invalid/unnamed'},
            ]
        }
        overview = next(
            section['html'] for section in profile_sections(item, 'live', self.read, 0, '') if section['id'] == 'Overview'
        )
        self.assertIn('href="https://example.invalid/web"', overview)
        self.assertIn('>Example link</a>', overview)
        self.assertIn('>https://example.invalid/unnamed</a>', overview)
        self.assertNotIn('href="  https://', overview)

    def test_teaching_overview_keeps_source_formatting(self) -> None:
        """
        Checks Teaching Overview keeps line breaks and bold text without active markup.
        """
        item: dict[str, object] = {
            'teaching_overview': '<p><strong>Courses taught:<br>Example Biology</strong></p><script>unsafe()</script>'
        }
        teaching = next(
            section['html'] for section in profile_sections(item, 'live', self.read, 0, '') if section['id'] == 'Teaching'
        )
        self.assertIn('<div class="property-list" role="list" displaylimit="5">', teaching)
        self.assertIn('<p><strong>Courses taught:<br>Example Biology</strong></p>', teaching)
        self.assertNotIn('unsafe()', teaching)

    def test_affiliations_show_credentials(self) -> None:
        """
        Checks credentials appear newest first, with missing fields and source text handled safely.
        """
        item: dict[str, object] = {
            'credentials': [
                {'name': 'Earlier license', 'start_date': '2001-01-01', 'end_date': '2004-01-01'},
                {
                    'name': 'Later license',
                    'start_date': '2015-01-01',
                    'grantor_name': 'state board',
                    'specialty_name': 'psychology',
                    'number': 'LIC-123',
                },
                {'name': '<Undated license>'},
                {'name': 'Another undated license'},
            ]
        }
        affiliations = next(
            section['html']
            for section in profile_sections(item, 'live', self.read, 0, '')
            if section['id'] == 'Affiliations'
        )
        self.assertIn('Credentials/Licenses', affiliations)
        self.assertLess(affiliations.index('Later license'), affiliations.index('Earlier license'))
        self.assertLess(affiliations.index('Earlier license'), affiliations.index('Another undated license'))
        self.assertLess(affiliations.index('Another undated license'), affiliations.index('&lt;Undated license&gt;'))
        self.assertIn('State board, Psychology</td><td>2015-</td><td>#LIC-123', affiliations)
        self.assertIn('2001-2004', affiliations)
        self.assertNotIn('<Undated license>', affiliations)

    def test_appointments_show_hospital_and_department_without_empty_link(self) -> None:
        """
        Checks appointment rows prefer the hospital, show departments, and skip links when no organization exists.
        """
        item: dict[str, object] = {
            'appointments': [
                {'name': 'Older role', 'start_date': '2001-01-01'},
                {
                    'name': 'Hospital role',
                    'hospital_name': 'Example Hospital',
                    'org_name': 'Unused Organization',
                    'start_date': '2018-01-01',
                },
                {'name': 'Department role', 'department': 'Example Division', 'start_date': '2010-01-01'},
            ]
        }
        affiliations = next(
            section['html']
            for section in profile_sections(item, 'live', self.read, 0, '')
            if section['id'] == 'Affiliations'
        )
        self.assertLess(affiliations.index('Hospital role'), affiliations.index('Department role'))
        self.assertLess(affiliations.index('Department role'), affiliations.index('Older role'))
        self.assertIn('>Example Hospital</a>,', affiliations)
        self.assertNotIn('Unused Organization', affiliations)
        self.assertIn('Department role</span>. <span>Example Division</span>', affiliations)
        self.assertIn('Older role</span>. <span>2001-</span>', affiliations)
        self.assertNotIn('q=%22%22', affiliations)

    def test_search_keeps_reference_parser_defaults_and_all_term_operator(self) -> None:
        """
        Checks ordinary, combined, and empty searches retain reference request options.
        """
        for query in ('Example', 'Example researcher', '*', ''):
            with self.subTest(query=query):
                key = search_key(query, 2, [('record_type', 'PEOPLE')])
                self.assertIn(('q.op', 'AND'), key.query)
                self.assertNotIn('defType', dict(key.query))
                self.assertIn(('start', '20'), key.query)
                self.assertIn(('fq', 'record_type:"PEOPLE"'), key.query)
                self.assertIn(('mm', '2<75%'), key.query)

    def test_profile_year_ranges_keep_missing_date_separators(self) -> None:
        """
        Checks open and absent date ranges retain the reference separator.
        """
        self.assertEqual(profile_year_range({}), '-')
        self.assertEqual(profile_year_range({'start_date': '2001-01-01'}), '2001-')
        self.assertEqual(profile_year_range({'end_date': '2005-01-01'}), '-2005')
        self.assertEqual(profile_year_range({'start_date': 'invalid'}), '-')
        self.assertEqual(profile_year_range({'start_date': '2001-01-01', 'end_date': '2005-01-01'}), '2001-2005')
        self.assertEqual(profile_year_range({'start_date': '2001-01-01', 'end_date': '2200-01-01'}), '2001-Present')

    def test_affiliations_text_keeps_source_links(self) -> None:
        """
        Checks Affiliations text keeps web links and line breaks without unsafe destinations.
        """
        item: dict[str, object] = {
            'affiliations_text': (
                '<a href="https://example.invalid/society">Example Society</a><br>'
                '<a href="javascript:unsafe()">Unsafe destination</a>'
            )
        }
        affiliations = next(
            section['html']
            for section in profile_sections(item, 'live', self.read, 0, '')
            if section['id'] == 'Affiliations'
        )
        self.assertIn('<div class="property-list" role="list" displaylimit="5">', affiliations)
        self.assertIn('<a href="https://example.invalid/society">Example Society</a><br>', affiliations)
        self.assertIn('Unsafe destination', affiliations)
        self.assertNotIn('javascript:', affiliations)

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
            self.assertContains(search, '&copy; 2017')
            self.assertContains(search, '/css/public.css')
            self.assertContains(search, '/css/individual.css')
            self.assertContains(search, '/display/invented-a')
            self.assertContains(search, 'Example Department')
            self.assertContains(search, 'Search matches')
            self.assertNotContains(search, '<script>unsafe</script>')
            filtered = self.get_page('/search?q=Example&fq=record_type%7CPEOPLE')
            self.assertContains(filtered, 'Remove filter PEOPLE')
            profile = self.get_page('/display/invented-a')
            self.assertContains(profile, 'Example publication')
            self.assertContains(profile, 'http://www.ncbi.nlm.nih.gov/pubmed/?term=12345678')
            self.assertContains(profile, 'Example University')
            self.assertContains(profile, '<a href="https://example.invalid/lab">Example lab</a>')
            self.assertContains(profile, '<a href="https://example.invalid/award">Award</a>')
            self.assertContains(profile, 'EXMP 1000')
            self.assertContains(profile, '/source-images/profile-images/567/8/logo.png')
            self.assertContains(profile, '/source-documents/docs/i/invented_cv.pdf?dt=1')
            self.assertContains(profile, 'id="viz_coauthor"')
            self.assertContains(profile, 'href="/display/invented-a/viz/coauthor"')
            picture = self.get_page('/source-images/profile-images/123/4/portrait.jpg')
            self.assertEqual(picture.content, b'invented-portrait')
            self.assertEqual(picture['Content-Type'], 'image/jpeg')
            self.assertEqual(self.get_page('/source-images/profile-images/567/8/logo.png').status_code, 200)
            organization = self.get_page('/display/org-example')
            self.assertContains(organization, 'Invented department')
            self.assertContains(organization, '<strong>Invented department</strong>')
            self.assertNotContains(organization, 'unsafe()')
            self.assertContains(organization, 'Researcher, Invented')
            self.assertContains(organization, '/display/org-example/viz/collab')
            self.assertContains(organization, '/source-images/profile-images/123/4/portrait.jpg')
            facet = self.get_page('/search_facets?q=Example&f_name=record_type')
            facet_rows = json.loads(facet.content)
            self.assertEqual(facet_rows[0]['text'], 'PEOPLE')
            self.assertEqual(facet_rows[0]['add_url'], '/search?q=Example&fq=record_type%7CPEOPLE')
            selected = self.get_page('/search_facets?q=Example&fq=record_type%7CPEOPLE&f_name=record_type')
            self.assertEqual(json.loads(selected.content)[0]['remove_url'], '/search?q=Example')
            redirect = self.get_page('/source-documents/docs/i/invented_cv.pdf')
            self.assertEqual(redirect.status_code, 301)
            self.assertEqual(redirect['Location'], '/source-documents/docs/i/invented_cv.pdf?dt=1')
            document = self.get_page(redirect['Location'])
            self.assertEqual(document['Content-Type'], 'application/pdf')
            self.assertTrue(document.content.startswith(b'%PDF-'))
            part = self.client.get(redirect['Location'], SERVER_NAME='127.0.0.1', HTTP_RANGE='bytes=0-4')
            assert isinstance(part, HttpResponse)
            self.assertEqual(part.status_code, 206)
            self.assertEqual(part.content, b'%PDF-')
            self.assertEqual(part['Content-Range'], f'bytes 0-4/{len(document.content)}')

    def test_search_title_length_matches_in_html_and_json(self) -> None:
        """
        Checks fifty-character titles stay whole and longer titles retain forty-eight characters before the ellipsis.
        """
        key = search_key('Example', 1, [])
        for title, expected in (('Short title', 'Short title'), ('É' * 50, 'É' * 50), ('É' * 48 + 'XYZ', 'É' * 48 + '...')):
            with self.subTest(title=title):
                response = json.loads(self.responses[key].body)
                document = response['response']['docs'][0]
                record = json.loads(document['json_txt'][0])
                record['title'] = title
                document['json_txt'] = [json.dumps(record)]
                self.responses[key] = RecordedResponse(
                    200, (('content-type', 'application/json'),), json.dumps(response).encode()
                )
                html = search_data([('q', 'Example')], 'live', self.read)
                items = html['results']
                assert isinstance(items, list)
                self.assertEqual(items[0]['title'], expected)
                data = search_json_data([('q', 'Example')], 'live', 'https://example.invalid', self.read)
                self.assertEqual(data[0]['title'], expected)

    def test_live_search_links_keep_the_deployment_prefix(self) -> None:
        """
        Checks search links, profile images, and JSON destinations stay inside a mounted Django application.
        """
        prefix = '/mounted-app'
        previous_prefix = get_script_prefix()
        set_script_prefix(prefix)
        try:
            with (
                patch('vivo_app.lib.source_pages.read_source', side_effect=self.read),
                patch('vivo_app.views.read_source', side_effect=self.read),
            ):
                search = self.client.get('/search?q=Example', SCRIPT_NAME=prefix)
                self.assertContains(search, f'action="{prefix}/search"')
                self.assertContains(search, f'href="{prefix}/search/advanced?q=Example"')
                self.assertContains(search, f'href="{prefix}/display/invented-a"')
                self.assertContains(search, f'href="{prefix}/search?q=Example')
                self.assertContains(search, f'src="{prefix}/source-images/profile-images/123/4/portrait.jpg"')
                image = self.client.get('/source-images/profile-images/123/4/portrait.jpg', SCRIPT_NAME=prefix)
                assert isinstance(image, HttpResponse)
                self.assertEqual(image.status_code, 200)
                self.assertEqual(image.content, b'invented-portrait')
                response = self.client.get('/search?q=Example&format=json', SCRIPT_NAME=prefix)
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(json.loads(response.content)[0]['uri'], f'http://testserver{prefix}/display/invented-a')
        finally:
            set_script_prefix(previous_prefix)

    def test_live_profile_and_organization_links_keep_the_deployment_prefix(self) -> None:
        """
        Checks person and organization links stay inside a mounted Django application.
        """
        prefix = '/mounted-app'
        previous_prefix = get_script_prefix()
        set_script_prefix(prefix)
        try:
            with (
                patch('vivo_app.lib.source_pages.read_source', side_effect=self.read),
                patch('vivo_app.views.read_source', side_effect=self.read),
            ):
                profile = self.client.get('/display/invented-a', SCRIPT_NAME=prefix)
                self.assertContains(profile, f'href="{prefix}/display/org-example"')
                self.assertContains(profile, f'href="{prefix}/search?q=%22Example+Journal%22"')
                self.assertContains(profile, f'href="{prefix}/search?q=alumni_of%3A%22Example+University%22"')
                self.assertContains(profile, f'href="{prefix}/search" class="back-to-search"')
                self.assertContains(profile, f'href="{prefix}/source-documents/docs/i/invented_cv.pdf?dt=1"')
                self.assertContains(profile, f'href="{prefix}/display/invented-a/viz/coauthor"')
                document_redirect = self.client.get('/source-documents/docs/i/invented_cv.pdf', SCRIPT_NAME=prefix)
                assert isinstance(document_redirect, HttpResponse)
                self.assertEqual(document_redirect['Location'], f'{prefix}/source-documents/docs/i/invented_cv.pdf?dt=1')
                organization = self.client.get('/display/org-example', SCRIPT_NAME=prefix)
                self.assertContains(organization, f'href="{prefix}/display/invented-a"')
                self.assertContains(organization, f'href="{prefix}/display/org-example/viz/collab"')
        finally:
            set_script_prefix(previous_prefix)

    def test_profile_still_loads_when_coauthor_list_is_unavailable(self) -> None:
        """
        Checks the optional visualization link disappears without hiding the profile.
        """
        self.responses.pop(visualization_key('coauthors'))
        with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
            profile = self.get_page('/display/invented-a')
        self.assertEqual(profile.status_code, 200)
        self.assertContains(profile, 'Invented Researcher')
        self.assertNotContains(profile, 'id="viz_coauthor"')
        with self.assertRaises(PageDataError):
            profile_data('invented-a', 'replay', self.read_replay)

    def test_affiliations_show_collaborators_and_available_graph(self) -> None:
        """
        Checks collaborator names, local links, and graph availability on a person page.
        """
        key = profile_key('invented-a')
        response = json.loads(self.responses[key].body)
        person = json.loads(response['response']['docs'][0]['json_txt'][0])
        person['collaborators'] = [
            {
                'uri': 'http://vivo.brown.edu/individual/invented-b',
                'name': 'Zeta Colleague',
                'title': 'Example Scientist',
            },
            {'uri': 'http://vivo.brown.edu/individual/invented-c', 'name': 'Alpha Colleague'},
        ]
        response['response']['docs'][0]['json_txt'] = [json.dumps(person)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        self.responses[visualization_key('collaborators')] = RecordedResponse(
            200, (('content-type', 'application/json'),), json.dumps({person['id']: True}).encode()
        )
        prefix = '/mounted-app'
        previous_prefix = get_script_prefix()
        set_script_prefix(prefix)
        try:
            with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
                profile = self.client.get('/display/invented-a', SCRIPT_NAME=prefix)
            assert isinstance(profile, HttpResponse)
            self.assertContains(profile, 'Zeta Colleague')
            self.assertContains(profile, 'Alpha Colleague')
            self.assertLess(profile.content.index(b'Alpha Colleague'), profile.content.index(b'Zeta Colleague'))
            self.assertContains(profile, 'Example Scientist')
            self.assertContains(profile, f'href="{prefix}/display/invented-b"')
            self.assertContains(profile, f'href="{prefix}/display/invented-a/viz/collab"')
            self.assertContains(profile, 'id="viz_collab"')
            self.responses.pop(visualization_key('collaborators'))
            with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
                profile_without_graph = self.client.get('/display/invented-a', SCRIPT_NAME=prefix)
            self.assertContains(profile_without_graph, 'Zeta Colleague')
            self.assertNotContains(profile_without_graph, 'id="viz_collab"')
        finally:
            set_script_prefix(previous_prefix)

    def test_live_search_offers_more_facets_when_an_eleventh_value_exists(self) -> None:
        """
        Checks ten values stay visible and the full local facet response supplies the dialog.
        """
        values = [entry for number in range(1, 12) for entry in (f'Area {number:02}', 12 - number)]
        search = search_key('Example', 1, [])
        full = search_key('Example', 1, [], -1)
        for key in (search, full):
            response = json.loads(self.responses[key].body)
            response['facet_counts']['facet_fields']['affiliations'] = values
            self.responses[key] = RecordedResponse(
                200, (('content-type', 'application/json'),), json.dumps(response).encode()
            )
        prefix = '/mounted-app'
        previous_prefix = get_script_prefix()
        set_script_prefix(prefix)
        try:
            with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
                page = self.client.get('/search?q=Example', SCRIPT_NAME=prefix)
                self.assertContains(page, 'Area 10')
                self.assertNotContains(page, 'Area 11')
                self.assertContains(page, 'modal_form_affiliations')
                self.assertContains(page, f'data-facet-url="{prefix}/search_facets?q=Example&amp;f_name=affiliations"')
                details = self.client.get('/search_facets?q=Example&f_name=affiliations', SCRIPT_NAME=prefix)
                assert isinstance(details, HttpResponse)
                rows = json.loads(details.content)
                self.assertEqual(len(rows), 11)
                self.assertEqual(rows[-1]['text'], 'Area 11')
                self.assertEqual(rows[-1]['add_url'], f'{prefix}/search?q=Example&fq=affiliations%7CArea+11')
                response = json.loads(self.responses[search].body)
                response['facet_counts']['facet_fields']['affiliations'] = values[:-2]
                self.responses[search] = RecordedResponse(
                    200, (('content-type', 'application/json'),), json.dumps(response).encode()
                )
                ten_values = self.client.get('/search?q=Example', SCRIPT_NAME=prefix)
                self.assertNotContains(ten_values, 'modal_form_affiliations')
        finally:
            set_script_prefix(previous_prefix)

    def test_varied_search_and_sparse_profile_states(self) -> None:
        """
        Checks empty results, later pages, repeated filters, and a person with no optional fields.
        """
        sparse_doc = {
            'id': 'http://vivo.brown.edu/individual/invented-sparse',
            'record_type': ['PEOPLE'],
            'json_txt': [json.dumps({'name': 'Sparse Researcher'})],
        }
        self.responses[profile_key('invented-sparse')] = self.solr_response([sparse_doc], 1)
        empty = search_data([('q', 'none')], 'live', self.read)
        self.assertEqual(empty['results'], [])
        self.assertEqual(empty['start'], 1)
        with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
            empty_page = self.get_page('/search?q=none')
        self.assertContains(empty_page, '<span id="search-page-start">1</span>')
        self.assertContains(empty_page, '<span id="search-page-end">0</span>')
        later = search_data([('q', 'Example'), ('page', '2')], 'live', self.read)
        self.assertEqual((later['start'], later['end']), (21, 21))
        pagination = later['pagination']
        self.assertIsInstance(pagination, list)
        if not isinstance(pagination, list):
            self.fail('Search pagination was not a list.')
        self.assertEqual(len(pagination), 2)
        repeated = search_data(
            [('q', 'Example'), ('fq', 'record_type|PEOPLE'), ('fq', 'affiliations|Example Department')],
            'live',
            self.read,
        )
        selected_filters = repeated['selected_filters']
        self.assertIsInstance(selected_filters, list)
        if not isinstance(selected_filters, list):
            self.fail('Selected search filters were not a list.')
        self.assertEqual(len(selected_filters), 2)
        repeated_pagination = repeated['pagination']
        if not isinstance(repeated_pagination, list):
            self.fail('Search pagination was not a list.')
        self.assertEqual(
            repeated_pagination[0]['url'],
            '/search?q=Example&fq=record_type%7CPEOPLE&fq=affiliations%7CExample+Department&page=1',
        )
        sparse = profile_data('invented-sparse', 'live', self.read)
        sections = sparse['sections']
        self.assertIsInstance(sections, list)
        if not isinstance(sections, list):
            self.fail('Profile sections were not a list.')
        self.assertEqual([section['id'] for section in sections], ['Overview'])
        panels = sparse['panels']
        if not isinstance(panels, list):
            self.fail('Profile panels were not a list.')
        self.assertEqual([panel['id'] for panel in panels], ['Overview', 'Background', 'Affiliations', 'Teaching'])
        self.assertEqual(sparse['publications'], [])
        self.assertEqual(sparse['cv_url'], '')

    def test_missing_affiliation_logo_uses_organization_placeholder(self) -> None:
        """Keeps the profile's affiliation visible when its logo record is absent."""
        self.responses[profile_key('org-example')] = self.solr_response([], 0)
        result = profile_data('invented-a', 'live', self.read)
        sections = result['sections']
        assert isinstance(sections, list)
        self.assertIn('org_placeholder.png', sections[0]['html'])

    def test_unrelated_affiliation_logo_uses_organization_placeholder(self) -> None:
        """
        Checks an unrelated Solr document cannot supply an affiliation logo.
        """
        other = {
            'id': 'http://vivo.brown.edu/individual/org-other',
            'record_type': ['ORGANIZATION'],
            'thumbnail_file_path_s': '/file/n9999/wrong.png',
        }
        self.responses[profile_key('org-example')] = self.solr_response([other], 1)
        result = profile_data('invented-a', 'live', self.read)
        sections = result['sections']
        if not isinstance(sections, list):
            self.fail('Profile sections should be a list.')
        self.assertIn('org_placeholder.png', sections[0]['html'])
        self.assertNotIn('wrong.png', sections[0]['html'])

    def test_unusable_affiliations_do_not_leave_an_empty_heading(self) -> None:
        """
        Checks malformed affiliation links do not leave an empty profile section.
        """
        key = profile_key('invented-a')
        source = json.loads(self.responses[key].body)
        person = json.loads(source['response']['docs'][0]['json_txt'][0])
        person['affiliations'] = [{'uri': 'http://vivo.brown.edu/individual/invalid id', 'name': 'Example Unit'}]
        source['response']['docs'][0]['json_txt'] = [json.dumps(person)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(source).encode())
        result = profile_data('invented-a', 'live', self.read)
        sections = result['sections']
        if not isinstance(sections, list):
            self.fail('Profile sections should be a list.')
        self.assertNotIn('Brown Affiliations', sections[0]['html'])
        self.assertIn('Invented', sections[0]['html'])

    def test_unusable_website_links_do_not_leave_an_empty_heading(self) -> None:
        """
        Checks a profile with no usable website links omits the empty heading.
        """
        key = profile_key('invented-a')
        source = json.loads(self.responses[key].body)
        person = json.loads(source['response']['docs'][0]['json_txt'][0])
        person['on_the_web'] = [{'url': 'not a web address', 'text': 'Example'}]
        source['response']['docs'][0]['json_txt'] = [json.dumps(person)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(source).encode())
        result = profile_data('invented-a', 'live', self.read)
        sections = result['sections']
        if not isinstance(sections, list):
            self.fail('Profile sections should be a list.')
        self.assertNotIn('On the Web', sections[0]['html'])

    def test_blank_website_label_uses_its_address(self) -> None:
        """
        Checks a website link remains readable when its optional label is blank.
        """
        key = profile_key('invented-a')
        source = json.loads(self.responses[key].body)
        person = json.loads(source['response']['docs'][0]['json_txt'][0])
        person['on_the_web'] = [{'url': 'https://example.invalid/profile', 'text': '  '}]
        source['response']['docs'][0]['json_txt'] = [json.dumps(person)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(source).encode())
        result = profile_data('invented-a', 'live', self.read)
        sections = result['sections']
        if not isinstance(sections, list):
            self.fail('Profile sections should be a list.')
        self.assertIn('>https://example.invalid/profile</a>', sections[0]['html'])

    def test_profile_keeps_named_research_areas_beside_blank_entries(self) -> None:
        """
        Checks blank and malformed area entries do not hide usable research links.
        """
        key = profile_key('invented-a')
        source = json.loads(self.responses[key].body)
        person = json.loads(source['response']['docs'][0]['json_txt'][0])
        person['research_areas'] = ['Genomics', '', None]
        source['response']['docs'][0]['json_txt'] = [json.dumps(person)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(source).encode())
        result = profile_data('invented-a', 'live', self.read)
        sections = result['sections']
        if not isinstance(sections, list):
            self.fail('Profile sections should be a list.')
        self.assertIn('> Genomics </a>', sections[0]['html'])
        self.assertEqual(sections[0]['html'].count('fq=research_areas%7C'), 1)

    def test_profile_json_preserves_nullable_research_areas(self) -> None:
        """
        Checks structured profiles preserve null and empty research areas as Rails does.
        """
        doc = json.loads(self.responses[profile_key('invented-a')].body)['response']['docs'][0]
        person = json.loads(doc['json_txt'][0])
        person['research_areas'] = ['Genomics', None, '']
        person['uri'] = person['id']
        doc['json_txt'] = [json.dumps(person)]
        result = faculty_item_from_doc(doc, {}, {})
        areas = result['research_areas']
        if not isinstance(areas, list) or not areas or not isinstance(areas[0], dict):
            self.fail('Structured research areas should be a nonempty list.')
        self.assertEqual([area['label'] for area in areas], [None, '', 'Genomics'])

    def test_profile_keeps_valid_courses_beside_invalid_entries(self) -> None:
        """
        Checks HTML keeps readable courses while JSON preserves null and empty entries.
        """
        key = profile_key('invented-a')
        source = json.loads(self.responses[key].body)
        doc = source['response']['docs'][0]
        person = json.loads(doc['json_txt'][0])
        person['teacher_for'] = ['EXMP 1000 - Example Course', None, '']
        person['uri'] = person['id']
        doc['json_txt'] = [json.dumps(person)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(source).encode())
        profile = profile_data('invented-a', 'live', self.read)
        sections = profile['sections']
        if not isinstance(sections, list):
            self.fail('Profile sections should be a list.')
        teaching = next(section['html'] for section in sections if section['id'] == 'Teaching')
        self.assertEqual(teaching.count('EXMP 1000'), 1)
        structured = faculty_item_from_doc(doc, {}, {})
        self.assertEqual(structured['teacher_for'], [None, '', 'EXMP 1000 - Example Course'])

    def test_profile_json_text_lists_match_reference_defaults(self) -> None:
        """
        Checks false entries remain and unsupported entries leave whole JSON fields empty.
        """
        cases = [
            (['Z example', 'A example'], ['A example', 'Z example']),
            (['Example', False], [False, 'Example']),
            (['Example', 42], []),
            (['Example', True], []),
            ([], []),
        ]
        doc = json.loads(self.responses[profile_key('invented-a')].body)['response']['docs'][0]
        person = json.loads(doc['json_txt'][0])
        person['uri'] = person['id']
        for source_values, expected in cases:
            with self.subTest(source_values=source_values):
                person['research_areas'] = source_values
                person['teacher_for'] = source_values
                doc['json_txt'] = [json.dumps(person)]
                structured = faculty_item_from_doc(doc, {}, {})
                areas = structured['research_areas']
                if not isinstance(areas, list):
                    self.fail('Structured research areas should be a list.')
                self.assertEqual([area['label'] for area in areas], expected)
                self.assertEqual(structured['teacher_for'], expected)

    def test_profile_and_organization_json_preserve_blank_website_labels(self) -> None:
        """
        Checks JSON preserves blank labels and uses the address only for missing labels.
        """
        websites = [
            {'url': ' https://example.invalid/website ', 'text': '  '},
            {'url': ' https://example.invalid/website ', 'text': ''},
            {'url': ' https://example.invalid/website ', 'text': None},
            {'url': ' https://example.invalid/website '},
            {'url': ' https://example.invalid/website ', 'text': ' Example label '},
            {'url': ' https://example.invalid/website ', 'text': False},
        ]
        expected_labels = [
            '',
            '',
            'https://example.invalid/website',
            'https://example.invalid/website',
            'Example label',
            'https://example.invalid/website',
        ]
        person_doc = json.loads(self.responses[profile_key('invented-a')].body)['response']['docs'][0]
        person = json.loads(person_doc['json_txt'][0])
        person['uri'] = person['id']
        person['on_the_web'] = websites
        person_doc['json_txt'] = [json.dumps(person)]
        structured_person = faculty_item_from_doc(person_doc, {}, {})
        person_websites = structured_person['on_the_web']
        if not isinstance(person_websites, list) or not person_websites or not isinstance(person_websites[0], dict):
            self.fail('Structured person websites should be a nonempty list.')
        self.assertEqual([row['text'] for row in person_websites], expected_labels)
        self.assertTrue(all(row['url'] == 'https://example.invalid/website' for row in person_websites))

        key = profile_key('org-example')
        source = json.loads(self.responses[key].body)
        organization = json.loads(source['response']['docs'][0]['json_txt'][0])
        organization['web_pages'] = websites
        source['response']['docs'][0]['json_txt'] = [json.dumps(organization)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(source).encode())
        structured_org = organization_json_data('org-example', 'live', self.read)
        org_websites = structured_org['web_pages']
        if not isinstance(org_websites, list) or not org_websites or not isinstance(org_websites[0], dict):
            self.fail('Structured organization websites should be a nonempty list.')
        self.assertEqual([row['text'] for row in org_websites], expected_labels)
        self.assertTrue(all(row['url'] == 'https://example.invalid/website' for row in org_websites))

    def test_affiliation_logo_request_failure_keeps_profile_visible(self) -> None:
        """Uses the placeholder if the optional affiliation lookup fails."""
        self.responses.pop(profile_key('org-example'))
        result = profile_data('invented-a', 'live', self.read)
        sections = result['sections']
        assert isinstance(sections, list)
        self.assertIn('org_placeholder.png', sections[0]['html'])

    def test_replay_reports_missing_affiliation_logo_response(self) -> None:
        """
        Checks replay reports a missing recorded affiliation lookup.
        """
        self.responses.pop(profile_key('org-example'))
        with self.assertRaises(PageDataError):
            profile_data('invented-a', 'replay', self.read_replay)

    def test_organization_preserves_custom_and_ordinary_member_order(self) -> None:
        """
        Checks custom labels keep letter case while ordinary labels sort in uppercase.
        """
        source = json.loads(self.responses[profile_key('org-example')].body)
        item = json.loads(source['response']['docs'][0]['json_txt'][0])
        labels = ['Zulu, Example', 'alpha, Example', '', 'Alpha, Example']
        item['people'] = [
            {
                'faculty_uri': 'http://vivo.brown.edu/individual/invented-a',
                'label': label,
                'specific_position': 'Example Professor',
                'general_position': 'http://vivoweb.org/ontology/core#FacultyPosition',
            }
            for label in labels
        ]
        source['response']['docs'][0]['json_txt'] = [json.dumps(item)]
        self.responses[profile_key('org-example')] = self.solr_response(source['response']['docs'], 1)
        for custom, expected in [
            (False, ['', 'alpha, Example', 'Alpha, Example', 'Zulu, Example']),
            (True, ['', 'Alpha, Example', 'Zulu, Example', 'alpha, Example']),
        ]:
            with (
                self.subTest(custom=custom),
                patch('vivo_app.lib.source_pages.CUSTOM_ORGANIZATION_IDS', {'org-example'} if custom else set()),
            ):
                result = organization_data('org-example', 'live', self.read, extra_member_ids=[])
                faculty = result['faculty_positions']
                if not isinstance(faculty, list):
                    self.fail('Faculty positions should be a list.')
                self.assertEqual([row['name'] for row in faculty], expected)
                self.assertEqual(result['administrative_positions'], [])

    def test_organization_uses_exact_administrative_role(self) -> None:
        """Keeps lookalike role identifiers in the ordinary faculty group."""
        key = profile_key('org-example')
        source = json.loads(self.responses[key].body)
        item = json.loads(source['response']['docs'][0]['json_txt'][0])
        item['people'][0]['general_position'] = 'http://example.invalid/other#FacultyAdministrativePosition'
        source['response']['docs'][0]['json_txt'] = [json.dumps(item)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(source).encode())
        result = organization_data('org-example', 'live', self.read)
        self.assertEqual(result['administrative_positions'], [])
        faculty = result['faculty_positions']
        assert isinstance(faculty, list)
        self.assertEqual(len(faculty), 1)

    def test_organization_keeps_valid_members_when_one_uri_is_unusable(self) -> None:
        """
        Checks an invalid member address does not hide the other organization members.
        """
        key = profile_key('org-example')
        source = json.loads(self.responses[key].body)
        organization = json.loads(source['response']['docs'][0]['json_txt'][0])
        organization['people'].append({'faculty_uri': 'invalid person address', 'label': 'Other Person'})
        source['response']['docs'][0]['json_txt'] = [json.dumps(organization)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(source).encode())
        result = organization_data('org-example', 'live', self.read)
        faculty = result['faculty_positions']
        if not isinstance(faculty, list):
            self.fail('Faculty positions should be a list.')
        self.assertEqual([row['name'] for row in faculty], ['Researcher, Invented'])

    def test_organization_rejects_repeated_member_documents(self) -> None:
        """
        Checks repeated Solr member records cannot silently replace a portrait.
        """
        key = member_key(['invented-a'])
        source = json.loads(self.responses[key].body)
        source['response']['docs'].append(dict(source['response']['docs'][0]))
        source['response']['numFound'] = 2
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(source).encode())
        with self.assertRaises(PageDataError):
            organization_data('org-example', 'live', self.read)
        with self.assertRaises(PageDataError):
            organization_json_data('org-example', 'live', self.read)

    def test_organization_without_logo_uses_borderless_placeholder(self) -> None:
        """Matches the organization page's plain default image."""
        key = profile_key('org-example')
        source = json.loads(self.responses[key].body)
        source['response']['docs'][0].pop('thumbnail_file_path_s')
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(source).encode())
        result = organization_data('org-example', 'live', self.read)
        image = result['image']
        assert isinstance(image, str)
        self.assertIn('org_placeholder_noborder.png', image)

    def test_numbered_facet_filter_keeps_search_selection(self) -> None:
        """
        Checks search submissions retain a facet sent as a numbered form field.
        """
        result = search_data([('q', 'Example'), ('fq_0', 'record_type|PEOPLE')], 'live', self.read)
        selected = result['selected_filters']
        self.assertIsInstance(selected, list)
        if not isinstance(selected, list):
            self.fail('Selected filters were not a list.')
        self.assertEqual(selected[0]['value'], 'PEOPLE')
        with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
            response = self.get_page('/search?q=Example&fq_0=record_type%7CPEOPLE')
        self.assertContains(response, 'Remove filter PEOPLE')

    def test_repeated_facet_filter_appears_once(self) -> None:
        """
        Checks a repeated facet from two form fields creates one search selection.
        """
        result = search_data(
            [('q', 'Example'), ('fq', 'record_type|PEOPLE'), ('fq_0', 'record_type|PEOPLE')],
            'live',
            self.read,
        )
        selected = result['selected_filters']
        if not isinstance(selected, list):
            self.fail('Selected search filters should be a list.')
        self.assertEqual([row['value'] for row in selected], ['PEOPLE'])

    def test_one_invalid_facet_value_does_not_hide_search_results(self) -> None:
        """
        Checks search and the full facet dialog keep usable values beside a malformed pair.
        """
        for key in (search_key('Example', 1, []), search_key('Example', 1, [], -1)):
            source = json.loads(self.responses[key].body)
            source['facet_counts']['facet_fields']['affiliations'] = [
                'Example Department',
                1,
                'Broken value',
                -1,
                'Another Unit',
                2,
            ]
            self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(source).encode())
        result = search_data([('q', 'Example')], 'live', self.read)
        facets = result['facets']
        if not isinstance(facets, list):
            self.fail('Search facets should be a list.')
        affiliation = next(facet for facet in facets if facet['name'] == 'affiliations')
        self.assertEqual([value['text'] for value in affiliation['values']], ['Example Department', 'Another Unit'])
        all_values = facet_values_data([('q', 'Example'), ('f_name', 'affiliations')], 'live', self.read)
        self.assertEqual([value['text'] for value in all_values], ['Example Department', 'Another Unit'])

    def test_search_ignores_other_solr_record_types(self) -> None:
        """Keeps visible results when Solr also returns an unrelated record type."""
        key = search_key('Example', 1, [])
        original = json.loads(self.responses[key].body)
        other = dict(original['response']['docs'][0], record_type=['DOCUMENT'])
        original['response']['docs'].insert(0, other)
        original['response']['numFound'] = 2
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(original).encode())
        result = search_data([('q', 'Example')], 'live', self.read)
        results = result['results']
        assert isinstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertEqual(result['total'], 2)

    def test_search_ignores_record_with_unreadable_json(self) -> None:
        """Keeps readable records when one search document has broken JSON."""
        key = search_key('Example', 1, [])
        original = json.loads(self.responses[key].body)
        bad = dict(original['response']['docs'][0], json_txt=['{invalid'])
        original['response']['docs'].insert(0, bad)
        original['response']['numFound'] = 2
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(original).encode())
        result = search_data([('q', 'Example')], 'live', self.read)
        results = result['results']
        assert isinstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Invented Researcher')

    def test_search_json_ignores_other_solr_record_types(self) -> None:
        """Returns supported records from JSON search despite an unrelated document."""
        key = search_key('Example', 1, [])
        original = json.loads(self.responses[key].body)
        other = dict(original['response']['docs'][0], record_type=['DOCUMENT'])
        original['response']['docs'].insert(0, other)
        original['response']['numFound'] = 2
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(original).encode())
        result = search_json_data([('q', 'Example')], 'live', 'https://example.invalid', self.read)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['vivo_id'], 'invented-a')

    def test_search_json_ignores_record_with_unreadable_json(self) -> None:
        """Returns readable records when another JSON search document is broken."""
        key = search_key('Example', 1, [])
        original = json.loads(self.responses[key].body)
        bad = dict(original['response']['docs'][0], json_txt=['{invalid'])
        original['response']['docs'].insert(0, bad)
        original['response']['numFound'] = 2
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(original).encode())
        result = search_json_data([('q', 'Example')], 'live', 'https://example.invalid', self.read)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['vivo_id'], 'invented-a')

    def test_search_ignores_record_with_unusable_identifier(self) -> None:
        """
        Checks one unsupported result identifier does not hide the other search results.
        """
        key = search_key('Example', 1, [])
        source = json.loads(self.responses[key].body)
        bad = dict(source['response']['docs'][0], id='http://vivo.brown.edu/individual/invalid id')
        source['response']['docs'].insert(0, bad)
        source['response']['numFound'] = 2
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(source).encode())
        html = search_data([('q', 'Example')], 'live', self.read)
        structured = search_json_data([('q', 'Example')], 'live', 'https://example.invalid', self.read)
        results = html['results']
        if not isinstance(results, list):
            self.fail('Search results should be a list.')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], 'invented-a')
        self.assertEqual(len(structured), 1)
        self.assertEqual(structured[0]['vivo_id'], 'invented-a')

    def test_search_keeps_named_records_when_another_has_no_name(self) -> None:
        """
        Checks a nameless source record does not hide usable search results.
        """
        key = search_key('Example', 1, [])
        source = json.loads(self.responses[key].body)
        unnamed = dict(source['response']['docs'][0])
        unnamed['id'] = 'http://vivo.brown.edu/individual/invented-unnamed'
        unnamed.pop('display_name_s', None)
        unnamed['json_txt'] = [json.dumps({'title': 'Unnamed source record'})]
        source['response']['docs'].insert(0, unnamed)
        source['response']['numFound'] = 2
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(source).encode())
        html = search_data([('q', 'Example')], 'live', self.read)
        structured = search_json_data([('q', 'Example')], 'live', 'https://example.invalid', self.read)
        results = html['results']
        if not isinstance(results, list):
            self.fail('Search results should be a list.')
        self.assertEqual(len(results), 1)
        self.assertEqual(len(structured), 1)
        self.assertEqual(structured[0]['vivo_id'], 'invented-a')

    def test_large_organization_loads_member_portraits_in_batches(self) -> None:
        """
        Checks smaller member requests retain every organization member in order.
        """
        ids = [f'invented-{number:03d}' for number in range(101)]
        key = profile_key('org-example')
        source = json.loads(self.responses[key].body)
        item = json.loads(source['response']['docs'][0]['json_txt'][0])
        item['people'] = [
            {'faculty_uri': f'http://vivo.brown.edu/individual/{identifier}', 'label': identifier} for identifier in ids
        ]
        source['response']['docs'][0]['json_txt'] = [json.dumps(item)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(source).encode())
        for start in range(0, len(ids), 20):
            batch = ids[start : start + 20]
            docs = [
                {'id': f'http://vivo.brown.edu/individual/{identifier}', 'record_type': ['PEOPLE']} for identifier in batch
            ]
            self.responses[member_key(batch)] = self.solr_response(docs, len(batch))
        result = organization_data('org-example', 'live', self.read)
        faculty = result['faculty_positions']
        assert isinstance(faculty, list)
        self.assertEqual(len(faculty), 101)
        self.assertEqual([row['name'] for row in faculty], ids)

    def test_large_organization_json_loads_member_portraits_in_batches(self) -> None:
        """
        Checks smaller member requests retain every structured member in order.
        """
        ids = [f'invented-{number:03d}' for number in range(101)]
        key = profile_key('org-example')
        source = json.loads(self.responses[key].body)
        item = json.loads(source['response']['docs'][0]['json_txt'][0])
        item['people'] = [
            {'faculty_uri': f'http://vivo.brown.edu/individual/{identifier}', 'label': identifier} for identifier in ids
        ]
        source['response']['docs'][0]['json_txt'] = [json.dumps(item)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(source).encode())
        for start in range(0, len(ids), 20):
            batch = ids[start : start + 20]
            docs = [
                {'id': f'http://vivo.brown.edu/individual/{identifier}', 'record_type': ['PEOPLE']} for identifier in batch
            ]
            self.responses[member_key(batch)] = self.solr_response(docs, len(batch))
        result = organization_json_data('org-example', 'live', self.read)
        people = result['people']
        assert isinstance(people, list)
        self.assertEqual(len(people), 101)
        self.assertEqual([row['label'] for row in people], ids)

    def test_large_organization_downloads_member_publications_in_batches(self) -> None:
        """Builds the publication download for more than 100 organization members."""
        ids = [f'invented-{number:03d}' for number in range(101)]
        key = profile_key('org-example')
        source = json.loads(self.responses[key].body)
        item = json.loads(source['response']['docs'][0]['json_txt'][0])
        item['people'] = [
            {'faculty_uri': f'http://vivo.brown.edu/individual/{identifier}', 'label': identifier} for identifier in ids
        ]
        source['response']['docs'][0]['json_txt'] = [json.dumps(item)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(source).encode())
        for start in range(0, len(ids), 20):
            batch = ids[start : start + 20]
            docs = [
                {
                    'id': f'http://vivo.brown.edu/individual/{identifier}',
                    'record_type': ['PEOPLE'],
                    'json_txt': [json.dumps({'name': identifier, 'contributor_to': []})],
                }
                for identifier in batch
            ]
            self.responses[member_details_key(batch)] = self.solr_response(docs, len(batch))
        result = organization_publications_data('org-example', 'live', self.read)
        self.assertEqual(result, 'Id\tFaculty\tTitle\tAuthors\tYear\tType\tCitation\n')

    def test_organization_download_skips_member_missing_from_solr(self) -> None:
        """Downloads publications from members whose Solr records still exist."""
        self.responses[member_details_key(['invented-a'])] = self.solr_response([], 0)
        result = organization_publications_data('org-example', 'live', self.read)
        self.assertEqual(result, 'Id\tFaculty\tTitle\tAuthors\tYear\tType\tCitation\n')

    def test_person_without_portrait_uses_public_placeholder(self) -> None:
        """
        Checks a missing person portrait uses the same image as the Rails profile.
        """
        self.assertEqual(thumbnail_url({}), '/static/images/person_placeholder.jpg')

    def test_search_result_without_email_keeps_reference_email_link(self) -> None:
        """
        Checks a result without an address retains the reference email control.
        """
        key = search_key('Example', 1, [])
        source = json.loads(self.responses[key].body)
        org = json.loads(self.responses[profile_key('org-example')].body)['response']['docs'][0]
        source['response']['docs'] = [org]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(source).encode())
        with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
            page = self.get_page('/search?q=Example')
        self.assertContains(page, 'href="mailto:" aria-label="Email researcher at "')
        self.assertContains(page, 'Example Department')

    def test_search_form_keeps_selected_filters_for_new_query(self) -> None:
        """
        Checks a new search submitted from a filtered result page retains its filters.
        """
        with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
            response = self.get_page('/search?q=Example&fq=record_type%7CPEOPLE')
        self.assertContains(response, 'name="fq_0" value="record_type|PEOPLE"')

    def test_search_bottom_pagination_links_to_adjacent_pages(self) -> None:
        """
        Checks the bottom pagination has the previous and next links shown by Rails.
        """
        key = search_key('Example', 1, [])
        response = json.loads(self.responses[key].body)
        response['response']['numFound'] = 21
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
            first = self.get_page('/search?q=Example')
            second = self.get_page('/search?q=Example&page=2')
        self.assertContains(first, '<h2 class="sr-only">Pagination</h2>')
        self.assertContains(first, '<li class="active"><a href="/search?q=Example&amp;page=1">1</a>')
        self.assertContains(first, '<a href="/search?q=Example&amp;page=2">')
        self.assertContains(second, '<a href="/search?q=Example&amp;page=1">')

    def test_old_search_term_redirects_without_source_request(self) -> None:
        """
        Checks legacy search redirects preserve spaces and discard other parameters.
        """
        prefix = '/mounted-app'
        previous_prefix = get_script_prefix()
        set_script_prefix(prefix)
        try:
            cases = [
                ('querytext=Example+Term', 'Example%20Term'),
                ('querytext=Example%20Term', 'Example%20Term'),
                ('querytext=Example&q=Other&page=2', 'Example'),
            ]
            for query, expected in cases:
                with self.subTest(query=query):
                    with patch('vivo_app.lib.source_pages.read_source') as read:
                        response = self.client.get('/search?' + query, SCRIPT_NAME=prefix)
                    assert isinstance(response, HttpResponse)
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(response['Location'], prefix + '/search?q=' + expected)
                    read.assert_not_called()
        finally:
            set_script_prefix(previous_prefix)

    def test_people_entry_redirects_to_filtered_search(self) -> None:
        """
        Checks the people entry link opens the People-filtered search.
        """
        prefix = '/mounted-app'
        previous_prefix = get_script_prefix()
        set_script_prefix(prefix)
        try:
            for path in ['/people', '/people/?fq=record_type%7CORGANIZATION&q=Other&page=2']:
                with self.subTest(path=path):
                    with patch('vivo_app.lib.source_pages.read_source') as read:
                        response = self.client.get(path, SCRIPT_NAME=prefix)
                    assert isinstance(response, HttpResponse)
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(response['Location'], 'http://testserver' + prefix + '/search?fq=record_type|PEOPLE')
                    read.assert_not_called()
        finally:
            set_script_prefix(previous_prefix)

    def test_organization_entry_redirects_to_filtered_search(self) -> None:
        """
        Checks the organization entry link opens the Organization-filtered search.
        """
        prefix = '/mounted-app'
        previous_prefix = get_script_prefix()
        set_script_prefix(prefix)
        try:
            for path in ['/ous', '/ous/?fq=record_type%7CPEOPLE&q=Other&page=2']:
                with self.subTest(path=path):
                    with patch('vivo_app.lib.source_pages.read_source') as read:
                        response = self.client.get(path, SCRIPT_NAME=prefix)
                    assert isinstance(response, HttpResponse)
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(
                        response['Location'], 'http://testserver' + prefix + '/search?fq=record_type|ORGANIZATION'
                    )
                    read.assert_not_called()
        finally:
            set_script_prefix(previous_prefix)

    def test_display_entry_redirects_to_search(self) -> None:
        """
        Checks an empty display path redirects to search inside the mounted app.
        """
        prefix = '/mounted-app'
        previous_prefix = get_script_prefix()
        set_script_prefix(prefix)
        try:
            response = self.client.get('/display/', SCRIPT_NAME=prefix)
            assert isinstance(response, HttpResponse)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response['Location'], prefix + '/search')
        finally:
            set_script_prefix(previous_prefix)

    def test_search_result_identifies_people_and_organizations(self) -> None:
        """
        Checks search cards identify their record types in the page markup.
        """
        with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
            person_page = self.get_page('/search?q=Example')
        self.assertContains(person_page, 'itemscope itemtype="http://schema.org/Person"')
        self.assertContains(person_page, '<span itemprop="name" class="fn">')

        key = search_key('Example', 1, [])
        response = json.loads(self.responses[key].body)
        response['response']['docs'] = [
            {
                'id': 'http://vivo.brown.edu/individual/org-invented',
                'record_type': ['ORGANIZATION'],
                'json_txt': [json.dumps({'name': 'Invented Organization'})],
            }
        ]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
            organization_page = self.get_page('/search?q=Example')
        self.assertContains(organization_page, 'itemscope itemtype="http://schema.org/Organization"')

    def test_search_matches_cover_distinct_terms_before_repeats(self) -> None:
        """
        Checks matching terms from later source fields appear before repeated first-term snippets.
        """
        fields: dict[str, object] = {
            'department_t': ['<strong>Biology</strong> one', '<strong>Biology</strong> two'],
            'overview_en': ['<strong>Research</strong> three'],
        }
        matches = selected_highlights(fields, 2)
        self.assertEqual(
            [value for _, value in matches], ['<strong>Biology</strong> one', '<strong>Research</strong> three']
        )

    def test_search_matches_preserve_nonbreaking_edge_spaces(self) -> None:
        """
        Checks match previews trim ordinary whitespace but retain nonbreaking edge spaces.
        """
        fields: dict[str, object] = {
            'alltext': [' \t\x00\u00a0 - <strong>Science</strong> lecture\u00a0\r\n '],
        }
        self.assertEqual(selected_highlights(fields), [('alltext', '\u00a0 - <strong>Science</strong> lecture\u00a0')])
        doc: dict[str, object] = {'id': 'http://vivo.brown.edu/individual/invented-a'}
        response: dict[str, object] = {
            'highlighting': {'vitroIndividual:http://vivo.brown.edu/individual/invented-a': fields},
        }
        self.assertEqual(match_html(response, doc), '<p>\u00a0 - <strong>Science</strong> lecture\u00a0</p>')

    def test_search_matches_group_fields_with_captions(self) -> None:
        """
        Checks search match details label and join snippets from descriptive fields.
        """
        doc: dict[str, object] = {'id': 'http://vivo.brown.edu/individual/invented-a'}
        response: dict[str, object] = {
            'highlighting': {
                'vitroIndividual:http://vivo.brown.edu/individual/invented-a': {
                    'department_t': ['<strong>Biology</strong> one', '<strong>Biology</strong> two'],
                    'research_areas_en': ['<p><strong>Science</strong> lab</p>'],
                }
            }
        }
        markup = match_html(response, doc)
        self.assertIn('<p>Department: <strong>Biology</strong> one, <strong>Biology</strong> two</p>', markup)
        self.assertIn('<p>Research areas: <strong>Science</strong> lab</p>', markup)

    def test_search_matches_display_markup_and_remove_source_label(self) -> None:
        """
        Checks match details keep bold terms and render source markup as visible text.
        """
        value = (
            '<strong>Science</strong> <script>alert(1)</script> Agent Faculty Member Organization or Person at Brown Person'
        )
        cleaned = safe_match_text(value)
        self.assertIn('<strong>Science</strong>', cleaned)
        self.assertIn('&lsaquo;script&rsaquo;', cleaned)
        self.assertNotIn('<script>', cleaned)
        self.assertNotIn('Agent Faculty Member Organization or Person at Brown Person', cleaned)

    def test_missing_response_and_unsupported_option_do_not_fall_back(self) -> None:
        """
        Checks missing source data and unsupported requests fail without sample content.
        """
        with (
            patch('vivo_app.lib.source_pages.read_source', side_effect=self.read),
            patch('vivo_app.lib.source_books.read_source', side_effect=self.read),
        ):
            self.assertEqual(self.get_page('/search?q=Other').status_code, 503)
            self.assertEqual(self.get_page('/search?q=Example&format=xml').status_code, 503)
            self.assertEqual(self.get_page('/display/other').status_code, 503)
            self.assertEqual(self.get_page('/search_facets?q=Example&f_name=bad').status_code, 503)
            self.assertEqual(self.get_page('/display/invented-a/publications/').status_code, 503)
            self.assertEqual(self.get_page('/').status_code, 503)
        self.responses.pop(member_key(['invented-a']))
        with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
            self.assertEqual(self.get_page('/display/org-example').status_code, 503)
        self.assertEqual(self.get_page('/source-documents/docs/../../private.pdf').status_code, 503)

    def test_absent_person_and_organization_show_not_found(self) -> None:
        """
        Checks exact Solr lookups with no record show the public missing-page response.
        """
        self.responses[profile_key('invented-absent')] = self.solr_response([], 0)
        self.responses[profile_key('org-absent')] = self.solr_response([], 0)
        with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
            person = self.get_page('/display/invented-absent')
            organization = self.get_page('/display/org-absent')
        self.assertContains(person, 'Page not found', status_code=404)
        self.assertContains(person, 'href="/search">searching for a researcher</a>', status_code=404)
        self.assertContains(person, 'id="search-homepage"', status_code=404)
        self.assertContains(person, 'name="q"', status_code=404)
        self.assertContains(organization, 'Page not found', status_code=404)

    def test_publication_title_joins_venue_without_extra_comma(self) -> None:
        """
        Checks source citation punctuation matches the public display format.
        """
        markup = publication_html({'title': 'Example work', 'published_in': 'Invented Journal', 'date': '2024'})
        self.assertIn('"Example work." <i>Invented Journal</i>, 2024.', markup)

    def test_book_citation_shows_italic_title_and_publisher(self) -> None:
        """
        Checks books include the publisher rather than article-style title quotes.
        """
        markup = publication_html(
            {
                'type': 'http://vivo.brown.edu/ontology/citation#Book',
                'title': 'Invented Book',
                'publisher_label': 'Example Press',
                'date': '2018',
            }
        )
        self.assertIn('<i>Invented Book</i>. Example Press, 2018.', markup)
        self.assertNotIn('"Invented Book', markup)

    def test_book_section_citation_shows_parent_book(self) -> None:
        """
        Checks chapters show the parent book, editor, publisher, year, and pages.
        """
        markup = publication_html(
            {
                'type': 'http://vivo.brown.edu/ontology/citation#BookSection',
                'title': 'Invented Chapter',
                'book': 'Invented Collection',
                'editors': 'A. Editor',
                'publisher_label': 'Example Press',
                'date': '2020',
                'pages': '10-20',
            }
        )
        self.assertIn(
            '"Invented Chapter." <i>Invented Collection</i>, edited by A. Editor, Example Press, 2020, pp. 10-20.',
            markup,
        )

    def test_book_citation_preserves_title_spacing(self) -> None:
        """
        Checks book titles retain spaces inside italics while blank values stay absent.
        """
        record: dict[str, object] = {'type': 'http://vivo.brown.edu/ontology/citation#Book', 'title': 'Example Book '}
        self.assertEqual(publication_html(record), '<i>Example Book </i>. <div class="no-orphans"></div>')
        record['title'] = ' '
        record['book'] = '  '
        self.assertNotIn('<i>', publication_html(record))
        record['title'] = ['Example Book ']
        record['book'] = 'Volume Two '
        self.assertEqual(publication_html(record), '<i>Example Book  Volume Two </i>. <div class="no-orphans"></div>')

    def test_publications_sort_titles_without_outer_spaces(self) -> None:
        """
        Checks same-year publication titles are ordered after trimming outer spaces.
        """
        rows: dict[str, object] = {
            'contributor_to': [
                {'type': 'http://vivo.brown.edu/ontology/citation#Article', 'title': ' Zeta', 'date': '2020'},
                {'type': 'http://vivo.brown.edu/ontology/citation#Article', 'title': 'Alpha', 'date': '2020'},
            ]
        }
        publications_data, _ = publications(rows)
        self.assertIn('Alpha', publications_data[0]['html'])
        self.assertIn('Zeta', publications_data[1]['html'])

    def test_publications_keep_unknown_citation_types(self) -> None:
        """
        Checks an unrecognized citation type remains visible as Other.
        """
        rows: dict[str, object] = {
            'contributor_to': [
                {'title': 'Missing type', 'date': '2020'},
                {'type': 'https://example.invalid/citation#Book', 'title': 'Unknown book', 'date': '2019'},
            ]
        }
        result, filters = publications(rows)
        self.assertEqual(len(result), 2)
        self.assertEqual(filters, [{'id': '', 'label': 'Other', 'count': 2}])
        self.assertIn('"Unknown book."', result[1]['html'])

    def test_publication_year_uses_public_site_range(self) -> None:
        """
        Checks dates outside the public site's accepted range do not display or outrank valid years.
        """
        rows: dict[str, object] = {
            'contributor_to': [
                {'type': 'http://vivo.brown.edu/ontology/citation#Article', 'title': 'Too Early', 'date': '1899'},
                {'type': 'http://vivo.brown.edu/ontology/citation#Article', 'title': 'Current', 'date': '2020-01-01'},
                {'type': 'http://vivo.brown.edu/ontology/citation#Article', 'title': 'Too Late', 'date': '2201'},
            ]
        }
        publications_data, _ = publications(rows)
        self.assertIn('Current', publications_data[0]['html'])
        self.assertIn('2020', publications_data[0]['html'])
        self.assertNotIn('1899', publications_data[1]['html'])
        self.assertNotIn('2201', publications_data[2]['html'])

    def test_publication_year_accepts_numeric_source_dates(self) -> None:
        """
        Checks numeric dates use the same year conversion as the Rails model.
        """
        rows: dict[str, object] = {
            'contributor_to': [
                {'type': 'http://vivo.brown.edu/ontology/citation#Article', 'title': 'Numeric date', 'date': 2021},
                {'type': 'http://vivo.brown.edu/ontology/citation#Article', 'title': 'Padded date', 'date': '02020'},
            ]
        }
        result, _ = publications(rows)
        self.assertIn('2021', result[0]['html'])
        self.assertIn('2020', result[1]['html'])

    def test_publication_links_match_available_source_fields(self) -> None:
        """
        Checks DOI and PubMed links appear together, while another safe URL is used only when neither exists.
        """
        linked = publication_html(
            {'doi': '10.0000/example', 'pub_med_id': '12345678', 'url': 'https://example.invalid/item'}
        )
        self.assertIn('https://doi.org/10.0000/example', linked)
        self.assertIn('http://www.ncbi.nlm.nih.gov/pubmed/?term=12345678', linked)
        self.assertNotIn('More Info', linked)
        alternate = publication_html({'url': 'https://example.invalid/item'})
        self.assertIn('More Info', alternate)
        self.assertIn('https://example.invalid/item', alternate)
        invalid = publication_html({'pub_med_id': 'bad value'})
        self.assertNotIn('PubMed', invalid)
        self.assertTrue(invalid.endswith(' <div class="no-orphans"></div>'))
        self.assertTrue(linked.endswith('</a></div>'))
        self.assertTrue(alternate.endswith('</a></div>'))

    def test_pubmed_link_accepts_alphanumeric_identifiers(self) -> None:
        """
        Checks a valid source identifier with letters still gets a PubMed link.
        """
        markup = publication_html({'pub_med_id': 'PMC12345'})
        self.assertIn('http://www.ncbi.nlm.nih.gov/pubmed/?term=PMC12345', markup)

    def test_publication_doi_links_preserve_source_punctuation(self) -> None:
        """
        Checks source DOI punctuation and supplied URL prefixes remain unchanged.
        """
        for doi in ('10.0000/example(2)', 'https://doi.org/10.0000/example'):
            with self.subTest(doi=doi):
                markup = publication_html({'doi': doi})
                self.assertIn('href="https://doi.org/' + doi + '"', markup)

    def test_publication_doi_links_escape_ampersands_in_markup(self) -> None:
        """
        Checks attribute escaping preserves a source ampersand in the destination.
        """
        markup = publication_html({'doi': '10.0000/example&appendix'})
        self.assertIn('href="https://doi.org/10.0000/example&amp;appendix"', markup)

    def test_publication_links_preserve_source_edge_spaces(self) -> None:
        """
        Checks citation link addresses keep spaces supplied by the source.
        """
        for doi in ('10.0000/example   ', ' https://doi.org/10.0000/example'):
            with self.subTest(doi=doi):
                markup = publication_html({'doi': doi})
                self.assertIn('href="https://doi.org/' + doi + '"', markup)
        markup = publication_html({'pub_med_id': '12345678 '})
        self.assertIn('href="http://www.ncbi.nlm.nih.gov/pubmed/?term=12345678 "', markup)
        markup = publication_html({'url': 'https://example.invalid/item '})
        self.assertIn('href="https://example.invalid/item "', markup)

    def test_repository_root_link_is_full_text(self) -> None:
        """
        Checks the repository root is treated as a full-text link when supplied by a citation.
        """
        markup = publication_html({'url': 'https://repository.library.brown.edu'})
        self.assertIn('Full Text', markup)
        self.assertNotIn('More Info', markup)

    def test_research_areas_use_case_insensitive_order(self) -> None:
        """
        Checks the profile displays research areas in the same alphabetical order as Rails.
        """
        with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
            profile = self.get_page('/display/invented-a')
        body = profile.content.decode()
        self.assertLess(body.index('research_areas%7Cabsorption'), body.index('research_areas%7CExcretion'))
        self.assertLess(body.index('research_areas%7CExcretion'), body.index('research_areas%7Cliver'))

    def test_profile_keeps_other_content_when_research_areas_are_invalid(self) -> None:
        """
        Checks malformed optional research areas do not hide HTML or profile JSON.
        """
        key = profile_key('invented-a')
        response = json.loads(self.responses[key].body)
        doc = response['response']['docs'][0]
        person = json.loads(doc['json_txt'][0])
        person['uri'] = person['id']
        person['research_areas'] = 'invalid list'
        doc['json_txt'] = [json.dumps(person)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        html = profile_data('invented-a', 'live', self.read)
        sections = html['sections']
        if not isinstance(sections, list):
            self.fail('Profile sections should be a list.')
        self.assertNotIn('Research Areas', sections[0]['html'])
        structured = faculty_item_from_doc(doc, {}, {})
        self.assertEqual(structured['research_areas'], [])

    def test_profile_keeps_other_content_when_teaching_is_invalid(self) -> None:
        """
        Checks HTML stays available and JSON retains the Rails empty course field.
        """
        key = profile_key('invented-a')
        response = json.loads(self.responses[key].body)
        doc = response['response']['docs'][0]
        person = json.loads(doc['json_txt'][0])
        person['uri'] = person['id']
        person['teacher_for'] = ['Valid course', 42]
        doc['json_txt'] = [json.dumps(person)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        html = profile_data('invented-a', 'live', self.read)
        sections = html['sections']
        if not isinstance(sections, list):
            self.fail('Profile sections should be a list.')
        self.assertIn('Teaching', [section['id'] for section in sections])
        structured = faculty_item_from_doc(doc, {}, {})
        self.assertEqual(structured['teacher_for'], [])

    def test_invalid_optional_record_array_does_not_hide_profile(self) -> None:
        """
        Checks an unreadable optional record array leaves other profile sections available.
        """
        self.assertEqual(entries({'on_the_web': 'invalid'}, 'on_the_web'), [])
        self.assertEqual(
            entries({'on_the_web': [{'url': 'https://example.invalid'}, 42]}, 'on_the_web'),
            [{'url': 'https://example.invalid'}],
        )
        key = profile_key('invented-a')
        response = json.loads(self.responses[key].body)
        doc = response['response']['docs'][0]
        person = json.loads(doc['json_txt'][0])
        person['on_the_web'] = [{'url': 'https://example.invalid'}, 42]
        doc['json_txt'] = [json.dumps(person)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        profile = profile_data('invented-a', 'live', self.read)
        self.assertEqual(profile['name'], 'Invented Researcher')
        sections = profile['sections']
        if not isinstance(sections, list):
            self.fail('Profile sections should be a list.')
        self.assertIn('https://example.invalid', sections[0]['html'])

    def test_search_json_uses_the_html_search_response(self) -> None:
        """
        Checks search JSON has the public fields without requesting another Solr shape.
        """
        rows = search_json_data([('q', 'Example')], 'live', 'http://127.0.0.1/', self.read)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['vivo_id'], 'invented-a')
        self.assertEqual(rows[0]['uri'], 'http://127.0.0.1/display/invented-a')
        self.assertEqual(rows[0]['thumbnail'], 'http://example.invalid/profile-images/123/4/portrait.jpg')
        self.assertEqual(rows[0]['title'], 'Example Professor')
        self.assertEqual(rows[0]['email'], 'invented@example.invalid')
        self.assertEqual(
            rows[0]['highlights'],
            {'highlights': [{'field': 'short_id_s', 'values': ['<strong>Example</strong> <script>unsafe</script>']}]},
        )
        with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
            response = self.get_page('/search?q=Example&format=json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEqual(response.content.decode(), profile_json_text(rows))
        self.assertEqual(json.loads(response.content), rows)
        self.assertEqual(search_json_data([('q', 'none')], 'live', 'http://127.0.0.1/', self.read), [])

    def test_search_json_preserves_null_and_empty_title_and_email(self) -> None:
        """
        Checks missing and null fields return JSON null while explicit empty strings remain empty.
        """
        key = search_key('Example', 1, [])
        original = self.responses[key]
        cases: tuple[tuple[str, dict[str, object], str | None], ...] = (
            ('missing', {}, None),
            ('null', {'title': None, 'email': None}, None),
            ('empty', {'title': '', 'email': ''}, ''),
        )
        for kind in ('PEOPLE', 'ORGANIZATION'):
            for label, fields, expected in cases:
                with self.subTest(kind=kind, fields=label):
                    source = json.loads(original.body)
                    doc = source['response']['docs'][0]
                    raw = json.loads(doc['json_txt'][0])
                    raw.pop('title', None)
                    raw.pop('email', None)
                    raw.update(fields)
                    doc['json_txt'] = [json.dumps(raw)]
                    doc['record_type'] = [kind]
                    self.responses[key] = RecordedResponse(200, (), json.dumps(source).encode())
                    with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
                        response = self.get_page('/search?q=Example&format=json')
                    self.assertEqual(response.status_code, 200)
                    result = json.loads(response.content)
                    self.assertEqual(result[0]['title'], expected)
                    self.assertEqual(result[0]['email'], expected)
                    if expected is None:
                        self.assertIn(b'"title":null', response.content)
                        self.assertIn(b'"email":null', response.content)

    def test_search_json_encoding_preserves_highlights_and_unicode(self) -> None:
        """
        Checks live and replay downloads escape HTML without changing decoded search values.
        """
        data: list[dict[str, object]] = [
            {
                'name': 'Réseau 雪',
                'highlights': {
                    'highlights': [
                        {'field': 'title', 'values': ['Professor of <strong>Example</strong> & text\u2028\u2029']}
                    ]
                },
                'literal': r'\u003c',
                'optional': None,
            }
        ]
        expected = (
            '[{"name":"Réseau 雪","highlights":{"highlights":[{"field":"title","values":'
            '["Professor of \\u003cstrong\\u003eExample\\u003c/strong\\u003e \\u0026 text\\u2028\\u2029"]}]},'
            '"literal":"\\\\u003c","optional":null}]'
        )
        for mode in ('live', 'replay'):
            with (
                self.subTest(mode=mode),
                override_settings(PAGE_DATA_MODE=mode, UPSTREAM_RECORDING_MANIFEST='invented-manifest.json'),
                patch('vivo_app.views.search_json_data', return_value=data),
            ):
                response = self.get_page('/search?q=Example&format=json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
            self.assertEqual(response.content.decode(), expected)
            self.assertEqual(json.loads(response.content), data)

    def test_search_json_encoding_preserves_empty_results(self) -> None:
        """
        Checks a search with no results still returns an empty JSON array.
        """
        with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
            response = self.get_page('/search?q=none&format=json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'[]')
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')

    def test_organization_publications_tsv_uses_member_records(self) -> None:
        """
        Checks the public TSV fields come from complete member records and fail if one is absent.
        """
        body = organization_publications_data('org-example', 'live', self.read)
        self.assertTrue(body.startswith('Id\tFaculty\tTitle\tAuthors\tYear\tType\tCitation\n'))
        self.assertIn('Example publication\tResearcher, Invented\t2024\tArticle\t', body)
        with patch('vivo_app.lib.source_pages.read_source', side_effect=self.read):
            response = self.get_page('/display/org-example/publications.tsv')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertEqual(
            response['Content-Disposition'], 'attachment; filename="org-example.tsv"; filename*=UTF-8\'\'org-example.tsv'
        )
        self.assertEqual(response.content.decode(), body)
        self.responses.pop(member_details_key(['invented-a']))
        with self.assertRaises(PageDataError):
            organization_publications_data('org-example', 'live', self.read)

    def test_organization_publications_tsv_orders_titles_and_valid_years(self) -> None:
        """
        Checks organization downloads follow the same publication order and year rules as profiles.
        """
        key = member_details_key(['invented-a'])
        response = json.loads(self.responses[key].body)
        person = json.loads(response['response']['docs'][0]['json_txt'][0])
        person['contributor_to'] = [
            {'type': 'http://vivo.brown.edu/ontology/citation#Article', 'title': ' Zeta', 'date': '2020'},
            {'type': 'http://vivo.brown.edu/ontology/citation#Article', 'title': 'Alpha', 'date': '2020'},
            {'type': 'http://vivo.brown.edu/ontology/citation#Article', 'title': 'Old', 'date': '1899'},
        ]
        response['response']['docs'][0]['json_txt'] = [json.dumps(person)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        body = organization_publications_data('org-example', 'live', self.read)
        self.assertLess(body.index('\tAlpha\t'), body.index('\t Zeta\t'))
        self.assertIn('\tOld\t\t\tArticle\t', body)

    def test_organization_export_sorts_members_before_request_batches(self) -> None:
        """
        Checks regular and custom exports sort members before batching and retain Solr response order.
        """
        ids = [f'invented-{number:02d}' for number in range(25)]
        people = [
            {
                'faculty_uri': f'http://vivo.brown.edu/individual/{identifier}',
                'label': ('a' if number % 2 == 0 else 'B') + identifier,
            }
            for number, identifier in enumerate(ids)
        ]
        original = json.loads(self.responses[profile_key('org-example')].body)['response']['docs'][0]
        for identifier, custom in (('org-example', False), ('org-brown-univ-dept124', True)):
            with self.subTest(custom=custom):
                organization = dict(original)
                organization['id'] = f'http://vivo.brown.edu/individual/{identifier}'
                item = json.loads(organization['json_txt'][0])
                item['people'] = list(reversed(people)) + [people[0]]
                organization['json_txt'] = [json.dumps(item)]
                self.responses[profile_key(identifier)] = self.solr_response([organization], 1)
                ordered = sorted(people, key=lambda person: person['label'] if custom else person['label'].upper())
                ordered_ids = [person['faculty_uri'].rsplit('/', 1)[-1] for person in ordered]
                expected_ids: list[str] = []
                for start in range(0, len(ordered_ids), 20):
                    batch = ordered_ids[start : start + 20]
                    response_ids = list(reversed(batch))
                    expected_ids.extend(response_ids)
                    docs = [
                        {
                            'id': f'http://vivo.brown.edu/individual/{member_id}',
                            'record_type': ['PEOPLE'],
                            'json_txt': [
                                json.dumps({'name': member_id, 'contributor_to': [{'title': member_id, 'date': '2024'}]})
                            ],
                        }
                        for member_id in response_ids
                    ]
                    self.responses[member_details_key(batch)] = self.solr_response(docs, len(docs))
                body = organization_publications_data(identifier, 'live', self.read)
                actual_ids = [row.split('\t')[0].rsplit('/', 1)[-1] for row in body.splitlines()[1:]]
                self.assertEqual(actual_ids, expected_ids)
                self.assertEqual(len(actual_ids), len(ids))

    def test_organization_export_preserves_unicode_spaces_when_sorting_titles(self) -> None:
        """
        Checks export sorting preserves Unicode spaces without changing profile publication sorting.
        """
        key = member_details_key(['invented-a'])
        response = json.loads(self.responses[key].body)
        person = json.loads(response['response']['docs'][0]['json_txt'][0])
        person['contributor_to'] = [
            {'title': '\u2007Alpha', 'date': '2024'},
            {'title': 'Zulu', 'date': '2024'},
            {'title': ' Beta ', 'date': '2024'},
            {'title': '\u00a0Alpha', 'date': '2024'},
            {'title': 'Newest', 'date': '2025'},
        ]
        response['response']['docs'][0]['json_txt'] = [json.dumps(person)]
        self.responses[key] = self.solr_response(response['response']['docs'], 1)
        body = organization_publications_data('org-example', 'live', self.read)
        titles = [row.split('\t')[2] for row in body.splitlines()[1:]]
        self.assertEqual(titles, ['Newest', ' Beta ', 'Zulu', '\u00a0Alpha', '\u2007Alpha'])
        profile_publications, _ = publications(person)
        self.assertIn('Alpha', profile_publications[1]['html'])
        self.assertIn('Zulu', profile_publications[-1]['html'])

    def test_organization_publications_tsv_preserves_source_tabs_and_line_breaks(self) -> None:
        """
        Checks the download retains the reference's original field separators.
        """
        key = member_details_key(['invented-a'])
        source = json.loads(self.responses[key].body)
        person = json.loads(source['response']['docs'][0]['json_txt'][0])
        person['contributor_to'][0]['title'] = 'Example\tpublication\ncontinued'
        source['response']['docs'][0]['json_txt'] = [json.dumps(person)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(source).encode())
        body = organization_publications_data('org-example', 'live', self.read)
        self.assertIn('\tExample\tpublication\ncontinued\t', body)
        self.assertIn('"Example\tpublication\ncontinued." ', body)
        self.assertGreater(len(body.splitlines()), 2)

    def test_publication_export_citation_preserves_quotation_and_detail_spacing(self) -> None:
        """
        Checks raw citation text retains nested quotes, periods, markup and spacing.
        """
        self.assertEqual(
            publication_citation({'title': '"An "example".."', 'published_in': 'Example & <b>Journal</b>', 'date': '2024'}),
            '"An "example".."  <i>Example & <b>Journal</b></i>, 2024.',
        )
        self.assertEqual(publication_citation({'title': '“Example”'}), '"Example”.".')

    def test_publication_export_citation_preserves_numeric_and_empty_details(self) -> None:
        """
        Checks numeric details, blank venue fallback and empty non-null fields match Rails.
        """
        self.assertEqual(
            publication_citation({'published_in': ' ', 'venue': 'Example', 'volume': 3, 'issue': '', 'pages': '1–2'}),
            '<i>Example</i>, vol. 3, no., pp. 1–2.',
        )
        self.assertEqual(publication_citation({}), '.')

    def test_publication_export_citation_preserves_unicode_spacing_in_titles(self) -> None:
        """
        Checks the export retains a figure space that the reference's title trim preserves.
        """
        self.assertEqual(publication_citation({'title': '\u2007Example'}), '"\u2007Example.".')
        self.assertEqual(publication_citation({'title': ' Example\u2007\n'}), '"Example\u2007.".')

    def test_publication_export_type_keeps_absent_and_unrecognized_types_empty(self) -> None:
        """
        Checks an absent export type stays empty while known classes use reference labels.
        """
        for value in (None, '', 'urn:example:Article'):
            with self.subTest(value=value):
                self.assertEqual(publication_export_type({'type': value}), '')
        prefix = 'http://vivo.brown.edu/ontology/citation#'
        self.assertEqual(publication_export_type({'type': prefix + 'BookSection'}), 'Book Section')
        self.assertEqual(publication_export_type({'type': prefix + 'Citation'}), 'Other')

    def test_profile_json_encoding_preserves_values_and_reference_escaping(self) -> None:
        """
        Checks compact profile JSON escapes HTML and separators while preserving Unicode and nested values.
        """
        data: dict[str, object] = {
            'text': '<p>Réseau & "雪"\u00a0</p>\u2028\u2029',
            'nested': [None, False, {'label': 'literal \\u003c', 'number': 1.0}],
        }
        encoded = profile_json_text(data)
        expected = (
            '{"text":"\\u003cp\\u003eRéseau \\u0026 \\"雪\\"\u00a0\\u003c/p\\u003e\\u2028\\u2029",'
            '"nested":[null,false,{"label":"literal \\\\u003c","number":1.0}]}'
        )
        self.assertEqual(encoded, expected)
        self.assertEqual(json.loads(encoded), data)

    def test_profile_json_preserves_nested_reference_field_order(self) -> None:
        """
        Checks optional model fields keep source order and calculated fields follow Rails assignments.
        """
        raw = {
            'uri': 'urn:example:person',
            'education': [{'degree': 'PhD', 'school_name': ' School ', 'date': '2020'}],
            'on_the_web': [{'text': '', 'url': ' https://example.invalid ', 'uri': 'urn:example:web'}],
            'collaborators': [{'org_name': 'School', 'name': 'Colleague', 'uri': 'urn:example:colleague'}],
            'training': [{'country': 'Example', 'name': 'Training', 'start_date': '2020-01-01'}],
            'contributor_to': [{'title': 'Paper', 'authors': 'Researcher', 'date': '2020'}],
        }
        doc: dict[str, object] = {'json_txt': [json.dumps(raw)]}
        body = faculty_item_from_doc(doc, {}, {})
        expected = {
            'education': ['degree', 'school_name', 'date'],
            'on_the_web': ['text', 'url', 'uri', 'id', 'rank'],
            'collaborators': ['org_name', 'name', 'uri', 'id'],
            'training': ['country', 'name', 'start_date', 'end_date'],
            'contributor_to': ['title', 'authors', 'date', 'year', 'external_url'],
        }
        for field, names in expected.items():
            with self.subTest(field=field):
                rows = body[field]
                self.assertIsInstance(rows, list)
                if isinstance(rows, list):
                    self.assertEqual(list(rows[0]), names)

    def test_profile_json_routes_use_compact_reference_encoding(self) -> None:
        """
        Checks both person JSON route forms preserve compact values and the reference UTF-8 response header.
        """
        data = {'overview': '<p>Made-up & text</p>', 'name': 'Réseau', 'optional': None}
        with patch('vivo_app.views.profile_json_data', return_value=data):
            for path in ('/display/invented-a.json', '/display/invented-a?format=json'):
                with self.subTest(path=path):
                    response = self.get_page(path)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
                    self.assertEqual(response.content.decode(), profile_json_text(data))
                    self.assertEqual(json.loads(response.content), data)

    def test_sparse_profile_json_uses_graph_availability(self) -> None:
        """
        Checks profile JSON combines one person record with a graph-availability list.
        """
        sparse_doc = {
            'id': 'http://vivo.brown.edu/individual/invented-sparse',
            'record_type': ['PEOPLE'],
            'json_txt': [
                json.dumps({'uri': 'http://vivo.brown.edu/individual/invented-sparse', 'name': 'Sparse Researcher'})
            ],
            'display_name_s': 'Sparse Researcher',
            'show_visualizations_s': 'false',
        }
        self.responses[profile_export_key('invented-sparse')] = self.solr_response([sparse_doc], 1)
        self.responses[visualization_key('coauthors')] = RecordedResponse(
            200, (('content-type', 'application/json'),), b'{}'
        )
        with patch('vivo_app.lib.source_formats.read_source', side_effect=self.read):
            response = self.get_page('/display/invented-sparse.json')
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertEqual(body['name'], 'Sparse Researcher')
        self.assertIsNone(body['id'])
        self.assertEqual(body['has_coauthors'], False)
        self.assertEqual(body['research_areas'], [])
        self.responses.pop(visualization_key('coauthors'))
        with patch('vivo_app.lib.source_formats.read_source', side_effect=self.read):
            response = self.get_page('/display/invented-sparse.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['has_coauthors'], False)
        with self.assertRaises(PageDataError):
            profile_json_data('invented-sparse', 'replay', self.read_replay)

    def test_profile_json_survives_missing_collaborator_list(self) -> None:
        """
        Checks optional graph-list failure leaves collaborator details available.
        """
        key = profile_export_key('invented-a')
        doc = json.loads(self.responses[profile_key('invented-a')].body)['response']['docs'][0]
        person = json.loads(doc['json_txt'][0])
        person['uri'] = person['id']
        person['collaborators'] = [{'uri': 'http://vivo.brown.edu/individual/invented-b', 'name': 'Colleague'}]
        doc['json_txt'] = [json.dumps(person)]
        self.responses[key] = self.solr_response([doc], 1)
        with patch('vivo_app.lib.source_formats.read_source', side_effect=self.read):
            response = self.get_page('/display/invented-a.json')
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertEqual(len(body['collaborators']), 1)
        self.assertEqual(body['has_collaborators'], False)

    def test_display_raw_json_returns_person_and_organization_records(self) -> None:
        """
        Checks raw JSON format returns the source record for both supported display types.
        """
        with patch('vivo_app.lib.source_formats.read_source', side_effect=self.read):
            person = self.get_page('/display/invented-a?format=json_txt')
            organization = self.get_page('/display/org-example.json_txt')
            invalid = self.get_page('/display/invented-a?format=json_txt&extra=1')
        self.assertEqual(json.loads(person.content)['name'], 'Invented Researcher')
        self.assertEqual(json.loads(organization.content)['name'], 'Example Department')
        self.assertEqual(invalid.status_code, 503)

    def test_organization_json_contains_websites_and_members(self) -> None:
        """
        Checks organization JSON includes the public fields and member portraits.
        """
        with (
            patch('vivo_app.lib.source_formats.read_source', side_effect=self.read),
            patch('vivo_app.lib.source_teams.read_source', side_effect=self.read),
        ):
            response = self.get_page('/display/org-example?format=json')
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertEqual(body['record_type'], 'ORGANIZATION')
        self.assertEqual(body['name'], 'Example Department')
        self.assertEqual(body['web_pages'][0]['text'], 'Department website')
        self.assertEqual(body['people'][0]['label'], 'Researcher, Invented')
        self.assertEqual(body['people'][0]['thumbnail_url'], 'http://example.invalid/profile-images/123/4/portrait.jpg')

    def test_organization_json_preserves_source_website_order(self) -> None:
        """
        Checks organization JSON keeps source website order even when ranks differ.
        """
        key = profile_key('org-example')
        response = json.loads(self.responses[key].body)
        item = json.loads(response['response']['docs'][0]['json_txt'][0])
        item['web_pages'] = [
            {'rank': '2', 'url': 'https://example.invalid/later'},
            {'rank': '1', 'url': 'https://example.invalid/earlier'},
        ]
        response['response']['docs'][0]['json_txt'] = [json.dumps(item)]
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        with patch('vivo_app.lib.source_formats.read_source', side_effect=self.read):
            result = self.get_page('/display/org-example.json')
        body = json.loads(result.content)
        self.assertEqual(
            [row['url'] for row in body['web_pages']], ['https://example.invalid/later', 'https://example.invalid/earlier']
        )

    def test_nested_profile_json_converts_and_sorts_entries(self) -> None:
        """
        Checks publication, appointment, training, credential, and collaborator JSON fields.
        """
        uri = 'http://vivo.brown.edu/individual/invented-nested'
        raw = {
            'id': uri,
            'uri': uri,
            'name': 'Invented Nested',
            'contributor_to': [
                {'title': 'Earlier', 'date': '2010-01-01', 'url': 'https://example.invalid/earlier'},
                {'title': 'Later', 'date': '2024-01-01'},
                {'title': 'Malformed', 'date': '20201'},
            ],
            'appointments': [
                {'uri': 'invented-old', 'name': 'Older', 'start_date': '2010-01-01'},
                {
                    'uri': 'invented-new',
                    'name': 'Newer',
                    'hospital_name': 'Example Hospital',
                    'start_date': '2020-01-01',
                    'end_date': 'invalid',
                },
            ],
            'credentials': [
                {'uri': 'invented-earlier', 'name': 'Earlier Credential'},
                {'uri': 'invented-credential', 'name': 'Example Credential'},
            ],
            'training': [{'name': 'Example Training', 'start_date': '2018-01-01T00:00:00'}],
            'collaborators': [{'uri': 'invented-b', 'name': 'B'}, {'uri': 'invented-a', 'name': 'A'}],
            'education': [
                {'date': '2020', 'degree': 'First', 'school_name': '  Example School  '},
                {'date': '2020', 'degree': 'Second', 'school_name': 'Another School'},
            ],
            'on_the_web': [{'uri': 'invented-web', 'rank': '1', 'url': ' https://example.invalid/ ', 'text': ' '}],
        }
        doc = {'id': uri, 'record_type': ['PEOPLE'], 'json_txt': [json.dumps(raw)]}
        self.responses[profile_export_key('invented-nested')] = self.solr_response([doc], 1)
        self.responses[visualization_key('coauthors')] = RecordedResponse(
            200, (('content-type', 'application/json'),), json.dumps({uri: True}).encode()
        )
        self.responses[visualization_key('collaborators')] = RecordedResponse(
            200, (('content-type', 'application/json'),), json.dumps({uri: True}).encode()
        )
        with patch('vivo_app.lib.source_formats.read_source', side_effect=self.read):
            response = self.get_page('/display/invented-nested.json')
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertEqual([row['title'] for row in body['contributor_to']], ['Later', 'Earlier', 'Malformed'])
        self.assertEqual(body['contributor_to'][1]['external_url'], 'https://example.invalid/earlier')
        self.assertIsNone(body['contributor_to'][2]['year'])
        self.assertEqual(body['appointments'][0]['org_name'], 'Example Hospital')
        self.assertIsNone(body['appointments'][0]['end_date'])
        self.assertEqual([row['id'] for row in body['credentials']], ['invented-credential', 'invented-earlier'])
        self.assertEqual(body['training'][0]['start_date'], '2018-01-01')
        self.assertEqual([row['name'] for row in body['collaborators']], ['A', 'B'])
        self.assertEqual([row['degree'] for row in body['education']], ['Second', 'First'])
        self.assertEqual(body['education'][1]['school_name'], 'Example School')
        self.assertEqual(body['on_the_web'][0]['url'], 'https://example.invalid/')
        self.assertEqual(body['on_the_web'][0]['text'], '')
        self.assertTrue(body['has_coauthors'])
        self.assertTrue(body['has_collaborators'])

    def test_profile_json_preserves_empty_metadata(self) -> None:
        """
        Checks explicit empty display and update values remain empty in JSON.
        """
        doc = json.loads(self.responses[profile_key('invented-a')].body)['response']['docs'][0]
        person = json.loads(doc['json_txt'][0])
        person['uri'] = person['id']
        doc['json_txt'] = [json.dumps(person)]
        doc.update(display_name_s='', fis_updated_s='', profile_updated_s='')
        result = faculty_item_from_doc(doc, {}, {})
        for field in ('display_name', 'fis_updated', 'profile_updated'):
            self.assertEqual(result[field], '')
        doc['display_name_s'] = None
        self.assertEqual(faculty_item_from_doc(doc, {}, {})['display_name'], person['name'])

    def test_profile_json_preserves_null_identifiers_and_optional_values(self) -> None:
        """
        Checks null identifiers, names and CV values keep their reference types.
        """
        doc = json.loads(self.responses[profile_key('invented-a')].body)['response']['docs'][0]
        person = json.loads(doc['json_txt'][0])
        uri = person.pop('id')
        person['uri'] = uri
        person['affiliations'] = [{'uri': None, 'name': None}]
        person['collaborators'] = [{'uri': None, 'name': None}]
        person['appointments'] = [{'uri': None, 'hospital_name': '', 'org_name': 'Other organization'}]
        person['credentials'] = [{'uri': None}]
        person['cv'] = [{'cv_link': None}]
        doc['json_txt'] = [json.dumps(person)]
        result = faculty_item_from_doc(doc, {uri: True}, {uri: True})
        self.assertIsNone(result['id'])
        self.assertIsNone(result['cv_link'])
        self.assertFalse(result['has_coauthors'])
        self.assertFalse(result['has_collaborators'])
        for field in ('affiliations', 'collaborators', 'appointments', 'credentials'):
            rows = result[field]
            if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
                self.fail('Structured optional records should be a nonempty list.')
            self.assertIsNone(rows[0]['id'])
            self.assertIsNone(rows[0]['uri'])
        appointments = result['appointments']
        assert isinstance(appointments, list)
        self.assertEqual(appointments[0]['org_name'], '')
        affiliations = result['affiliations']
        assert isinstance(affiliations, list)
        self.assertIsNone(affiliations[0]['name'])

    def test_profile_json_converts_nested_scalar_arrays(self) -> None:
        """
        Checks nested array values follow the original Rails model conversions.
        """
        doc = json.loads(self.responses[profile_key('invented-a')].body)['response']['docs'][0]
        person = json.loads(doc['json_txt'][0])
        person['uri'] = person['id']
        person['contributor_to'] = [{'title': ['Example paper'], 'authors': ['Example author'], 'date': ['2024-01-01']}]
        person['appointments'] = [
            {
                'uri': ['urn:example:appointment'],
                'name': ['Example appointment'],
                'org_name': ['Example organization'],
                'start_date': ['2020-01-01'],
            }
        ]
        person['credentials'] = [{'uri': ['urn:example:credential'], 'number': ['123'], 'start_date': ['2019-01-01']}]
        person['training'] = [{'name': ['Example training'], 'city': ['Example City'], 'start_date': ['2018-01-01']}]
        person['education'] = [{'date': ['2012'], 'degree': ['Example degree'], 'school_name': [' Example school ']}]
        person['collaborators'] = [{'uri': ['urn:example:person'], 'name': ['Example collaborator']}]
        person['on_the_web'] = [
            {'uri': ['urn:example:web'], 'rank': ['2later'], 'url': [' https://example.invalid/ '], 'text': [None]}
        ]
        doc['json_txt'] = [json.dumps(person)]
        result = faculty_item_from_doc(doc, {}, {})
        expected = {
            'contributor_to': {'title': 'Example paper', 'authors': 'Example author', 'date': '2024-01-01', 'year': 2024},
            'appointments': {
                'id': 'urn:example:appointment',
                'name': 'Example appointment',
                'org_name': ['Example organization'],
                'start_date': '2020-01-01',
            },
            'credentials': {'id': 'urn:example:credential', 'number': '123', 'start_date': '2019-01-01'},
            'training': {'name': 'Example training', 'city': 'Example City', 'start_date': '2018-01-01'},
            'education': {'date': '2012', 'degree': 'Example degree', 'school_name': 'Example school'},
            'collaborators': {'id': 'urn:example:person', 'name': 'Example collaborator'},
            'on_the_web': {
                'id': 'urn:example:web',
                'rank': 2,
                'url': 'https://example.invalid/',
                'text': 'https://example.invalid/',
            },
        }
        for field, expected_values in expected.items():
            rows = result[field]
            if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
                self.fail('Structured optional records should be a nonempty list.')
            for name, value in expected_values.items():
                self.assertEqual(rows[0][name], value, f'{field}.{name}')

    def test_profile_json_accepts_website_rank_prefix(self) -> None:
        """
        Checks a saved website rank with trailing text follows Rails number conversion.
        """
        key = profile_export_key('invented-nested-rank')
        uri = 'http://vivo.brown.edu/individual/invented-nested-rank'
        raw = {
            'uri': uri,
            'on_the_web': [
                {'rank': '2later', 'url': 'https://example.invalid/later', 'source_only_field': 'private value'},
                {'rank': '1first', 'url': 'https://example.invalid/first'},
            ],
        }
        doc = {'id': uri, 'record_type': ['PEOPLE'], 'json_txt': [json.dumps(raw)]}
        self.responses[key] = self.solr_response([doc], 1)
        self.responses[visualization_key('coauthors')] = RecordedResponse(
            200, (('content-type', 'application/json'),), b'{}'
        )
        with patch('vivo_app.lib.source_formats.read_source', side_effect=self.read):
            result = self.get_page('/display/invented-nested-rank.json')
        self.assertEqual(result.status_code, 200)
        body = json.loads(result.content)
        self.assertEqual([row['rank'] for row in body['on_the_web']], [1, 2])
        self.assertNotIn('source_only_field', body['on_the_web'][1])

    def test_profile_json_publication_without_title_has_empty_title(self) -> None:
        """
        Checks an untitled publication uses the empty title supplied by Rails.
        """
        rows: dict[str, object] = {'contributor_to': [{'date': '2024'}]}
        self.assertEqual(publication_entries(rows)[0]['title'], '')

    def test_active_team_uses_external_members_and_solr_profiles(self) -> None:
        """
        Checks a configured active team builds its faculty rows without a team Solr record.
        """
        with TemporaryDirectory() as directory:
            manifest = Path(directory) / 'teams.json'
            manifest.write_text(
                json.dumps({'teams': {'team-example': {'name': 'Invented Team', 'member_ids': ['invented-a']}}})
            )
            with (
                override_settings(TEAM_SOURCE_MANIFEST=str(manifest)),
                patch('vivo_app.lib.source_teams.read_source', side_effect=self.read),
            ):
                result = team_data('team-example', 'live', self.read)
                self.assertEqual(result['name'], 'Invented Team')
                self.assertEqual(result['administrative_positions'], [])
                response = self.get_page('/display/team-example')
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Invented Researcher')
                with self.assertRaises(PageDataError):
                    team_data('team-missing', 'live', self.read)

    def test_active_team_skips_member_missing_from_solr(self) -> None:
        """Shows available team members when an older listed profile has vanished."""
        ids = ['invented-a', 'invented-b']
        person = json.loads(self.responses[team_member_key(['invented-a'])].body)['response']['docs'][0]
        self.responses[team_member_key(ids)] = self.solr_response([person], 1)
        with TemporaryDirectory() as directory:
            manifest = Path(directory) / 'teams.json'
            manifest.write_text(json.dumps({'teams': {'team-example': {'name': 'Invented Team', 'member_ids': ids}}}))
            with override_settings(TEAM_SOURCE_MANIFEST=str(manifest)):
                result = team_data('team-example', 'live', self.read)
        positions = result['faculty_positions']
        assert isinstance(positions, list)
        self.assertEqual(len(positions), 1)

    def test_team_member_links_keep_the_deployment_prefix(self) -> None:
        """
        Checks team member links remain inside a mounted Django application.
        """
        with TemporaryDirectory() as directory:
            manifest = Path(directory) / 'teams.json'
            manifest.write_text(
                json.dumps({'teams': {'team-example': {'name': 'Invented Team', 'member_ids': ['invented-a']}}})
            )
            previous_prefix = get_script_prefix()
            set_script_prefix('/mounted-app')
            try:
                with override_settings(TEAM_SOURCE_MANIFEST=str(manifest)):
                    result = team_data('team-example', 'live', self.read)
                positions = result['faculty_positions']
                self.assertIsInstance(positions, list)
                if not isinstance(positions, list):
                    self.fail('Team faculty positions were not a list.')
                self.assertEqual(positions[0]['url'], '/mounted-app/display/invented-a')
                self.assertEqual(result['visualization_url'], '/mounted-app/display/team-example/viz/collab')
            finally:
                set_script_prefix(previous_prefix)

    def test_custom_organization_adds_configured_members(self) -> None:
        """
        Checks a fixed custom member appears on the page and in its publication export.
        """
        added = {
            'id': 'http://vivo.brown.edu/individual/invented-b',
            'record_type': ['PEOPLE'],
            'display_name_s': 'Another Researcher',
            'json_txt': [
                json.dumps(
                    {
                        'name': 'Another Researcher',
                        'title': 'Example Lecturer',
                        'contributor_to': [
                            {
                                'type': 'http://vivo.brown.edu/ontology/citation#Article',
                                'title': 'Another publication',
                                'authors': 'Researcher, Another',
                                'date': '2023',
                            }
                        ],
                    }
                )
            ],
        }
        existing = json.loads(self.responses[member_details_key(['invented-a'])].body)['response']['docs'][0]
        self.responses[team_member_key(['invented-b'])] = self.solr_response([added], 1)
        self.responses[member_key(['invented-a', 'invented-b'])] = self.solr_response([existing, added], 2)
        self.responses[member_details_key(['invented-b', 'invented-a'])] = self.solr_response([existing, added], 2)
        with TemporaryDirectory() as directory:
            manifest = Path(directory) / 'members.json'
            manifest.write_text(
                json.dumps({'organizations': {'org-brown-univ-dept124': {'extra_member_ids': ['invented-b']}}})
            )
            with override_settings(TEAM_SOURCE_MANIFEST=str(manifest)):
                extras = custom_organization_members('org-brown-univ-dept124', 'live')
                result = organization_data('org-example', 'live', self.read, extras)
                faculty = result['faculty_positions']
                self.assertIsInstance(faculty, list)
                if not isinstance(faculty, list):
                    self.fail('Organization faculty positions are not a list.')
                self.assertEqual([row['name'] for row in faculty], ['Another Researcher', 'Researcher, Invented'])
                self.assertEqual(result['visualization_url'], '/display/org-example/viz/collab')
                preview = result['visualization_graph']
                self.assertIsInstance(preview, dict)
                if not isinstance(preview, dict):
                    self.fail('Organization preview was not an object.')
                self.assertEqual(len(preview['nodes']), 8)
                with override_settings(VIZ_ENABLED=False):
                    hidden = organization_data('org-example', 'live', self.read, extras)
                self.assertEqual(hidden['visualization_url'], '')
                export = organization_publications_data('org-example', 'live', self.read, extras)
                self.assertIn('Another publication', export)
                self.responses[team_member_key(['invented-b'])] = self.solr_response([], 0)
                missing = organization_data('org-example', 'live', self.read, extras)
                missing_faculty = missing['faculty_positions']
                self.assertIsInstance(missing_faculty, list)
                if not isinstance(missing_faculty, list):
                    self.fail('Organization faculty positions are not a list.')
                self.assertEqual(len(missing_faculty), 1)
                with self.assertRaises(PageDataError):
                    custom_organization_members('org-brown-univ-dept148', 'live', self.read)

    def test_research_area_organization_combines_query_and_fixed_members(self) -> None:
        """
        Checks the selected research areas and fixed IDs form one bounded member list.
        """
        key = community_research_members_key()
        self.assertTrue(any(name == 'fq' and value.startswith('research_areas:(') for name, value in key.query))
        area_member = {'id': 'http://vivo.brown.edu/individual/invented-c', 'record_type': ['PEOPLE']}
        self.responses[key] = self.solr_response([area_member], 1)
        with TemporaryDirectory() as directory:
            manifest = Path(directory) / 'members.json'
            manifest.write_text(
                json.dumps({'organizations': {'org-brown-univ-dept148': {'extra_member_ids': ['invented-b']}}})
            )
            with override_settings(TEAM_SOURCE_MANIFEST=str(manifest)):
                self.assertEqual(
                    custom_organization_members('org-brown-univ-dept148', 'live', self.read),
                    ['invented-b', 'invented-c'],
                )
                self.responses[key] = self.solr_response([area_member], 501)
                with self.assertRaises(PageDataError):
                    custom_organization_members('org-brown-univ-dept148', 'live', self.read)
