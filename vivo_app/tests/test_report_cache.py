"""
Checks completed-report reuse, invalidation, expiry, and coordination between workers.
"""

import multiprocessing
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings

from vivo_app.lib.report_cache import cached_report, generation_lock, report_cache_key
from vivo_app.lib.reports import Report, ReportError, parse_report
from vivo_app.tests.test_report_entry import example_bundle, example_row


def worker_download(report: Report, marker: str) -> None:
    """
    Requests a report in a separate process and records successful completion.

    Called by: ReportCacheTests.test_processes_share_one_generation()
    """
    bundle = cached_report(report)
    Path(marker).write_bytes(bundle.csv.body)


class ReportCacheTests(SimpleTestCase):
    def setUp(self) -> None:
        """
        Checks caching in temporary on-disk storage shared by test workers.
        """
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.config = override_settings(
            REPORT_CACHE_TIMEOUT_SECONDS=28800,
            REPORT_CACHE_LOCK_DIR=self.directory.name + '/locks',
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
        self.report = parse_report(example_row())

    def test_reuse_fixed_expiry_and_both_formats(self) -> None:
        """
        Checks both formats share a completed entry, hits do not extend expiry, and expired data regenerates.
        """
        with patch('vivo_app.lib.report_cache.generate_report', return_value=example_bundle()) as generate:
            with patch('time.time', return_value=100):
                first = cached_report(self.report)
            with patch('time.time', return_value=200):
                self.assertEqual(cached_report(self.report).xml, first.xml)
            with patch('time.time', return_value=28901):
                cached_report(self.report)
            self.assertEqual(generate.call_count, 2)

    def test_zero_bypasses_cache_and_failures_are_not_stored(self) -> None:
        """
        Checks disabled caching does no cache reads, writes, or locking, and failures can be retried.
        """
        with (
            override_settings(REPORT_CACHE_TIMEOUT_SECONDS=0),
            patch('vivo_app.lib.report_cache.cache') as backend,
            patch('vivo_app.lib.report_cache.generation_lock') as lock,
            patch('vivo_app.lib.report_cache.generate_report', return_value=example_bundle()) as generate,
        ):
            cached_report(self.report)
            cached_report(self.report)
            self.assertEqual(generate.call_count, 2)
            backend.get.assert_not_called()
            backend.set.assert_not_called()
            lock.assert_not_called()
        with patch(
            'vivo_app.lib.report_cache.generate_report', side_effect=[ReportError('Example'), example_bundle()]
        ) as generate:
            with self.assertRaises(ReportError):
                cached_report(self.report)
            self.assertIsNone(cache.get(report_cache_key(self.report)))
            self.assertEqual(cached_report(self.report), example_bundle())
            self.assertEqual(generate.call_count, 2)

    def test_keys_change_for_file_source_timeout_and_code(self) -> None:
        """
        Checks full row changes, source changes, timeout changes, and export versions select new entries.
        """
        original = report_cache_key(self.report)
        for field, value in [
            ('name', 'Changed'),
            ('description', 'Changed'),
            ('definition', '{"faculty_ids":[]}'),
            ('updated_at', '2026-01-01'),
        ]:
            self.assertNotEqual(original, report_cache_key(parse_report({**example_row(), field: value})))
        with override_settings(SOLR_URL='https://different.invalid/solr'):
            self.assertNotEqual(original, report_cache_key(self.report))
        with override_settings(REPORT_CACHE_TIMEOUT_SECONDS=60):
            self.assertNotEqual(original, report_cache_key(self.report))
        with patch('vivo_app.lib.report_cache.EXPORT_VERSION', 2):
            self.assertNotEqual(original, report_cache_key(self.report))
        self.assertNotIn('source.invalid', original)
        self.assertNotIn('Example', original)

    def slow_faculty(self, report: Report) -> list[dict[str, object]]:
        """
        Checks generation count through a shared file and allows workers time to overlap.
        """
        with (Path(self.directory.name) / 'generated').open('a') as handle:
            handle.write('generated\n')
        time.sleep(0.2)
        return [{'name': 'Example'}]

    def test_processes_share_one_generation(self) -> None:
        """
        Checks separate worker processes fetch faculty only once for the same report.
        """
        context = multiprocessing.get_context('fork')
        with patch('vivo_app.lib.report_cache.report_faculty', side_effect=self.slow_faculty):
            workers = [
                context.Process(target=worker_download, args=(self.report, self.directory.name + f'/done-{n}'))
                for n in range(3)
            ]
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

    def test_lock_wait_is_bounded_and_releases_after_error(self) -> None:
        """
        Checks waiting requests fail cleanly and an exception releases the held lock.
        """
        with (
            generation_lock('example'),
            patch('vivo_app.lib.report_cache.LOCK_WAIT_SECONDS', 0),
            self.assertRaises(ReportError),
            generation_lock('example'),
        ):
            self.fail('A second request obtained the same lock.')
        with self.assertRaises(ValueError), generation_lock('example'):
            raise ValueError('Example')
        with generation_lock('example'):
            pass
