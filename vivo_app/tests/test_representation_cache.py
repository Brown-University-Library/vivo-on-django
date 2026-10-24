"""
Checks VIVO download freshness, timeout recovery, and shared source reads with made-up data.
"""

import multiprocessing
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

from django.core.cache import cache
from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings

from vivo_app.lib.display_jsonld_cache import jsonld_cache_key
from vivo_app.lib.page_errors import PageDataError, SourceTimeoutError
from vivo_app.lib.reports import ReportError
from vivo_app.lib.source_representations import cached_representation, representation_cache_key
from vivo_app.lib.source_requests import read_source, vitro_key
from vivo_app.lib.source_types import RequestKey, SourceResponse


def representation_worker(marker: str) -> None:
    """
    Saves a download obtained by a separate application worker.

    Called by: RepresentationCacheTests.test_processes_share_source_reads()
    """
    response = cached_representation('invented-a', 'rdf', read_source)
    Path(marker).write_bytes(response.body)


class RepresentationCacheTests(SimpleTestCase):
    def setUp(self) -> None:
        """
        Checks downloads against isolated file storage and made-up source responses.
        """
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        config = override_settings(
            VIVO_EXPORT_CACHE_TIMEOUT_SECONDS=60,
            REPORT_CACHE_LOCK_DIR=self.directory.name + '/locks',
            VIVO_BACKEND_URL='https://source.invalid/vivo',
            CACHES={
                'default': {
                    'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
                    'LOCATION': self.directory.name + '/cache',
                }
            },
        )
        config.enable()
        self.addCleanup(config.disable)
        self.body = b'<?xml version="1.0"?>\n<rdf:RDF xmlns:rdf="urn:example:rdf"/>\n'
        self.responses = {
            vitro_key('invented-a', 'rdf'): SourceResponse(200, (), self.body),
            vitro_key('invented-a', 'ttl'): SourceResponse(200, (), b'@prefix ex: <urn:example:> .\n'),
            vitro_key('invented-a', 'jsonld'): SourceResponse(200, (), b'{"@id":"urn:example:record"}\n'),
        }
        self.requested: list[RequestKey] = []
        self.clock: Mock | None = None
        self.source_marker: Path | None = None
        self.enterContext(patch('vivo_app.views.read_source', side_effect=self.read))

    def read(self, key: RequestKey) -> SourceResponse:
        """
        Supplies made-up bytes and optionally records worker reads or advances the test clock.

        Called by: views.individual_export(), representation_worker() in tests
        """
        self.requested.append(key)
        if self.clock is not None:
            self.clock.return_value = 120
        if self.source_marker is not None:
            with self.source_marker.open('a') as handle:
                handle.write('read\n')
            time.sleep(0.1)
        return self.responses[key]

    def download(self, fmt: str = 'rdf', suffix: str = '', method: str = 'GET', prefix: str = '') -> HttpResponse:
        """
        Requests a public download through Django using isolated sources and storage.

        Called by: test methods
        """
        response = self.client.generic(method, f'/individual/invented-a/invented-a.{fmt}' + suffix, SCRIPT_NAME=prefix)
        assert isinstance(response, HttpResponse)
        return response

    def test_formats_keep_exact_bytes_and_share_head_slash_and_mount_forms(self) -> None:
        """
        Checks each format retains its own bytes and headers while aliases reuse a single source read.
        """
        for fmt, content_type in (('rdf', 'application/rdf+xml'), ('ttl', 'text/turtle'), ('jsonld', 'application/json')):
            first = self.download(fmt, method='HEAD')
            self.assertEqual(first.status_code, 200)
            self.assertEqual(first.content, b'')
            for suffix, prefix in (('', ''), ('/', ''), ('', '/mounted-app')):
                response = self.download(fmt, suffix, prefix=prefix)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, self.responses[vitro_key('invented-a', fmt)].body)
                self.assertEqual(response['Content-Type'], content_type + '; charset=utf-8')
                self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
                self.assertEqual(response['Content-Length'], first['Content-Length'])
                self.assertIn('no-store', response['Cache-Control'])
        self.assertEqual(self.requested, list(self.responses))

    def test_expiry_starts_after_fetch_and_hits_do_not_delay_updates(self) -> None:
        """
        Checks repeated downloads cannot extend the lifetime or delay new source data beyond it.
        """
        original = self.responses[vitro_key('invented-a', 'rdf')]
        updated = SourceResponse(200, (), b'<rdf:RDF>Updated example</rdf:RDF>')
        for timeout in (60, 30):
            with override_settings(VIVO_EXPORT_CACHE_TIMEOUT_SECONDS=timeout), patch('time.time', return_value=100) as clock:
                self.responses[vitro_key('invented-a', 'rdf')] = original
                self.clock = clock
                self.assertEqual(self.download().content, self.body)
                self.clock = None
                self.responses[vitro_key('invented-a', 'rdf')] = updated
                clock.return_value = 120 + timeout - 1
                self.assertEqual(self.download().content, self.body)
                clock.return_value = 120 + timeout + 1
                self.assertEqual(self.download().content, updated.body)
        self.assertEqual(len(self.requested), 4)

    def test_disabled_cache_reads_fresh_data_and_other_methods_skip_reads(self) -> None:
        """
        Checks disabled caching reads fresh data, while unsupported methods skip both sources and storage.
        """
        self.download()
        self.requested.clear()
        for timeout, method in ((0, 'GET'), (60, 'POST')):
            with (
                override_settings(VIVO_EXPORT_CACHE_TIMEOUT_SECONDS=timeout),
                patch('vivo_app.lib.source_representations.cache') as backend,
                patch('vivo_app.lib.source_representations.generation_lock') as lock,
            ):
                expected_status = 200 if method == 'GET' else 405
                self.assertEqual(self.download(method=method).status_code, expected_status)
                self.assertEqual(self.download(method=method).status_code, expected_status)
                backend.get.assert_not_called()
                backend.set.assert_not_called()
                lock.assert_not_called()
        self.assertEqual(len(self.requested), 2)

    def test_timeout_retries_once_and_caches_success_without_email(self) -> None:
        """
        Checks a successful retry preserves bytes and prevents later downloads from repeating source work.
        """
        with (
            patch(
                'vivo_app.views.read_source',
                side_effect=[SourceTimeoutError('Example timeout'), self.responses[vitro_key('invented-a', 'rdf')]],
            ) as source,
            patch('vivo_app.lib.source_representations.time.sleep') as pause,
            patch('django.utils.log.AdminEmailHandler.emit') as email,
            self.assertLogs('vivo_app.lib.source_representations', level='WARNING'),
        ):
            self.assertEqual(self.download().content, self.body)
            self.assertEqual(self.download().content, self.body)
        self.assertEqual(source.call_count, 2)
        pause.assert_called_once_with(0.25)
        email.assert_not_called()

    def test_repeated_timeouts_remain_uncached_without_email_and_recover(self) -> None:
        """
        Checks repeated timeouts return a clear temporary response, log warnings, and allow immediate recovery.
        """
        for debug in (False, True):
            for method in ('GET', 'HEAD'):
                with (
                    self.subTest(debug=debug, method=method),
                    override_settings(DEBUG=debug),
                    patch('vivo_app.views.read_source', side_effect=SourceTimeoutError('Example private detail')) as source,
                    patch('vivo_app.lib.source_representations.time.sleep'),
                    patch('django.utils.log.AdminEmailHandler.emit') as email,
                    self.assertLogs('vivo_app', level='WARNING') as logs,
                ):
                    response = self.download(method=method)
                self.assertEqual(response.status_code, 503)
                if method == 'GET':
                    self.assertContains(
                        response, 'Download temporarily unavailable. Please try again in a minute.', status_code=503
                    )
                else:
                    self.assertEqual(response.content, b'')
                self.assertNotIn(b'Example private detail', response.content)
                self.assertEqual(response['Content-Type'], 'text/plain; charset=utf-8')
                self.assertEqual(response['Retry-After'], '60')
                self.assertIn('no-store', response['Cache-Control'])
                self.assertEqual(source.call_count, 2)
                self.assertEqual(len(logs.records), 2)
                self.assertIsNone(cache.get(representation_cache_key('invented-a', 'rdf')))
                email.assert_not_called()
        self.assertEqual(self.download().content, self.body)

    def test_other_failures_keep_email_including_after_a_timeout(self) -> None:
        """
        Checks unrelated failures still alert administrators, even when they follow a timed-out first attempt.
        """
        failure = PageDataError('Example source failure')
        for failures in ([failure], [SourceTimeoutError('Example timeout'), failure]):
            with (
                patch('vivo_app.views.read_source', side_effect=failures) as source,
                patch('vivo_app.lib.source_representations.time.sleep') as pause,
                patch('django.utils.log.AdminEmailHandler.emit') as email,
                self.assertLogs('vivo_app', level='WARNING'),
            ):
                self.assertEqual(self.download().status_code, 503)
            self.assertEqual(source.call_count, len(failures))
            self.assertEqual(pause.call_count, len(failures) - 1)
            email.assert_called_once()
            self.assertIsNone(cache.get(representation_cache_key('invented-a', 'rdf')))

    def test_missing_records_are_not_cached(self) -> None:
        """
        Checks missing files retain their status and a newly available download appears immediately.
        """
        missing = SourceResponse(404, (), b'Example missing record')
        original = self.responses[vitro_key('invented-a', 'rdf')]
        self.responses[vitro_key('invented-a', 'rdf')] = missing
        for _ in range(2):
            response = self.download()
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.content, missing.body)
            self.assertIn('no-store', response['Cache-Control'])
        self.responses[vitro_key('invented-a', 'rdf')] = original
        self.assertEqual(self.download().content, self.body)
        self.assertEqual(len(self.requested), 3)

    def test_failed_refresh_does_not_return_expired_data(self) -> None:
        """
        Checks expired downloads are not served after a failed refresh and a later request can recover.
        """
        with patch('time.time', return_value=100):
            self.download()
        with patch('time.time', return_value=161):
            with (
                patch('vivo_app.views.read_source', side_effect=SourceTimeoutError('Example timeout')),
                patch('vivo_app.lib.source_representations.time.sleep'),
                self.assertLogs('vivo_app', level='WARNING'),
            ):
                self.assertEqual(self.download().status_code, 503)
            self.assertIsNone(cache.get(representation_cache_key('invented-a', 'rdf')))
            self.responses[vitro_key('invented-a', 'rdf')] = SourceResponse(200, (), b'Example updated download')
            self.assertEqual(self.download().content, b'Example updated download')

    def test_keys_separate_ids_formats_sources_lifetimes_and_versions(self) -> None:
        """
        Checks changed source settings cannot reuse old downloads or cached display data.
        """
        key = representation_cache_key('invented-a', 'rdf')
        self.assertEqual(
            len(
                {
                    key,
                    representation_cache_key('invented-b', 'rdf'),
                    representation_cache_key('invented-a', 'ttl'),
                    representation_cache_key('invented-a', 'jsonld'),
                    jsonld_cache_key('invented-a'),
                }
            ),
            5,
        )
        for setting in ({'VIVO_BACKEND_URL': 'https://changed.invalid'}, {'VIVO_EXPORT_CACHE_TIMEOUT_SECONDS': 30}):
            with override_settings(**setting):
                self.assertNotEqual(key, representation_cache_key('invented-a', 'rdf'))
        with patch('vivo_app.lib.source_representations.REPRESENTATION_VERSION', 2):
            self.assertNotEqual(key, representation_cache_key('invented-a', 'rdf'))
        with override_settings(REPORT_CACHE_TIMEOUT_SECONDS=28800, DISPLAY_JSONLD_CACHE_TIMEOUT_SECONDS=900):
            self.assertEqual(key, representation_cache_key('invented-a', 'rdf'))

    def test_invalid_requests_do_not_read_sources_or_cache(self) -> None:
        """
        Checks unsupported inputs cannot obtain an existing download from the cache.
        """
        self.download()
        self.requested.clear()
        for path, status in (
            ('/individual/invented-a/other.rdf', 404),
            ('/individual/invented-a/invented-a.unknown', 404),
            ('/individual/invented-a/invented-a.rdf?format=json', 400),
            ('/individual/bad%22name/bad%22name.rdf', 404),
        ):
            with patch('vivo_app.lib.source_representations.cache') as backend:
                response = self.client.get(path)
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, status)
                backend.get.assert_not_called()
                backend.set.assert_not_called()
        self.assertEqual(self.requested, [])

    def test_cache_storage_and_lock_failures_keep_error_alerts(self) -> None:
        """
        Checks storage failures and busy locks return an error with email instead of an unhandled exception.
        """
        for target, failure in (
            ('cache.get', OSError('Example read failure')),
            ('cache.set', OSError('Example write failure')),
            ('generation_lock', ReportError('Example lock wait failure')),
        ):
            with (
                patch('vivo_app.lib.source_representations.' + target, side_effect=failure),
                patch('django.utils.log.AdminEmailHandler.emit') as email,
                self.assertLogs('vivo_app', level='ERROR'),
            ):
                self.assertEqual(self.download().status_code, 503)
                email.assert_called_once()

    def test_processes_share_source_reads(self) -> None:
        """
        Checks simultaneous downloads in separate workers share one successful source read.
        """
        self.source_marker = Path(self.directory.name) / 'source-reads'
        context = multiprocessing.get_context('fork')
        workers = [
            context.Process(target=representation_worker, args=(self.directory.name + f'/done-{n}',)) for n in range(3)
        ]
        with patch(__name__ + '.read_source', side_effect=self.read):
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
        self.assertEqual(self.source_marker.read_text(), 'read\n')
        for n in range(3):
            self.assertEqual((Path(self.directory.name) / f'done-{n}').read_bytes(), self.body)
