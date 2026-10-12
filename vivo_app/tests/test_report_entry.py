"""
Checks protected report pages, private definitions, and attachment URLs.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings
from django.urls import get_script_prefix, set_script_prefix

from vivo_app.lib.report_cache import ReportBundle, ReportDownload
from vivo_app.lib.reports import (
    ReportError,
    cache_timeout,
    download_name,
    load_reports,
    parse_report,
    rails_integer,
    report_access,
)


def example_row() -> dict[str, object]:
    """
    Supplies made-up report data without any private source values.

    Called by: report tests
    """
    return {
        'id': 1,
        'user_id': None,
        'name': 'Example Report',
        'description': 'Example selection',
        'definition': '{"faculty_ids":["invented-a"]}',
        'created_at': None,
        'updated_at': None,
    }


def example_bundle() -> ReportBundle:
    """
    Supplies two distinguishable attachments without contacting Solr.

    Called by: report tests
    """
    return ReportBundle(
        ReportDownload(b'csv body\n', 'example_report.csv', 'text/plain; charset=utf-8'),
        ReportDownload(b'<xml/>', 'example_report.xml', 'application/xml; charset=utf-8'),
        100,
    )


@override_settings(
    SOLR_URL='https://source.invalid/solr',
    TURNSTILE_ENABLED=False,
    REPORTS_ALLOW_LOCAL_DEVELOPMENT=False,
    REPORTS_SHIB_ATTRIBUTE='Shibboleth-isMemberOf',
)
class ReportEntryTests(SimpleTestCase):
    def setUp(self) -> None:
        """
        Checks requests using a temporary private definition file.
        """
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'reports.json'
        self.path.write_text(json.dumps({'schema_version': 1, 'reports': [example_row()]}))
        self.config = override_settings(REPORT_DEFINITIONS_PATH=str(self.path))
        self.config.enable()
        self.addCleanup(self.config.disable)
        self.client.defaults['Shibboleth-isMemberOf'] = 'example-staff-group'

    def report_response(self, path: str, method: str = 'GET') -> HttpResponse:
        """
        Requires an HTTP response from the configured test client.

        Called by: ReportEntryTests
        """
        response = self.client.generic(method, path)
        assert isinstance(response, HttpResponse)
        return response

    def test_access_precedes_file_and_cache_reads(self) -> None:
        """
        Checks anonymous and header-only requests cannot read report files or cached downloads.
        """
        with patch('vivo_app.views.load_reports') as loader, patch('vivo_app.views.cached_report') as cached:
            for path in (
                '/reports/subject-lib',
                '/reports/subject-lib/',
                '/reports/subject-lib/1.csv',
                '/reports/subject-lib/1.xml',
                '/reports/subject-lib/1',
                '/reports/subject-lib/1/',
            ):
                for meta in ({}, {'HTTP_SHIBBOLETH_ISMEMBEROF': 'example'}, {'Shibboleth-isMemberOf': ' '}):
                    self.client.defaults = dict(meta)
                    response = self.report_response(path)
                    self.assertEqual(response.status_code, 403)
                    self.assertIn('no-store', response['Cache-Control'])
            loader.assert_not_called()
            cached.assert_not_called()

    def test_list_and_mounted_links(self) -> None:
        """
        Checks both list URLs render the report table and retain Django's mount prefix.
        """
        old = get_script_prefix()
        set_script_prefix('/mounted-app/')
        try:
            for path in ('/reports/subject-lib', '/reports/subject-lib/'):
                response = self.client.get(path, {'format': 'json'}, SCRIPT_NAME='/mounted-app')
                assert isinstance(response, HttpResponse)
                self.assertContains(response, 'Subject Librarian Reports')
                self.assertContains(response, 'Example Report')
                self.assertContains(response, '/mounted-app/reports/subject-lib/1.xml')
                self.assertContains(response, '/mounted-app/reports/subject-lib/1.csv')
                self.assertIn('no-store', response['Cache-Control'])
        finally:
            set_script_prefix(old)

    def test_download_forms_and_format_precedence(self) -> None:
        """
        Checks suffixes, queries, slash aliases, Ruby IDs, and default CSV behavior.
        """
        cases = [
            ('1.csv', b'csv body\n'),
            ('1.xml', b'<xml/>'),
            ('1', b'csv body\n'),
            ('1/', b'csv body\n'),
            ('1.xml/', b'<xml/>'),
            ('1.csv/', b'csv body\n'),
            ('1?format=xml', b'<xml/>'),
            ('1.csv?format=xml', b'csv body\n'),
            ('1.xml?format=csv', b'<xml/>'),
            ('1.json', b'csv body\n'),
            ('01suffix', b'csv body\n'),
        ]
        with patch('vivo_app.views.cached_report', return_value=example_bundle()):
            for suffix, body in cases:
                response = self.report_response('/reports/subject-lib/' + suffix)
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, 200, suffix)
                self.assertEqual(response.content, body)
                extension = 'xml' if body == b'<xml/>' else 'csv'
                self.assertEqual(response['Content-Disposition'], f'attachment; filename="example_report.{extension}"')
                self.assertIn('charset=utf-8', response['Content-Type'])
                self.assertIn('no-store', response['Cache-Control'])
            response = self.report_response('/reports/subject-lib/1.xml', 'HEAD')
            self.assertEqual(response.content, b'')
            self.assertEqual(response.status_code, 200)

    def test_errors_and_methods(self) -> None:
        """
        Checks unknown IDs, missing configuration, failures, and unsupported methods never become downloads.
        """
        response = self.report_response('/reports/subject-lib/missing?format=json')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Page not found', status_code=404)
        for path in ('/reports/subject-lib', '/reports/subject-lib/1.csv'):
            self.assertEqual(self.report_response(path, 'POST').status_code, 405)
        with patch('vivo_app.views.cached_report', side_effect=ReportError('Example failure')):
            response = self.report_response('/reports/subject-lib/1.csv')
            self.assertContains(response, 'Report unavailable', status_code=500)
        self.path.write_text('invalid')
        response = self.report_response('/reports/subject-lib/')
        self.assertContains(response, 'Report unavailable', status_code=500)
        self.assertNotIn(str(self.path).encode(), response.content)
        with override_settings(REPORT_DEFINITIONS_PATH=''):
            self.assertEqual(self.report_response('/about').status_code, 200)

    def test_second_format_reuses_faculty_and_access_still_applies(self) -> None:
        """
        Checks real handlers share one generation across formats and recheck access on cache hits.
        """
        with (
            override_settings(
                REPORT_CACHE_TIMEOUT_SECONDS=28800,
                REPORT_CACHE_LOCK_DIR=self.directory.name + '/locks',
                CACHES={
                    'default': {
                        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
                        'LOCATION': self.directory.name + '/cache',
                    }
                },
            ),
            patch('vivo_app.lib.report_cache.report_faculty', return_value=[{'name': 'Example Faculty'}]) as faculty,
        ):
            self.assertEqual(self.report_response('/reports/subject-lib/1.csv').status_code, 200)
            self.assertEqual(self.report_response('/reports/subject-lib/1.xml').status_code, 200)
            self.assertEqual(self.report_response('/reports/subject-lib/1/').status_code, 200)
            faculty.assert_called_once()
            self.client.defaults.clear()
            self.assertEqual(self.report_response('/reports/subject-lib/1.xml').status_code, 403)
            faculty.assert_called_once()

    def test_file_validation_and_replacement(self) -> None:
        """
        Checks invalid data fails clearly and file replacements are read immediately.
        """
        self.assertEqual(load_reports()[0].name, 'Example Report')
        row = example_row()
        row['name'] = 'Changed Example'
        self.path.write_text(json.dumps({'schema_version': 1, 'reports': [row]}))
        self.assertEqual(load_reports()[0].name, 'Changed Example')
        for data in (
            {'schema_version': True, 'reports': []},
            {'schema_version': 2, 'reports': []},
            {'schema_version': 1, 'reports': [row, row]},
            {'schema_version': 1, 'reports': None},
        ):
            self.path.write_text(json.dumps(data))
            with self.assertRaises(ReportError):
                load_reports()
        for field, value in [
            ('id', True),
            ('id', 0),
            ('definition', '{}oops'),
            ('definition', '{"unknown":[]}'),
            ('definition', '{"faculty_ids":[null]}'),
            ('definition', '{"faculty_ids":[""]}'),
            ('name', []),
            ('user_id', '1'),
            ('updated_at', 2),
        ]:
            row = {**example_row(), field: value}
            with self.subTest(field=field, value=value), self.assertRaises(ReportError):
                parse_report(row)
        with override_settings(BASE_DIR=self.path.parent, REPORT_DEFINITIONS_PATH='reports.json'):
            self.path.write_text(json.dumps({'schema_version': 1, 'reports': [example_row()]}))
            self.assertEqual(load_reports()[0].id, 1)

    def test_local_exception_requires_explicit_loopback_runserver(self) -> None:
        """
        Checks debug, hostnames, and loopback peers alone cannot enable local report access.
        """
        for debug, enabled, runserver, address, expected in (
            (True, True, True, '127.0.0.1', True),
            (True, True, True, '::1', True),
            (False, True, True, '127.0.0.1', False),
            (True, False, True, '127.0.0.1', False),
            (True, True, False, '127.0.0.1', False),
            (True, True, True, '192.0.2.1', False),
        ):
            with override_settings(DEBUG=debug, REPORTS_ALLOW_LOCAL_DEVELOPMENT=enabled, REPORTS_LOCAL_RUNSERVER=runserver):
                self.assertEqual(report_access({'REMOTE_ADDR': address, 'HTTP_HOST': 'localhost'}), expected)
        with override_settings(REPORTS_SHIB_ATTRIBUTE='HTTP_SHIBBOLETH_ISMEMBEROF'), self.assertRaises(ReportError):
            report_access({'HTTP_SHIBBOLETH_ISMEMBEROF': 'example'})

    def test_integer_and_filename_rules(self) -> None:
        """
        Checks timeout parsing, Ruby-style IDs, and Rails filenames.
        """
        for value, expected in [('28800', 28800), ('28_800', 28800), ('0', 0), ('60', 60)]:
            self.assertEqual(cache_timeout(value), expected)
        for value in ('-1', '1.5', 'bad', ''):
            with self.assertRaises(ImproperlyConfigured):
                cache_timeout(value)
        self.assertEqual(rails_integer(' +01tail'), 1)
        self.assertEqual(rails_integer('missing'), 0)
        for name, expected in [
            (None, 'untitled.csv'),
            ('  ', 'untitled.csv'),
            ('1 Example!', '_1_example_.csv'),
            ('Example Name', 'example_name.csv'),
            ('_Example', '__example.csv'),
        ]:
            self.assertEqual(download_name(name, 'csv'), expected)
