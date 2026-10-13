"""
Checks public export reuse, expiry, definition changes, and separate worker generation.
"""

import json
import multiprocessing
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings

from vivo_app.lib.display_cache import cached_display, display_cache_key
from vivo_app.lib.page_errors import PageDataError
from vivo_app.lib.report_cache import cached_report, generation_lock, report_cache_key
from vivo_app.lib.reports import parse_report
from vivo_app.tests.test_display_exports import organization_doc, person_doc
from vivo_app.tests.test_report_entry import example_bundle, example_row
from vivo_app.tests.test_report_exports import solr_response


def display_worker(marker: str) -> None:
    """
    Records a completed public export from a separate worker process.

    Called by: DisplayCacheTests.test_processes_share_one_generation()
    """
    Path(marker).write_bytes(cached_display('invented-a').xml.body)


class DisplayCacheTests(SimpleTestCase):
    def setUp(self) -> None:
        """
        Checks caching with temporary file storage shared by test workers.
        """
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'members.json'
        self.path.write_text(json.dumps({'teams': {'team-example': {'name': 'Example', 'member_ids': ['invented-a']}}}))
        self.config = override_settings(
            REPORT_CACHE_TIMEOUT_SECONDS=28800,
            REPORT_CACHE_LOCK_DIR=self.directory.name + '/locks',
            TEAM_SOURCE_MANIFEST=str(self.path),
            SOLR_URL='https://source.invalid/solr',
            CACHES={
                'default': {
                    'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
                    'LOCATION': self.directory.name + '/cache',
                }
            },
        )
        self.config.enable()
        self.addCleanup(self.config.disable)

    def test_both_formats_fixed_expiry_and_custom_timeout(self) -> None:
        """
        Checks eight-hour and custom lifetimes start after generation and hits never extend them.
        """
        for timeout in [28800, 60]:
            with (
                override_settings(REPORT_CACHE_TIMEOUT_SECONDS=timeout),
                patch('vivo_app.lib.display_cache.display_files', return_value=(b'csv', b'xml')) as source,
            ):
                with patch('time.time', return_value=100):
                    first = cached_display('invented-a')
                self.assertEqual(first.generated_at, 100)
                self.assertEqual(first.csv.content_type, 'application/xml')
                with patch('time.time', return_value=100 + timeout - 1):
                    self.assertEqual(cached_display('invented-a').xml.body, b'xml')
                source.assert_called_once_with('invented-a')
                with patch('time.time', return_value=101 + timeout):
                    cached_display('invented-a')
                self.assertEqual(source.call_count, 2)

    def test_disabled_cache_and_failed_refresh(self) -> None:
        """
        Checks zero avoids all storage and locks, and failed refreshes do not return expired exports.
        """
        with (
            override_settings(REPORT_CACHE_TIMEOUT_SECONDS=0),
            patch('vivo_app.lib.display_cache.cache') as backend,
            patch('vivo_app.lib.display_cache.generation_lock') as lock,
            patch('vivo_app.lib.display_cache.display_files', return_value=(b'csv', b'xml')) as source,
        ):
            cached_display('invented-a')
            cached_display('invented-a')
            self.assertEqual(source.call_count, 2)
            backend.get.assert_not_called()
            backend.set.assert_not_called()
            lock.assert_not_called()
        with patch(
            'vivo_app.lib.display_cache.display_files',
            side_effect=[(b'csv', b'xml'), PageDataError('Example'), (b'new', b'new')],
        ):
            with patch('time.time', return_value=100):
                cached_display('invented-a')
            with patch('time.time', return_value=28901):
                with self.assertRaises(PageDataError):
                    cached_display('invented-a')
                self.assertIsNone(cache.get(display_cache_key('invented-a')))
                self.assertEqual(cached_display('invented-a').csv.body, b'new')

    def test_complete_organization_generation_is_shared_by_formats(self) -> None:
        """
        Checks a large organization's source reads and serialization happen once for both requested formats.
        """
        identifiers = [f'invented-{n:03}' for n in range(121)]
        responses = [solr_response([organization_doc(identifiers)])]
        responses.extend(
            solr_response([person_doc(identifier) for identifier in identifiers[start : start + 20]])
            for start in range(0, len(identifiers), 20)
        )
        with (
            patch('vivo_app.lib.display_exports.read_source', side_effect=responses) as source,
            patch('vivo_app.lib.reports.load_reports', side_effect=AssertionError('Public downloads cannot read reports')),
        ):
            csv = cached_display('org-example').csv
            xml = cached_display('org-example').xml
            self.assertIn(b'invented-120', csv.body)
            self.assertIn(b'invented-120', xml.body)
            self.assertEqual(source.call_count, 8)

    def test_key_changes_and_manifest_changes_during_generation(self) -> None:
        """
        Checks definitions, source, timeout, and code changes invalidate entries and unsafe IDs fail before cache reads.
        """
        key = display_cache_key('team-example')
        self.path.write_text(json.dumps({'teams': {'team-example': {'name': 'Updated', 'member_ids': ['invented-b']}}}))
        self.assertNotEqual(key, display_cache_key('team-example'))
        key = display_cache_key('invented-a')
        for setting in [{'SOLR_URL': 'https://different.invalid/solr'}, {'REPORT_CACHE_TIMEOUT_SECONDS': 30}]:
            with override_settings(**setting):
                self.assertNotEqual(key, display_cache_key('invented-a'))
        with patch('vivo_app.lib.display_cache.EXPORT_VERSION', 2):
            self.assertNotEqual(key, display_cache_key('invented-a'))
        with self.assertRaises(PageDataError):
            cached_display('bad"name')
        with (
            patch(
                'vivo_app.lib.display_cache.display_cache_key',
                side_effect=['display-export:first', 'display-export:changed'],
            ),
            patch('vivo_app.lib.display_cache.display_files', return_value=(b'csv', b'xml')),
            self.assertRaises(PageDataError),
        ):
            cached_display('team-example')
        self.assertIsNone(cache.get('display-export:first'))

    def test_public_and_protected_entries_and_locks_are_separate(self) -> None:
        """
        Checks shared timeout/storage cannot serve a public export as a staff report or block its distinct lock.
        """
        report = parse_report(example_row())
        with (
            patch('vivo_app.lib.display_cache.display_files', return_value=(b'public csv', b'public xml')),
            patch('vivo_app.lib.report_cache.generate_report', return_value=example_bundle()),
        ):
            public = cached_display('invented-a')
            protected = cached_report(report)
            self.assertNotEqual(public.csv.body, protected.csv.body)
            self.assertEqual(cached_display('invented-a'), public)
            self.assertEqual(cached_report(report), protected)
        public_key = display_cache_key('invented-a')
        report_key = report_cache_key(report)
        self.assertNotEqual(public_key, report_key)
        with generation_lock(public_key), generation_lock(report_key):
            pass

    def slow_files(self, identifier: str) -> tuple[bytes, bytes]:
        """
        Records source work and allows concurrent workers time to request the same export.

        Called by: test_processes_share_one_generation()
        """
        with (Path(self.directory.name) / 'generated').open('a') as handle:
            handle.write('generated\n')
        time.sleep(0.2)
        return b'csv', b'xml'

    def test_processes_share_one_generation(self) -> None:
        """
        Checks simultaneous public downloads in separate workers generate both formats only once.
        """
        context = multiprocessing.get_context('fork')
        with patch('vivo_app.lib.display_cache.display_files', side_effect=self.slow_files):
            workers = [context.Process(target=display_worker, args=(self.directory.name + f'/done-{n}',)) for n in range(3)]
            try:
                for worker in workers:
                    worker.start()
                for worker in workers:
                    worker.join(timeout=10)
                    self.assertEqual(worker.exitcode, 0)
            finally:
                for worker in workers:
                    if worker.is_alive():
                        worker.terminate()
                        worker.join()
        self.assertEqual((Path(self.directory.name) / 'generated').read_text(), 'generated\n')
        self.assertEqual(len(list(Path(self.directory.name).glob('done-*'))), 3)
