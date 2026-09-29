"""
Checks invented prepared bundles without using real records or live services.
"""

import hashlib
import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.http import HttpResponse
from django.test import TestCase, override_settings

from vivo_app.checks import check_page_data
from vivo_app.lib.page_data import cached_bundle
from vivo_app.lib.page_fields import validate_profile, validate_search
from vivo_app.lib.prepared_data import PageDataError, load_bundle, request_key


class PreparedDataTests(TestCase):
    """Exercises file validation and complete local request handling."""

    def setUp(self) -> None:
        """
        Checks use an external temporary directory and invented page content.
        """
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.search_data = {
            'query': 'Example',
            'page': 1,
            'page_size': 20,
            'total': 1,
            'results': [
                {
                    'id': 'invented-a',
                    'name': 'Invented Researcher',
                    'title': 'Example title',
                    'email': '',
                    'url': '/display/invented-a',
                    'thumbnail': '/__prepared_assets/portrait.png',
                }
            ],
            'facets': [
                {
                    'name': 'record_type',
                    'title': 'Type',
                    'values': [
                        {'text': 'PEOPLE', 'count': 1, 'url': '/search?q=Example&fq=record_type%7CPEOPLE', 'selected': False}
                    ],
                }
            ],
            'pagination': [{'label': '1', 'url': '/search?q=Example&page=1', 'current': True}],
            'previous_url': '',
            'next_url': '',
            'remove_query_url': '/search',
            'selected_filters': [],
        }
        self.profile_data: dict[str, object] = {
            'id': 'invented-a',
            'name': 'Invented Researcher',
            'title': 'Example title',
            'thumbnail': '/__prepared_assets/portrait.png',
            'sections': [
                {'id': 'Overview', 'label': 'Overview', 'html': '<p>Invented overview.</p>'},
                {'id': 'Research', 'label': 'Research', 'html': '<p>Invented research.</p>'},
            ],
        }
        self.manifest: dict[str, object] = {
            'format_version': 1,
            'bundle_version': 'test.1',
            'data_origin': 'invented',
            'prepared_at': '2026-09-26T12:00:00+00:00',
            'application_revision': 'invented-test-revision',
            'readme': self.save('README.md', b'Invented test bundle'),
            'assets': {
                'portrait.png': {**self.save('assets/portrait.png', b'invented-image'), 'content_type': 'image/png'},
                'source-sans-pro.ttf': {**self.save('assets/font.woff2', b'invented-font'), 'content_type': 'font/woff2'},
            },
            'entries': {
                'search': {
                    **self.save('data/search.json', json.dumps(self.search_data).encode()),
                    'family': 'search',
                    'path': '/search',
                    'query': [['q', 'Example']],
                },
                'profile': {
                    **self.save('data/profile.json', json.dumps(self.profile_data).encode()),
                    'family': 'profile',
                    'path': '/display/invented-a',
                    'query': [],
                },
                'facets': {
                    **self.save('data/facets.json', b'[{"text":"Example","count":1}]'),
                    'family': 'response',
                    'path': '/search_facets',
                    'query': [['q', 'Example'], ['f_name', 'affiliations']],
                    'status': 200,
                    'content_type': 'application/json',
                    'headers': [],
                },
            },
            'cases': {'journey': ['search', 'profile', 'facets']},
        }
        self.write_manifest()
        cached_bundle.cache_clear()
        self.addCleanup(cached_bundle.cache_clear)
        self.config = override_settings(PAGE_DATA_MODE='prepared', PREPARED_FIXTURE_DIR=str(self.root))
        self.config.enable()
        self.addCleanup(self.config.disable)

    def save(self, name: str, body: bytes) -> dict[str, str]:
        """
        Writes an invented file and returns its checksum.

        Called by: setUp()
        """
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        return {'file': name, 'sha256': hashlib.sha256(body).hexdigest()}

    def write_manifest(self) -> None:
        """
        Saves the current test manifest.

        Called by: setUp(), test methods
        """
        (self.root / 'manifest.json').write_text(json.dumps(self.manifest))

    def get_page(self, url: str) -> HttpResponse:
        """
        Checks the Django client result is an HTTP response.

        Called by: test methods
        """
        response = self.client.get(url)
        assert isinstance(response, HttpResponse)
        return response

    def test_search_profile_and_return(self) -> None:
        """
        Checks HTML rendering, optional tabs, and the preserved search return URL without network access.
        """
        with patch('socket.socket.connect', side_effect=AssertionError('Unexpected network connection')):
            response = self.get_page('/search?q=Example&page=1')
            self.assertContains(response, 'Invented Researcher')
            self.assertTemplateUsed(response, 'search/results.html')
            self.assertContains(response, 'aria-current="page"')
            response = self.get_page('/display/invented-a')
            self.assertContains(response, 'Invented overview.')
            self.assertContains(response, 'Invented research.')
            self.assertContains(response, 'tabResearchBtn')
            self.assertNotContains(response, 'tabTeachingBtn')
            self.assertContains(response, '/search?q=Example&amp;page=1')
            self.assertNotContains(response, 'Mock Person')
            self.assertIn("connect-src 'self'", response['Content-Security-Policy'])
            self.assertNotContains(response, 'fonts.googleapis.com')
            self.assertContains(response, '/static/css/fonts.css')
            self.assertNotContains(response, '/__prepared_assets/source-sans-pro.ttf')

    def test_saved_pages_accept_deployment_prefix(self) -> None:
        """
        Checks saved search and profile routes use paths without the server prefix.
        """
        search = self.client.get('/search?q=Example', SCRIPT_NAME='/vivo_on_django')
        profile = self.client.get('/display/invented-a', SCRIPT_NAME='/vivo_on_django')
        self.assertContains(search, 'Invented Researcher')
        self.assertContains(profile, 'Invented overview.')

    def test_application_fonts_do_not_require_a_bundle_font(self) -> None:
        """
        Checks that prepared HTML uses application fonts even when its bundle contains no font.
        """
        assets = self.manifest['assets']
        assert isinstance(assets, dict)
        del assets['source-sans-pro.ttf']
        self.write_manifest()
        response = self.get_page('/display/invented-a')
        self.assertContains(response, 'Invented overview.')
        self.assertContains(response, '/static/css/fonts.css')

    def test_unsaved_state_does_not_fall_back(self) -> None:
        """
        Checks unsupported filters and unknown profiles fail clearly instead of returning samples.
        """
        for url in ['/search?q=Example&fq=missing', '/display/n123', '/search?q=Example&format=json']:
            response = self.get_page(url)
            self.assertContains(response, 'No prepared state', status_code=503)
            self.assertNotIn(b'Stub', response.content)

    def test_unconverted_route_is_not_sample_success(self) -> None:
        """
        Checks unconverted public endpoints fail explicitly in prepared mode.
        """
        for url in ['/display/invented-a/publications/', '/search/advanced/']:
            self.assertContains(self.get_page(url), 'not connected to prepared data', status_code=503)

    def test_prepared_organization_roles_and_member_navigation(self) -> None:
        """
        Checks saved role order, repeated members, images, and a linked profile without network access.
        """
        organization = {
            'id': 'org-example',
            'name': 'Invented Department',
            'page_title': 'Invented Department',
            'image': '/__prepared_assets/portrait.png',
            'website_links': [{'label': 'Department website', 'url': 'https://example.invalid/department'}],
            'overview_html': '<p>Invented department overview.</p>',
            'visualization_url': '',
            'visualization_graph': {'view_box': '0 0 100 100', 'lines': [], 'nodes': []},
            'administrative_positions': [
                {
                    'name': 'Invented Researcher',
                    'title': 'Invented chair',
                    'url': '/display/invented-a',
                    'image': '/__prepared_assets/portrait.png',
                }
            ],
            'faculty_positions': [
                {
                    'name': 'Invented Researcher',
                    'title': 'Invented professor',
                    'url': '/display/invented-a',
                    'image': '/__prepared_assets/portrait.png',
                }
            ],
        }
        entries = self.manifest['entries']
        assert isinstance(entries, dict)
        entries['organization'] = {
            **self.save('data/organization.json', json.dumps(organization).encode()),
            'family': 'organization',
            'path': '/display/org-example',
            'query': [],
        }
        self.manifest['cases'] = {'journey': ['search', 'profile', 'facets', 'organization']}
        self.write_manifest()
        with patch('socket.socket.connect', side_effect=AssertionError('Unexpected network connection')):
            response = self.get_page('/display/org-example')
            self.assertContains(response, 'Invented department overview.')
            self.assertContains(response, 'Faculty Administrative Positions')
            self.assertContains(response, 'Faculty Positions')
            self.assertEqual(response.content.count(b'href="/display/invented-a"'), 2)
            self.assertLess(response.content.index(b'Invented chair'), response.content.index(b'Invented professor'))
            self.assertContains(self.get_page('/display/invented-a'), 'Invented overview.')
            self.assertEqual(self.get_page('/display/org-missing').status_code, 503)

    def test_prepared_home_and_saved_book_groups(self) -> None:
        """
        Checks the homepage uses saved backgrounds and book order, then follows a prepared profile.
        """
        home = {
            'backgrounds': ['/__prepared_assets/portrait.png'],
            'book_covers_paginated': [
                [
                    {
                        'title': 'Invented first book',
                        'author_url': '/display/invented-a',
                        'image_url': '/__prepared_assets/portrait.png',
                    }
                ],
                [
                    {
                        'title': 'Invented second book',
                        'author_url': '/display/invented-a',
                        'image_url': '/__prepared_assets/portrait.png',
                    }
                ],
            ],
        }
        entries = self.manifest['entries']
        assert isinstance(entries, dict)
        entries['home'] = {
            **self.save('data/home.json', json.dumps(home).encode()),
            'family': 'home',
            'path': '/',
            'query': [],
        }
        self.manifest['cases'] = {'journey': ['search', 'profile', 'facets', 'home']}
        self.write_manifest()
        with patch('socket.socket.connect', side_effect=AssertionError('Unexpected network connection')):
            response = self.get_page('/')
            self.assertContains(response, 'Invented first book')
            self.assertContains(response, 'Invented second book')
            self.assertContains(response, 'background-image: url(/__prepared_assets/portrait.png)')
            self.assertContains(response, 'alt="A clip art visualization of a simple network"')
            self.assertContains(self.get_page('/display/invented-a'), 'Invented overview.')
        self.assertEqual(self.get_page('/?unsupported=yes').status_code, 503)

    def test_prepared_legacy_redirect_reaches_saved_profile(self) -> None:
        """
        Checks an exact saved 303 redirect and its local destination without a slash hop.
        """
        entries = self.manifest['entries']
        assert isinstance(entries, dict)
        entries['redirect'] = {
            **self.save('responses/redirect.html', b'<a href="/display/invented-a">Moved</a>'),
            'family': 'response',
            'path': '/individual/invented-a',
            'query': [],
            'status': 303,
            'content_type': 'text/html; charset=utf-8',
            'headers': [['Location', '/display/invented-a'], ['Cache-Control', 'no-cache']],
        }
        self.manifest['cases'] = {'journey': ['search', 'profile', 'facets', 'redirect']}
        self.write_manifest()
        with patch('socket.socket.connect', side_effect=AssertionError('Unexpected network connection')):
            response = self.get_page('/individual/invented-a')
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response['Location'], '/display/invented-a')
            self.assertEqual(response['Cache-Control'], 'no-cache')
            final = self.client.get('/individual/invented-a', follow=True)
            assert isinstance(final, HttpResponse)
            self.assertContains(final, 'Invented overview.')
            self.assertEqual(final['Cache-Control'], 'max-age=0, private, must-revalidate')

    def test_repeated_filters_are_retained(self) -> None:
        """
        Checks repeated filters cannot collapse to a different saved request.
        """
        first = request_key('/search', [('q', 'Example'), ('fq', 'a'), ('fq', 'b')])
        reordered_keys = request_key('/search/', [('fq', 'a'), ('fq', 'b'), ('q', 'Example')])
        self.assertEqual(first, reordered_keys)
        self.assertNotEqual(first, request_key('/search', [('q', 'Example'), ('fq', 'b')]))
        self.assertNotEqual(first, request_key('/search', [('q', 'Example'), ('fq', 'b'), ('fq', 'a')]))

    def test_response_bytes_and_assets(self) -> None:
        """
        Checks saved JSON bytes and listed assets are served without interpretation.
        """
        response = self.get_page('/search_facets?q=Example&f_name=affiliations')
        self.assertEqual(response.content, b'[{"text":"Example","count":1}]')
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(self.get_page('/__prepared_assets/portrait.png').content, b'invented-image')
        self.assertEqual(self.get_page('/__prepared_assets/absent.png').status_code, 404)

    def test_selected_filter_labels(self) -> None:
        """
        Checks category labels can hide on narrow screens while the value and removal name remain available.
        """
        self.search_data['selected_filters'] = [
            {
                'label': 'Research Areas: Invented field',
                'category': 'Research Areas',
                'value': 'Invented field',
                'url': '/search?q=Example',
            }
        ]
        entries = self.manifest['entries']
        assert isinstance(entries, dict)
        entries['search'].update(self.save('data/search.json', json.dumps(self.search_data).encode()))
        self.write_manifest()
        response = self.get_page('/search?q=Example')
        self.assertContains(response, '<span class="facet-category">Research Areas: </span>')
        self.assertContains(response, 'Remove filter Invented field')
        self.assertNotContains(response, 'Remove filter Research Areas:')

    def test_selected_filter_category_requires_value(self) -> None:
        """
        Checks incomplete or nontext separated labels fail before rendering.
        """
        for fields in [
            {'category': 'Type'},
            {'value': 'PEOPLE'},
            {'category': 'Type', 'value': 4},
            {'category': '', 'value': 'PEOPLE'},
        ]:
            self.search_data['selected_filters'] = [{'label': 'Invented', 'url': '/search', **fields}]
            with self.subTest(fields=fields), self.assertRaises(PageDataError):
                validate_search(self.search_data, {'portrait.png'})

    def test_profile_publications_and_contacts(self) -> None:
        """
        Checks saved contact fields, publication ordering, controls, and hidden section links.
        """
        self.profile_data.update(
            email='invented@example.invalid',
            cv_url='',
            publications=[
                {'type': '_article', 'html': '<em>First invented article</em>'},
                {'type': '_book', 'html': '<em>Second invented book</em>'},
            ],
            publication_filters=[
                {'id': '_article', 'label': 'Article', 'count': 1},
                {'id': '_book', 'label': 'Book', 'count': 1},
            ],
        )
        sections = self.profile_data['sections']
        assert isinstance(sections, list)
        sections.append({'id': 'Publications', 'label': 'Publications', 'html': '<h3>Publications</h3>'})
        entries = self.manifest['entries']
        assert isinstance(entries, dict)
        entries['profile'].update(self.save('data/profile.json', json.dumps(self.profile_data).encode()))
        self.write_manifest()
        response = self.get_page('/display/invented-a')
        self.assertContains(response, 'mailto:invented@example.invalid')
        self.assertContains(response, 'Example title')
        self.assertContains(response, 'View All (2)')
        self.assertContains(response, 'Article (1)')
        self.assertContains(response, 'data-publication-type="_book"')
        self.assertLess(response.content.index(b'First invented article'), response.content.index(b'Second invented book'))
        self.assertNotContains(response, 'Curriculum Vitae [PDF]')

    def test_publication_counts_must_match(self) -> None:
        """
        Checks missing groups, wrong counts, and absent sections fail validation.
        """
        self.profile_data['publications'] = [{'type': '_article', 'html': '<p>Invented article</p>'}]
        for filters in ([], [{'id': '_article', 'label': 'Article', 'count': 2}]):
            self.profile_data['publication_filters'] = filters
            with self.assertRaises(PageDataError):
                validate_profile(self.profile_data, {'portrait.png'})
        self.profile_data['publication_filters'] = [{'id': '_article', 'label': 'Article', 'count': 1}]
        with self.assertRaises(PageDataError):
            validate_profile(self.profile_data, {'portrait.png'})

    def test_saved_search_controls_render(self) -> None:
        """
        Checks complete facet lists and formatted search matches render from invented data.
        """
        self.search_data['results'][0].update(
            matches_html='<p>Studies <strong>Example</strong> subjects.</p>', matches_url='/display/invented-a#All'
        )
        self.search_data['facets'][0]['more_values'] = [
            {'text': f'Example {index}', 'count': index, 'url': f'/search?q=Example&fq=type%7C{index}', 'selected': False}
            for index in range(25)
        ]
        entries = self.manifest['entries']
        assert isinstance(entries, dict)
        entries['search'].update(self.save('data/search.json', json.dumps(self.search_data).encode()))
        self.write_manifest()
        response = self.get_page('/search?q=Example')
        self.assertContains(response, 'modal_form_record_type')
        self.assertContains(response, 'aria-labelledby="modal_title_record_type"')
        self.assertContains(response, 'facet-data-record_type')
        self.assertContains(response, 'data-facet-action="alphabetical"')
        self.assertContains(response, '<strong>Example</strong>', html=True)
        self.assertContains(response, 'href="/display/invented-a#All"')
        self.assertContains(response, 'js/search_controls.js')

    def test_search_preview_validation(self) -> None:
        """
        Checks malformed previews and destinations cannot enter the rendered page.
        """
        result = self.search_data['results'][0]
        for markup, url in [
            ('<p>Example</p>', ''),
            ('<img src="/image.png">', '/display/invented-a#All'),
            ('<strong title="extra">Example</strong>', '/display/invented-a#All'),
            ('<p>Example</p>', '/display/different#All'),
        ]:
            result.update(matches_html=markup, matches_url=url)
            with self.subTest(markup=markup, url=url), self.assertRaises(PageDataError):
                validate_search(self.search_data, {'portrait.png'})

    def test_complete_facet_list_validation(self) -> None:
        """
        Checks repeated labels, nonlocal links, and invalid counts in dialog data.
        """
        facet = self.search_data['facets'][0]
        value = {'text': 'Example', 'count': 1, 'url': '/search?q=Example', 'selected': False}
        for values in [
            [value, value],
            [{**value, 'count': -1}],
            [{**value, 'url': 'https://example.invalid/search'}],
            [{**value, 'selected': 'false'}],
        ]:
            facet['more_values'] = values
            with self.subTest(values=values), self.assertRaises(PageDataError):
                validate_search(self.search_data, {'portrait.png'})

    def test_prepared_cv_delivery_and_missing_response(self) -> None:
        """
        Checks CV bytes and query parameters and rejects profiles with missing documents.
        """
        self.profile_data['cv_url'] = '/docs/example/cv.pdf?version=1'
        entries = self.manifest['entries']
        assert isinstance(entries, dict)
        entries['profile'].update(self.save('data/profile.json', json.dumps(self.profile_data).encode()))
        self.write_manifest()
        with self.assertRaisesRegex(PageDataError, 'saved PDF'):
            load_bundle(self.root)
        body = b'%PDF-1.4\nInvented document for response testing.'
        entries['cv'] = {
            **self.save('responses/cv.pdf', body),
            'family': 'response',
            'path': '/docs/example/cv.pdf',
            'query': [['version', '1']],
            'status': 200,
            'content_type': 'application/pdf',
            'headers': [],
        }
        self.manifest['cases'] = {'journey': ['search', 'profile', 'facets', 'cv']}
        self.write_manifest()
        response = self.get_page('/docs/example/cv.pdf?version=1')
        self.assertEqual(response.content, body)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertContains(self.get_page('/display/invented-a'), '/docs/example/cv.pdf?version=1')
        self.assertEqual(self.get_page('/docs/example/cv.pdf?version=2').status_code, 503)
        with override_settings(PAGE_DATA_MODE='prototype'):
            self.assertEqual(self.get_page('/docs/example/cv.pdf?version=1').status_code, 404)

    def test_invalid_modes_fail_startup(self) -> None:
        """
        Checks unknown modes and missing source settings report configuration errors.
        """
        for mode in ('invalid', 'replay', 'live'):
            with (
                self.subTest(mode=mode),
                override_settings(PAGE_DATA_MODE=mode, SOLR_URL='', UPSTREAM_RECORDING_MANIFEST=''),
            ):
                self.assertEqual(check_page_data()[0].id, 'vivo_app.E001')
                self.assertEqual(self.get_page('/search?q=Example').status_code, 503)
                self.assertEqual(self.get_page('/').status_code, 503)

    def test_validator_reports_origin(self) -> None:
        """
        Checks the command states invented origin and does not claim integration.
        """
        output = io.StringIO()
        call_command('validate_prepared_data', str(self.root), stdout=output)
        report = json.loads(output.getvalue())
        self.assertEqual(report['data_origin'], 'invented')
        self.assertEqual(report['source_integration'], 'not_verified')
        self.assertEqual(report['cases'], 1)

    def test_corrupt_and_missing_files(self) -> None:
        """
        Checks altered data and missing assets invalidate the whole bundle.
        """
        path = self.root / 'data/search.json'
        path.write_text('{}')
        with self.assertRaisesRegex(PageDataError, 'checksum'):
            load_bundle(self.root)
        path.unlink()
        with self.assertRaisesRegex(PageDataError, 'missing'):
            load_bundle(self.root)

    def test_unknown_version_and_case(self) -> None:
        """
        Checks unsupported versions and absent case references fail validation.
        """
        self.manifest['format_version'] = 99
        self.write_manifest()
        with self.assertRaisesRegex(PageDataError, 'version'):
            load_bundle(self.root)
        self.manifest['format_version'] = 1
        self.manifest['cases'] = {'broken': ['absent']}
        self.write_manifest()
        with self.assertRaisesRegex(PageDataError, 'absent'):
            load_bundle(self.root)

    def test_manifest_errors_identify_missing_and_invalid_files(self) -> None:
        """
        Checks a deployment can distinguish a missing manifest from invalid JSON.
        """
        manifest_path = self.root / 'manifest.json'
        manifest_path.unlink()
        with self.assertRaisesRegex(PageDataError, 'missing or unreadable'):
            load_bundle(self.root)
        manifest_path.write_text('{')
        with self.assertRaisesRegex(PageDataError, 'invalid JSON'):
            load_bundle(self.root)

    def test_file_escape_and_git_checkout(self) -> None:
        """
        Checks bundle files cannot leave the directory or live inside a Git checkout.
        """
        self.manifest['readme'] = {'file': '../outside.md', 'sha256': 'not-used'}
        self.write_manifest()
        with self.assertRaisesRegex(PageDataError, 'leaves'):
            load_bundle(self.root)
        (self.root / '.git').mkdir()
        with self.assertRaisesRegex(PageDataError, 'Git checkout'):
            load_bundle(self.root)

    def test_missing_fields_and_remote_assets(self) -> None:
        """
        Checks page fields, rich content, and asset references before rendering.
        """
        from vivo_app.lib.page_fields import validate_page

        for changes in (
            {'name': None},
            {'thumbnail': 'https://example.invalid/photo.jpg'},
            {'sections': [{'id': 'Overview', 'label': 'Overview', 'html': '<script>bad()</script>'}]},
        ):
            with self.subTest(changes=changes), self.assertRaises(PageDataError):
                validate_page('profile', {**self.profile_data, **changes}, {'portrait.png'})

    def test_template_errors_are_not_success(self) -> None:
        """
        Checks a broken prepared template cannot become a successful placeholder response.
        """
        with (
            patch('vivo_app.views.render', side_effect=RuntimeError('broken template')),
            self.assertRaisesRegex(RuntimeError, 'broken template'),
        ):
            self.get_page('/search?q=Example')
