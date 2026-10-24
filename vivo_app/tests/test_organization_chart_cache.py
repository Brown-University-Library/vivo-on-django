"""
Checks chart caching and prompt updates using made-up chart results and temporary storage.
"""

import json
import multiprocessing
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

from django.core.cache import cache
from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings

from vivo_app.lib.organization_chart_cache import cached_chart, chart_cache_key
from vivo_app.lib.page_errors import MissingRecordError, PageDataError
from vivo_app.lib.reports import ReportError


def chart_worker(builder: Mock, destination: str) -> None:
    """
    Saves a chart built or reused by a separate application worker.

    Called by: OrganizationChartCacheTests.test_workers_share_one_successful_generation()
    """
    result = cached_chart('org-example', 'research', builder)
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

    def test_missing_or_failed_chart_is_retried_on_the_next_request(self) -> None:
        """
        Checks missing records and source failures stay uncached and recover on the next request.
        """
        for failure, status in (
            (MissingRecordError('Example missing record.'), 404),
            (PageDataError('Example outage.'), 503),
        ):
            cache.clear()
            with patch('vivo_app.views.research_areas_data', side_effect=[failure, self.result]) as builder:
                response = self.client.get('/display/org-example/viz/research.json')
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, status)
                self.assertIn('no-store', response['Cache-Control'])
                self.assertIsNone(cache.get(chart_cache_key('org-example', 'research')))
                for _ in range(2):
                    response = self.client.get('/display/org-example/viz/research.json')
                    assert isinstance(response, HttpResponse)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(json.loads(response.content), self.research)
                self.assertEqual(builder.call_count, 2)

    def test_failed_refresh_does_not_return_an_expired_chart(self) -> None:
        """
        Checks failed refreshes do not serve expired content and a later request can succeed.
        """
        builder = Mock(side_effect=[self.result, PageDataError('Example outage.'), self.result])
        with patch('time.time', return_value=100):
            cached_chart('org-example', 'research', builder)
        with patch('time.time', return_value=161):
            with self.assertRaises(PageDataError):
                cached_chart('org-example', 'research', builder)
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
        with patch('vivo_app.lib.organization_chart_cache.CHART_VERSION', 3):
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

    def slow_chart(self, identifier: str) -> tuple[str, dict[str, object]]:
        """
        Records one slow generation where all test workers can observe it.

        Called by: test_workers_share_one_successful_generation()
        """
        with (Path(self.directory.name) / 'generations').open('a') as output:
            output.write(identifier + '\n')
        time.sleep(0.1)
        return self.result

    def test_workers_share_one_successful_generation(self) -> None:
        """
        Checks simultaneous requests from separate workers generate one successful chart.
        """
        context = multiprocessing.get_context('fork')
        builder = Mock(side_effect=self.slow_chart)
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
        for index in range(3):
            self.assertEqual(json.loads((Path(self.directory.name) / f'done-{index}').read_text()), list(self.result))
