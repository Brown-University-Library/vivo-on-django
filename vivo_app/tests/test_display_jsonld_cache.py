"""
Checks legacy JSON-LD caching, freshness, source failures, and shared worker generation.
"""

import multiprocessing
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

from django.core.cache import cache
from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings

from vivo_app.lib.display_cache import display_cache_key
from vivo_app.lib.display_jsonld_cache import cached_display_data, jsonld_cache_key
from vivo_app.lib.page_errors import PageDataError
from vivo_app.lib.report_cache import generation_lock, report_cache_key
from vivo_app.lib.reports import parse_report
from vivo_app.lib.source_requests import profile_key, vitro_key
from vivo_app.lib.source_types import RequestKey, SourceResponse
from vivo_app.tests.source_fixtures import page_responses, solr_response
from vivo_app.tests.test_display_exports import person_doc
from vivo_app.tests.test_report_entry import example_row


def jsonld_worker(marker: str) -> None:
    """
    Records a JSON-LD response obtained by a separate application worker.

    Called by: DisplayJsonldCacheTests.test_processes_share_source_reads()
    """
    response = cached_display_data('/display/invented-other', [])
    assert isinstance(response, SourceResponse)
    Path(marker).write_bytes(response.body)


class DisplayJsonldCacheTests(SimpleTestCase):
    def setUp(self) -> None:
        """
        Checks caching with isolated file storage and made-up Solr and VIVO responses.
        """
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        config = override_settings(
            REPORT_CACHE_TIMEOUT_SECONDS=60,
            REPORT_CACHE_LOCK_DIR=self.directory.name + '/locks',
            SOLR_URL='https://source.invalid/solr',
            VIVO_BACKEND_URL='https://source.invalid/vivo',
            TURNSTILE_ENABLED=False,
            VIZ_ENABLED=False,
            CACHES={
                'default': {
                    'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
                    'LOCATION': self.directory.name + '/cache',
                }
            },
        )
        config.enable()
        self.addCleanup(config.disable)
        self.body = b'{\n "@id": "urn:example:record", "label": "Example & record"\n}\n'
        self.source_response = SourceResponse(200, (('content-type', 'application/json'),), self.body)
        doc = person_doc('invented-other')
        doc['record_type'] = ['UNCATEGORIZED']
        self.responses = {
            profile_key('invented-other'): solr_response([doc], 1),
            vitro_key('invented-other', 'jsonld'): self.source_response,
        }
        self.requested: list[RequestKey] = []
        self.source_marker: Path | None = None
        self.clock: Mock | None = None
        self.enterContext(patch('vivo_app.lib.source_pages.read_source', side_effect=self.read))
        self.enterContext(patch('vivo_app.lib.page_data.read_source', side_effect=self.read))

    def read(self, key: RequestKey) -> SourceResponse:
        """
        Supplies made-up source bytes and optionally records work across processes or advances time.

        Called by: get_display(), cached_display_data() in tests
        """
        self.requested.append(key)
        if self.source_marker is not None:
            with self.source_marker.open('a') as handle:
                handle.write(key.service + '\n')
            time.sleep(0.1)
        if key.service == 'vitro' and self.clock is not None:
            self.clock.return_value = 120
        response = self.responses.get(key)
        if response is None:
            raise PageDataError('Example source failure.')
        return response

    def get_display(self, path: str = '/display/invented-other', method: str = 'GET', prefix: str = '') -> HttpResponse:
        """
        Requests a display URL through Django with the test's isolated sources and cache.

        Called by: test methods
        """
        response = self.client.generic(method, path, SCRIPT_NAME=prefix)
        assert isinstance(response, HttpResponse)
        return response

    def test_hits_skip_both_sources_and_share_slash_mount_and_head_forms(self) -> None:
        """
        Checks cached bytes and headers survive aliases and HEAD without any more source reads.
        """
        first = self.get_display(method='HEAD')
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.content, b'')
        for suffix, prefix in (('', ''), ('/', ''), ('', '/mounted-app')):
            response = self.get_display('/display/invented-other' + suffix, prefix=prefix)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, self.body)
            self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
            self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(self.get_display(method='HEAD').content, b'')
        self.assertEqual(self.requested, [profile_key('invented-other'), vitro_key('invented-other', 'jsonld')])

    def test_expiry_starts_after_fetch_and_hits_do_not_extend_it(self) -> None:
        """
        Checks default and custom lifetimes start after source work and expire despite intervening hits.
        """
        for timeout in (28800, 60):
            with override_settings(REPORT_CACHE_TIMEOUT_SECONDS=timeout), patch('time.time', return_value=100) as clock:
                self.clock = clock
                self.requested.clear()
                self.get_display()
                self.clock = None
                clock.return_value = 120 + timeout - 1
                self.get_display()
                self.assertEqual(len(self.requested), 2)
                clock.return_value = 120 + timeout + 1
                self.get_display()
                self.assertEqual(len(self.requested), 4)

    def test_zero_bypasses_cache_and_locks(self) -> None:
        """
        Checks disabling caching reads fresh source data without touching storage or locks.
        """
        self.get_display()
        self.requested.clear()
        with (
            override_settings(REPORT_CACHE_TIMEOUT_SECONDS=0),
            patch('vivo_app.lib.display_jsonld_cache.cache') as backend,
            patch('vivo_app.lib.display_jsonld_cache.generation_lock') as lock,
        ):
            self.get_display()
            self.get_display()
            self.assertEqual(len(self.requested), 4)
            backend.get.assert_not_called()
            backend.set.assert_not_called()
            lock.assert_not_called()

    def test_failed_refresh_does_not_serve_expired_data(self) -> None:
        """
        Checks expired entries are not served after a failure and a later success can populate the cache.
        """
        with patch('time.time', return_value=100):
            self.get_display()
        del self.responses[vitro_key('invented-other', 'jsonld')]
        with patch('time.time', return_value=161):
            with self.assertLogs('vivo_app.views', level='ERROR'):
                failed = self.get_display()
            self.assertContains(failed, 'Oops! Something went wrong', status_code=500)
            self.assertIsNone(cache.get(jsonld_cache_key('invented-other')))
            self.responses[vitro_key('invented-other', 'jsonld')] = SourceResponse(200, (), b'{"label":"Updated"}')
            self.assertEqual(self.get_display().content, b'{"label":"Updated"}')
            self.requested.clear()
            self.assertEqual(self.get_display().content, b'{"label":"Updated"}')
            self.assertEqual(self.requested, [])

    def test_missing_records_and_upstream_404_are_not_cached(self) -> None:
        """
        Checks both Solr absence and VIVO not-found responses are fetched again on the next request.
        """
        for missing_source in ('solr', 'vitro'):
            with self.subTest(missing_source=missing_source):
                original = dict(self.responses)
                if missing_source == 'solr':
                    self.responses[profile_key('invented-other')] = solr_response([], 0)
                else:
                    self.responses[vitro_key('invented-other', 'jsonld')] = SourceResponse(404, (), b'{"error":"missing"}')
                self.requested.clear()
                for _ in range(2):
                    self.assertEqual(self.get_display().status_code, 404)
                self.assertEqual(len(self.requested), 2 if missing_source == 'solr' else 4)
                self.assertIsNone(cache.get(jsonld_cache_key('invented-other')))
                self.responses = original

    def test_html_pages_are_not_cached(self) -> None:
        """
        Checks person and organization HTML continue to read their sources each time.
        """
        self.responses.update(page_responses())
        for identifier in ('invented-a', 'org-example'):
            with self.subTest(identifier=identifier):
                self.requested.clear()
                for _ in range(2):
                    response = self.get_display('/display/' + identifier)
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response['Content-Type'].startswith('text/html'))
                self.assertEqual(self.requested.count(profile_key(identifier)), 2)
                self.assertIsNone(cache.get(jsonld_cache_key(identifier)))

    def test_keys_separate_ids_sources_timeouts_and_versions(self) -> None:
        """
        Checks source and lifetime changes require a fresh lookup and different IDs cannot share data.
        """
        self.get_display()
        key = jsonld_cache_key('invented-other')
        self.assertNotEqual(key, jsonld_cache_key('invented-second'))
        for setting in (
            {'SOLR_URL': 'https://changed.invalid/solr'},
            {'VIVO_BACKEND_URL': 'https://changed.invalid/vivo'},
            {'REPORT_CACHE_TIMEOUT_SECONDS': 30},
        ):
            with self.subTest(setting=setting), override_settings(**setting):
                self.assertNotEqual(key, jsonld_cache_key('invented-other'))
                self.requested.clear()
                self.get_display()
                self.assertEqual(len(self.requested), 2)
        with patch('vivo_app.lib.display_jsonld_cache.JSONLD_VERSION', 2):
            self.assertNotEqual(key, jsonld_cache_key('invented-other'))
            self.requested.clear()
            self.get_display()
            self.assertEqual(len(self.requested), 2)

    def test_exports_reports_and_jsonld_use_separate_entries_and_locks(self) -> None:
        """
        Checks existing exports and protected reports cannot supply or block the JSON-LD entry.
        """
        export_key = display_cache_key('invented-other')
        report_key = report_cache_key(parse_report(example_row()))
        key = jsonld_cache_key('invented-other')
        self.assertEqual(len({export_key, report_key, key}), 3)
        cache.set(export_key, b'Example export')
        cache.set(report_key, b'Example protected report')
        with generation_lock(export_key), generation_lock(report_key):
            self.assertEqual(self.get_display().content, self.body)
        self.assertEqual(cache.get(export_key), b'Example export')
        self.assertEqual(cache.get(report_key), b'Example protected report')

    def test_ignored_query_reuses_cache_and_post_reads_fresh_sources(self) -> None:
        """
        Checks unrelated parameters share cached bytes and POST retains fresh source reads.
        """
        self.get_display()
        self.requested.clear()
        with patch('vivo_app.lib.display_jsonld_cache.cache.set') as write:
            self.assertEqual(self.get_display('/display/invented-other?unexpected=1').content, self.body)
            write.assert_not_called()
        self.assertEqual(self.requested, [])
        self.responses[vitro_key('invented-other', 'jsonld')] = SourceResponse(200, (), b'{"label":"Fresh"}')
        self.assertEqual(self.get_display(method='POST').content, b'{"label":"Fresh"}')
        self.assertEqual(len(self.requested), 2)
        self.assertEqual(self.get_display().content, self.body)

    def test_tracking_request_populates_the_same_cache_entry(self) -> None:
        """
        Checks a first request with unrelated parameters creates the entry later used by a plain request.
        """
        response = self.get_display('/display/invented-other?utm_source=example&id=other&url=example')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.body)
        self.assertEqual(self.requested, [profile_key('invented-other'), vitro_key('invented-other', 'jsonld')])
        self.requested.clear()
        self.assertEqual(self.get_display().content, self.body)
        self.assertEqual(self.requested, [])

    def test_invalid_formats_do_not_read_or_replace_cached_jsonld(self) -> None:
        """
        Checks invalid and conflicting format requests return 400 before source reads or cache lookup.
        """
        self.get_display()
        self.requested.clear()
        for suffix in (
            '?format=',
            '?format=unknown',
            '?format=json&format=unknown',
            '?format=csv&format=json',
            '.json?format=json_txt',
            '.json_txt?format=json',
        ):
            with self.subTest(suffix=suffix), patch('vivo_app.views.cached_display_data') as cached:
                response = self.get_display('/display/invented-other' + suffix + '&utm_source=example')
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.content, b'Unsupported display format.')
                cached.assert_not_called()
        self.assertEqual(self.requested, [])
        self.assertEqual(self.get_display().content, self.body)

    def test_json_formats_with_tracking_keep_their_own_responses(self) -> None:
        """
        Checks explicit JSON and raw JSON cannot return or replace the cached legacy response.
        """
        self.get_display()
        self.requested.clear()
        for suffix, loader in (
            ('?format=json', 'profile_json_data'),
            ('.json?utm_medium=example', 'profile_json_data'),
            ('?format=json_txt', 'raw_record_json_data'),
            ('.json_txt?utm_medium=example', 'raw_record_json_data'),
        ):
            with (
                self.subTest(suffix=suffix),
                patch('vivo_app.views.' + loader, return_value={'name': 'Example explicit response'}) as source,
            ):
                response = self.get_display('/display/invented-other' + suffix + '&utm_source=example')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response['Content-Type'].split(';')[0], 'application/json')
                self.assertIn(b'Example explicit response', response.content)
                self.assertNotEqual(response.content, self.body)
                source.assert_called_once_with('invented-other')
        self.assertEqual(self.requested, [])
        self.assertEqual(self.get_display().content, self.body)

    def test_explicit_formats_do_not_use_jsonld_cache(self) -> None:
        """
        Checks a cached legacy response cannot replace explicit JSON, raw-JSON, or export handlers.
        """
        self.get_display()
        for path, loader in (
            ('/display/invented-other?format=json', 'profile_json_data'),
            ('/display/invented-other.json', 'profile_json_data'),
            ('/display/invented-other?format=json_txt', 'raw_record_json_data'),
            ('/display/invented-other.csv', 'cached_display'),
            ('/display/invented-other.xml', 'cached_display'),
        ):
            with (
                self.subTest(path=path),
                patch('vivo_app.views.' + loader, side_effect=PageDataError('Example format failure.')) as source,
                self.assertLogs('vivo_app.views', level='ERROR'),
            ):
                self.assertEqual(self.get_display(path).status_code, 500)
                source.assert_called_once()

    def test_invalid_id_and_storage_failure_keep_error_behavior(self) -> None:
        """
        Checks IDs are validated before cache reads and storage failures produce the display error page.
        """
        with patch('vivo_app.lib.display_jsonld_cache.cache') as backend:
            with self.assertRaises(PageDataError):
                cached_display_data('/display/bad"name', [])
            backend.get.assert_not_called()
        for operation in ('get', 'set'):
            with (
                self.subTest(operation=operation),
                patch(
                    'vivo_app.lib.display_jsonld_cache.cache.' + operation, side_effect=OSError('Example storage failure')
                ),
                self.assertLogs('vivo_app.views', level='ERROR'),
            ):
                self.assertEqual(self.get_display().status_code, 500)
            self.assertIsNone(cache.get(jsonld_cache_key('invented-other')))

    def test_processes_share_source_reads(self) -> None:
        """
        Checks simultaneous requests in separate workers fetch Solr and VIVO only once.
        """
        self.source_marker = Path(self.directory.name) / 'source-reads'
        context = multiprocessing.get_context('fork')
        workers = [context.Process(target=jsonld_worker, args=(self.directory.name + f'/done-{n}',)) for n in range(3)]
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
        self.assertEqual(self.source_marker.read_text(), 'solr\nvitro\n')
        for n in range(3):
            self.assertEqual((Path(self.directory.name) / f'done-{n}').read_bytes(), self.body)
