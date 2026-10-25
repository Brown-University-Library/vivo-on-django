"""
Checks chart caching and prompt updates using made-up chart results and temporary storage.
"""

import json
import logging
import multiprocessing
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

from django.core import mail
from django.core.cache import cache
from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings

from vivo_app.lib.organization_chart_cache import cached_chart, chart_cache_key
from vivo_app.lib.page_errors import ChartRetryError, MissingRecordError, PageDataError, SourceTimeoutError
from vivo_app.lib.reports import ReportError


def chart_worker(builder: Mock, destination: str) -> None:
    """
    Saves a chart built or reused by a separate application worker.

    Called by: OrganizationChartCacheTests worker-sharing tests
    """
    try:
        result = cached_chart('org-example', 'research', builder)
    except ChartRetryError as exc:
        result = {'retry_after': exc.retry_after, 'cached': exc.cached}
    Path(destination).write_text(json.dumps(result))


class OrganizationChartCacheTests(SimpleTestCase):
    def setUp(self) -> None:
        """
        Checks chart caching with temporary files and a separate short lifetime.
        """
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.enterContext(
            override_settings(
                CHART_CACHE_TIMEOUT_SECONDS=60,
                REPORT_CACHE_LOCK_DIR=self.directory.name + '/locks',
                CACHES={
                    'default': {
                        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
                        'LOCATION': self.directory.name + '/cache',
                    }
                },
            )
        )
        self.publications: dict[str, object] = {
            'matrix': [{'year': 2020, 'total': 1, 'invented-a': 1}],
            'years': ['2020'],
            'columns': ['invented-a'],
            'nodes': [{'faculty_id': 'invented-a', 'name': 'Invented A', 'group': 'Professor'}],
        }
        self.research: dict[str, object] = {'nodes': [[], []], 'links': []}
        self.result = ('Example Organization', self.research)

    def test_formats_and_head_share_one_successful_generation_per_chart(self) -> None:
        """
        Checks HTML, JSON, CSV, HEAD, and mounted requests reuse each chart without extending browser caching.
        """
        with (
            patch(
                'vivo_app.views.publication_history_data', return_value=('Example Organization', self.publications)
            ) as pubs,
            patch('vivo_app.views.research_areas_data', return_value=self.result) as research,
        ):
            for kind, suffixes in (('publications', ('', '.json', '.csv')), ('research', ('', '.json'))):
                for suffix in suffixes:
                    response = self.client.get('/display/org-example/viz/' + kind + suffix)
                    assert isinstance(response, HttpResponse)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn('no-store', response['Cache-Control'])
                    if not suffix:
                        self.assertContains(response, 'Example Organization')
                    elif suffix == '.json':
                        expected = self.publications if kind == 'publications' else self.research
                        self.assertEqual(json.loads(response.content), expected)
                    else:
                        self.assertContains(response, 'year,year_total,invented-a\n2020,1,1')
                head = self.client.head('/display/org-example/viz/' + kind + '.json', SCRIPT_NAME='/mounted')
                assert isinstance(head, HttpResponse)
                self.assertEqual(head.status_code, 200)
                self.assertEqual(head.content, b'')
            pubs.assert_called_once_with('org-example')
            research.assert_called_once_with('org-example')

    def test_expiry_starts_after_generation_and_hits_do_not_extend_it(self) -> None:
        """
        Checks a replacement appears sixty seconds after completion even when requests keep arriving.
        """
        with patch('time.time', return_value=100) as clock:
            self.clock = clock
            builder = Mock(side_effect=self.delayed_chart)
            self.assertEqual(cached_chart('org-example', 'research', builder), self.result)
            builder.side_effect = None
            builder.return_value = ('Updated Organization', self.research)
            clock.return_value = 189
            self.assertEqual(cached_chart('org-example', 'research', builder), self.result)
            clock.return_value = 191
            self.assertEqual(cached_chart('org-example', 'research', builder)[0], 'Updated Organization')
        self.assertEqual(builder.call_count, 2)

    def delayed_chart(self, identifier: str) -> tuple[str, dict[str, object]]:
        """
        Advances the clock to represent a slow successful source read.

        Called by: test_expiry_starts_after_generation_and_hits_do_not_extend_it()
        """
        self.clock.return_value = 130
        return self.result

    def test_zero_disables_cache_reads_writes_and_locks(self) -> None:
        """
        Checks disabling caching always builds fresh chart results.
        """
        builder = Mock(return_value=self.result)
        with (
            override_settings(CHART_CACHE_TIMEOUT_SECONDS=0),
            patch('vivo_app.lib.organization_chart_cache.cache') as backend,
            patch('vivo_app.lib.organization_chart_cache.generation_lock') as lock,
        ):
            cached_chart('org-example', 'research', builder)
            cached_chart('org-example', 'research', builder)
            backend.get.assert_not_called()
            backend.set.assert_not_called()
            lock.assert_not_called()
        self.assertEqual(builder.call_count, 2)

    def test_missing_chart_is_retried_on_the_next_request(self) -> None:
        """
        Checks missing records stay uncached and recover on the next request.
        """
        with patch(
            'vivo_app.views.research_areas_data', side_effect=[MissingRecordError('Example missing record.'), self.result]
        ) as builder:
            response = self.client.get('/display/org-example/viz/research.json')
            assert isinstance(response, HttpResponse)
            self.assertEqual(response.status_code, 404)
            self.assertIn('no-store', response['Cache-Control'])
            self.assertIsNone(cache.get(chart_cache_key('org-example', 'research')))
            for _ in range(2):
                response = self.client.get('/display/org-example/viz/research.json')
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(json.loads(response.content), self.research)
            self.assertEqual(builder.call_count, 2)

    def delayed_failure(self, identifier: str) -> tuple[str, dict[str, object]]:
        """
        Advances the clock to represent a slow source failure.

        Called by: test_failure_delay_starts_after_failure_and_hits_do_not_extend_it()
        """
        self.clock.return_value = 130
        raise SourceTimeoutError('Example slow source.')

    def test_failure_delay_starts_after_failure_and_hits_do_not_extend_it(self) -> None:
        """
        Checks a corrected chart appears ten seconds after failure despite repeated requests during the delay.
        """
        with patch('time.time', return_value=100) as clock:
            self.clock = clock
            builder = Mock(side_effect=self.delayed_failure)
            with self.assertRaises(ChartRetryError) as first:
                cached_chart('org-example', 'research', builder)
            self.assertEqual(first.exception.retry_after, 10)
            self.assertFalse(first.exception.cached)
            self.assertIsInstance(first.exception.__cause__, SourceTimeoutError)
            builder.side_effect = None
            builder.return_value = self.result
            for now, remaining in ((131, 9), (135, 5), (139.1, 1)):
                clock.return_value = now
                with self.assertRaises(ChartRetryError) as repeated:
                    cached_chart('org-example', 'research', builder)
                self.assertTrue(repeated.exception.cached)
                self.assertEqual(repeated.exception.retry_after, remaining)
            builder.assert_called_once()
            clock.return_value = 140
            self.assertEqual(cached_chart('org-example', 'research', builder), self.result)
            self.assertEqual(builder.call_count, 2)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        ADMINS=[('Test administrator', 'admin@example.invalid')],
        SERVER_EMAIL='errors@example.invalid',
    )
    def test_failed_formats_share_warning_and_delay_without_email(self) -> None:
        """
        Checks all chart formats and HEAD share one warning, show the remaining delay, and recover without email.
        """
        for debug in (False, True):
            for kind, loader, result, suffixes in (
                (
                    'publications',
                    'publication_history_data',
                    ('Example Organization', self.publications),
                    ('', '.json', '.csv'),
                ),
                ('research', 'research_areas_data', self.result, ('', '.json')),
            ):
                cache.clear()
                with (
                    self.subTest(debug=debug, kind=kind),
                    override_settings(DEBUG=debug),
                    patch('time.time', return_value=100) as clock,
                    patch('vivo_app.views.' + loader, side_effect=[PageDataError('Example outage.'), result]) as builder,
                    patch.object(
                        logging.getLogger('django.request'), 'warning', wraps=logging.getLogger('django.request').warning
                    ) as warning,
                    patch('vivo_app.lib.page_rendering.logger.warning') as details,
                ):
                    for suffix in suffixes:
                        for method in ('get', 'head'):
                            response = getattr(self.client, method)('/display/org-example/viz/' + kind + suffix)
                            assert isinstance(response, HttpResponse)
                            self.assertEqual(response.status_code, 503)
                            self.assertEqual(response['Retry-After'], '10')
                            self.assertIn('no-store', response['Cache-Control'])
                            if method == 'head':
                                self.assertEqual(response.content, b'')
                            else:
                                self.assertIn(b'temporarily unavailable', response.content)
                            self.assertNotIn(b'Example outage.', response.content)
                    builder.assert_called_once()
                    warning.assert_called_once()
                    details.assert_not_called()
                    error = warning.call_args.kwargs['exc_info']
                    self.assertEqual(str(error.__cause__), 'Example outage.')
                    self.assertIsNotNone(error.__cause__.__traceback__)
                    clock.return_value = 109
                    response = self.client.get('/display/org-example/viz/' + kind + '.json?utm_source=example')
                    assert isinstance(response, HttpResponse)
                    self.assertEqual(response['Retry-After'], '1')
                    warning.assert_called_once()
                    clock.return_value = 110
                    response = self.client.get('/display/org-example/viz/' + kind + '.json')
                    assert isinstance(response, HttpResponse)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(json.loads(response.content), result[1])
                    self.assertNotIn('Retry-After', response)
                    self.assertEqual(builder.call_count, 2)
                    self.assertEqual(vars(mail)['outbox'], [])

    def test_continuing_failure_is_retried_only_after_each_delay(self) -> None:
        """
        Checks continuing failures are attempted again after each delay while other charts remain available.
        """
        builder = Mock(side_effect=PageDataError('Example ongoing outage.'))
        healthy = Mock(return_value=self.result)
        with patch('time.time', return_value=100) as clock:
            for now, cached in ((100, False), (109, True), (110, False), (119, True), (120, False)):
                clock.return_value = now
                with self.assertRaises(ChartRetryError) as failure:
                    cached_chart('org-example', 'research', builder)
                self.assertEqual(failure.exception.cached, cached)
            self.assertEqual(builder.call_count, 3)
            self.assertEqual(cached_chart('org-other', 'research', healthy), self.result)
            self.assertEqual(cached_chart('org-example', 'publications', healthy), self.result)
            self.assertEqual(healthy.call_count, 2)

    @override_settings(CHART_CACHE_TIMEOUT_SECONDS=0)
    def test_disabled_cache_retries_failures_immediately(self) -> None:
        """
        Checks disabling caching also disables the failure delay without changing the original exception.
        """
        builder = Mock(side_effect=[PageDataError('Example outage.'), self.result])
        with (
            patch('vivo_app.lib.organization_chart_cache.cache') as backend,
            patch('vivo_app.lib.organization_chart_cache.generation_lock') as lock,
        ):
            with self.assertRaisesRegex(PageDataError, 'Example outage.'):
                cached_chart('org-example', 'research', builder)
            self.assertEqual(cached_chart('org-example', 'research', builder), self.result)
            backend.get.assert_not_called()
            backend.set.assert_not_called()
            lock.assert_not_called()

    @override_settings(
        DEBUG=False,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        ADMINS=[('Test administrator', 'admin@example.invalid')],
        SERVER_EMAIL='errors@example.invalid',
    )
    def test_unexpected_failures_remain_uncached_and_email_once_per_request(self) -> None:
        """
        Checks code errors remain visible with one traceback email per failed request while chart caching is enabled.
        """
        self.client.raise_request_exception = False
        with patch('vivo_app.views.research_areas_data', side_effect=RuntimeError('Made-up code failure.')) as builder:
            for _ in range(2):
                response = self.client.get('/display/org-example/viz/research.json')
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, 500)
                self.assertIsNone(cache.get(chart_cache_key('org-example', 'research')))
                self.assertNotIn(b'Made-up code failure.', response.content)
            self.assertEqual(builder.call_count, 2)
        messages = vars(mail)['outbox']
        self.assertEqual(len(messages), 2)
        for message in messages:
            self.assertIn('RuntimeError', message.body)
            self.assertIn('cached_chart', message.body)
            self.assertIn('Made-up code failure.', message.body)

    def test_failed_refresh_does_not_return_an_expired_chart(self) -> None:
        """
        Checks failed refreshes do not serve expired content and a later request can succeed.
        """
        builder = Mock(side_effect=[self.result, PageDataError('Example outage.'), self.result])
        with patch('time.time', return_value=100):
            cached_chart('org-example', 'research', builder)
        with patch('time.time', return_value=161) as clock:
            with self.assertRaises(PageDataError):
                cached_chart('org-example', 'research', builder)
            clock.return_value = 170
            with self.assertRaises(ChartRetryError):
                cached_chart('org-example', 'research', builder)
            self.assertEqual(builder.call_count, 2)
            clock.return_value = 171
            self.assertEqual(cached_chart('org-example', 'research', builder), self.result)

    def test_keys_separate_source_settings_organizations_and_chart_kinds(self) -> None:
        """
        Checks unrelated charts and changed source settings cannot reuse the same cached result.
        """
        original = chart_cache_key('org-example', 'research')
        self.assertNotEqual(original, chart_cache_key('org-other', 'research'))
        self.assertNotEqual(original, chart_cache_key('org-example', 'publications'))
        for change in ({'SOLR_URL': 'https://changed.invalid/solr'}, {'CHART_CACHE_TIMEOUT_SECONDS': 30}):
            with override_settings(**change):
                self.assertNotEqual(original, chart_cache_key('org-example', 'research'))
        with patch('vivo_app.lib.organization_chart_cache.CHART_VERSION', 5):
            self.assertNotEqual(original, chart_cache_key('org-example', 'research'))
        with patch('vivo_app.lib.organization_chart_cache.datetime.datetime') as clock:
            clock.now.return_value.astimezone.return_value.year = 2099
            self.assertNotEqual(original, chart_cache_key('org-example', 'research'))
        with self.assertRaises(PageDataError):
            chart_cache_key('org-example', 'unsupported')

    def test_changed_team_membership_selects_a_fresh_chart(self) -> None:
        """
        Checks an edited team definition is read before looking up a cached chart.
        """
        manifest = Path(self.directory.name) / 'teams.json'
        builder = Mock(return_value=self.result)
        with override_settings(TEAM_SOURCE_MANIFEST=str(manifest)):
            for member in ('invented-a', 'invented-b'):
                manifest.write_text(
                    json.dumps({'teams': {'team-example': {'name': 'Example Team', 'member_ids': [member]}}})
                )
                cached_chart('team-example', 'research', builder)
            self.assertEqual(builder.call_count, 2)
            manifest.write_text('invalid')
            with self.assertRaises(PageDataError):
                cached_chart('team-example', 'research', builder)

    def test_storage_and_lock_failures_return_controlled_errors(self) -> None:
        """
        Checks unavailable cache storage and busy generation locks retain the service-error response.
        """
        for target, failure in (
            ('cache.get', OSError('Example cache failure.')),
            ('generation_lock', ReportError('Example busy lock.')),
        ):
            with patch('vivo_app.lib.organization_chart_cache.' + target, side_effect=failure):
                response = self.client.get('/display/org-example/viz/research.json')
            assert isinstance(response, HttpResponse)
            self.assertEqual(response.status_code, 503)

    def test_failure_cache_write_error_does_not_delay_recovery(self) -> None:
        """
        Checks unavailable failure storage returns a handled response and allows a fresh attempt on the next request.
        """
        with patch(
            'vivo_app.views.research_areas_data', side_effect=[PageDataError('Example outage.'), self.result]
        ) as builder:
            with patch('vivo_app.lib.organization_chart_cache.cache.set', side_effect=OSError('Example storage failure.')):
                response = self.client.get('/display/org-example/viz/research.json')
            assert isinstance(response, HttpResponse)
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('Retry-After', response)
            response = self.client.get('/display/org-example/viz/research.json')
            assert isinstance(response, HttpResponse)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(builder.call_count, 2)

    def slow_chart(self, identifier: str) -> tuple[str, dict[str, object]]:
        """
        Records one slow generation where all test workers can observe it.

        Called by: test_workers_share_one_successful_generation(), slow_failure()
        """
        with (Path(self.directory.name) / 'generations').open('a') as output:
            output.write(identifier + '\n')
        time.sleep(0.1)
        return self.result

    def slow_failure(self, identifier: str) -> tuple[str, dict[str, object]]:
        """
        Records a slow failed attempt where all test workers can observe it.

        Called by: test_workers_share_one_failure_delay()
        """
        self.slow_chart(identifier)
        raise PageDataError('Example slow failure.')

    def worker_results(self, builder: Mock) -> list[object]:
        """
        Collects the outcomes of three separate application workers sharing the file cache and locks.

        Called by: test_workers_share_one_successful_generation(), test_workers_share_one_failure_delay()
        """
        context = multiprocessing.get_context('fork')
        workers = [
            context.Process(target=chart_worker, args=(builder, self.directory.name + f'/done-{index}'))
            for index in range(3)
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
        self.assertEqual((Path(self.directory.name) / 'generations').read_text(), 'org-example\n')
        return [json.loads((Path(self.directory.name) / f'done-{index}').read_text()) for index in range(3)]

    def test_workers_share_one_successful_generation(self) -> None:
        """
        Checks simultaneous requests from separate workers generate one successful chart.
        """
        results = self.worker_results(Mock(side_effect=self.slow_chart))
        self.assertEqual(results, [list(self.result)] * 3)

    def test_workers_share_one_failure_delay(self) -> None:
        """
        Checks waiting workers reuse the failure delay and only the first worker reports the original failure.
        """
        results = self.worker_results(Mock(side_effect=self.slow_failure))
        reported = 0
        for result in results:
            assert isinstance(result, dict)
            self.assertGreaterEqual(result['retry_after'], 1)
            self.assertLessEqual(result['retry_after'], 10)
            reported += not result['cached']
        self.assertEqual(reported, 1)
