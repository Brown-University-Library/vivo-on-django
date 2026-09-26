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
            'query': 'Example', 'page': 1, 'page_size': 20, 'total': 1,
            'results': [{'id': 'invented-a', 'name': 'Invented Researcher', 'title': 'Example title',
                         'email': '', 'url': '/display/invented-a', 'thumbnail': '/__prepared_assets/portrait.png'}],
            'facets': [{'name': 'record_type', 'title': 'Type', 'values': [
                {'text': 'PEOPLE', 'count': 1, 'url': '/search?q=Example&fq=record_type%7CPEOPLE', 'selected': False}]}],
            'pagination': [{'label': '1', 'url': '/search?q=Example&page=1', 'current': True}],
            'previous_url': '', 'next_url': '', 'remove_query_url': '/search', 'selected_filters': [],
        }
        self.profile_data = {
            'id': 'invented-a', 'name': 'Invented Researcher', 'title': 'Example title',
            'thumbnail': '/__prepared_assets/portrait.png',
            'sections': [{'id': 'Overview', 'label': 'Overview', 'html': '<p>Invented overview.</p>'},
                         {'id': 'Research', 'label': 'Research', 'html': '<p>Invented research.</p>'}],
        }
        self.manifest: dict[str, object] = {
            'format_version': 1, 'bundle_version': 'test.1', 'data_origin': 'invented',
            'prepared_at': '2026-09-26T12:00:00+00:00', 'application_revision': 'invented-test-revision',
            'readme': self.save('README.md', b'Invented test bundle'),
            'assets': {'portrait.png': {**self.save('assets/portrait.png', b'invented-image'), 'content_type': 'image/png'},
                       'source-sans-pro.ttf': {**self.save('assets/font.woff2', b'invented-font'), 'content_type': 'font/woff2'}},
            'entries': {
                'search': {**self.save('data/search.json', json.dumps(self.search_data).encode()),
                           'family': 'search', 'path': '/search', 'query': [['q', 'Example']]},
                'profile': {**self.save('data/profile.json', json.dumps(self.profile_data).encode()),
                            'family': 'profile', 'path': '/display/invented-a', 'query': []},
                'facets': {**self.save('data/facets.json', b'[{"text":"Example","count":1}]'),
                           'family': 'response', 'path': '/search_facets', 'query': [['q', 'Example'], ['f_name', 'affiliations']],
                           'status': 200, 'content_type': 'application/json', 'headers': []},
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
        for url in ['/', '/display/invented-a/publications/', '/people/']:
            self.assertContains(self.get_page(url), 'not connected to prepared data', status_code=503)

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

    def test_invalid_modes_fail_startup(self) -> None:
        """
        Checks invalid and unimplemented source modes report configuration errors.
        """
        for mode in ('invalid', 'replay', 'live'):
            with self.subTest(mode=mode), override_settings(PAGE_DATA_MODE=mode):
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

        for changes in ({'name': None}, {'thumbnail': 'https://example.invalid/photo.jpg'},
                        {'sections': [{'id': 'Overview', 'label': 'Overview', 'html': '<script>bad()</script>'}]}):
            with self.subTest(changes=changes), self.assertRaises(PageDataError):
                validate_page('profile', {**self.profile_data, **changes}, {'portrait.png'})

    def test_template_errors_are_not_success(self) -> None:
        """
        Checks a broken prepared template cannot become a successful placeholder response.
        """
        with patch('vivo_app.views.render', side_effect=RuntimeError('broken template')):
            with self.assertRaisesRegex(RuntimeError, 'broken template'):
                self.get_page('/search?q=Example')
