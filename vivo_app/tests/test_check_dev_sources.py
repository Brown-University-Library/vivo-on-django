"""
Checks server diagnostics without contacting external services.
"""

import io
import json
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase, override_settings

from vivo_app.lib.page_errors import PageDataError
from vivo_app.lib.source_requests import profile_key, read_source
from vivo_app.lib.source_types import SourceResponse
from vivo_app.management.commands.check_dev_sources import source_check


class CheckDevSourcesTests(SimpleTestCase):
    """Checks safe reports and explicit source selection."""

    def test_failed_source_check_exits_after_reporting_its_reason(self) -> None:
        """
        Checks source failures remain visible and cause a nonzero exit.
        """
        output = io.StringIO()
        with (
            patch(
                'vivo_app.management.commands.check_dev_sources.source_check',
                return_value={'status': 'error', 'reason': 'solr source request failed.'},
            ),
            self.assertRaises(SystemExit) as exit_status,
        ):
            call_command('check_dev_sources', '--source', 'solr', stdout=output)
        self.assertEqual(exit_status.exception.code, 1)
        report = json.loads(output.getvalue())
        self.assertEqual(report['sources']['solr']['reason'], 'solr source request failed.')

    def test_vivo_needs_an_existing_record_id(self) -> None:
        """
        Checks the VIVO probe does not guess a record ID or issue a request.
        """
        with patch('vivo_app.management.commands.check_dev_sources.read_source') as read:
            result = source_check('vivo', '')
        self.assertEqual(result['status'], 'error')
        read.assert_not_called()

    def test_vivo_reports_status_and_digest_without_record_content(self) -> None:
        """
        Checks a successful export can be compared without printing its body.
        """
        response = SourceResponse(200, (), b'invented record content')
        with patch('vivo_app.management.commands.check_dev_sources.read_source', return_value=response):
            result = source_check('vivo', 'invented-a')
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['http_status'], 200)
        digest = result.get('sha256')
        assert isinstance(digest, str)
        self.assertEqual(len(digest), 64)
        self.assertNotIn('invented record content', json.dumps(result))

    def test_search_check_processes_results_without_printing_them(self) -> None:
        """
        Checks the selected query reaches search processing and only a count is reported.
        """
        output = io.StringIO()
        with patch(
            'vivo_app.management.commands.check_dev_sources.search_data',
            return_value={'results': [{'name': 'Invented Private Name'}]},
        ) as search:
            call_command('check_dev_sources', '--source', 'search', '--search-query', 'invented', stdout=output)
        report = json.loads(output.getvalue())
        self.assertEqual(report['sources']['search']['results_on_page'], 1)
        self.assertNotIn('Invented Private Name', output.getvalue())
        self.assertNotIn('invented', output.getvalue())
        search.assert_called_once_with([('q', 'invented')])

    def test_search_check_reports_parser_failure(self) -> None:
        """
        Checks a search processing error produces a safe nonzero report.
        """
        with patch(
            'vivo_app.management.commands.check_dev_sources.search_data',
            side_effect=PageDataError('Solr did not return search facets.'),
        ):
            result = source_check('search', '')
        self.assertEqual(result, {'status': 'error', 'reason': 'Solr did not return search facets.'})

    def test_profile_check_reports_collaborator_count_without_record_content(self) -> None:
        """
        Checks the profile probe reports source availability without names or record JSON.
        """
        uri = 'http://vivo.brown.edu/individual/invented-a'
        document = {
            'id': uri,
            'record_type': ['PEOPLE'],
            'show_visualizations_s': 'true',
            'json_txt': [json.dumps({'collaborators': [{'name': 'Invented Private Name'}]})],
        }
        response = {'responseHeader': {'status': 0}, 'response': {'numFound': 1, 'docs': [document]}}
        with (
            patch('vivo_app.management.commands.check_dev_sources.response_object', return_value=response) as source,
            patch('vivo_app.management.commands.check_dev_sources.visualization_list', return_value={uri: True}) as graphs,
        ):
            result = source_check('profile', 'invented-a')
        self.assertEqual(result['collaborators'], 1)
        self.assertTrue(result['profile_visualizations_enabled'])
        self.assertTrue(result['collaborator_graph_available'])
        self.assertNotIn('Invented Private Name', json.dumps(result))
        source.assert_called_once_with(profile_key('invented-a'), read_source)
        graphs.assert_called_once_with('collaborators')

    def test_profile_check_requires_an_id(self) -> None:
        """
        Checks the profile probe does not query Solr without an explicit identifier.
        """
        with patch('vivo_app.management.commands.check_dev_sources.response_object') as source:
            result = source_check('profile', '')
        self.assertEqual(result['status'], 'error')
        source.assert_not_called()

    def test_full_search_facet_check_reports_counts_without_values(self) -> None:
        """
        Checks the full facet read reports only counts and detects a shorter response.
        """
        search_result = {
            'facets': [{'name': 'affiliations', 'values': [{'text': 'Invented Private Name'} for _ in range(10)]}]
        }
        with (
            patch('vivo_app.management.commands.check_dev_sources.search_data', return_value=search_result),
            patch('vivo_app.management.commands.check_dev_sources.facet_values_data') as full,
        ):
            full.return_value = [{'text': 'Invented Private Name'} for _ in range(12)]
            output = io.StringIO()
            call_command('check_dev_sources', '--source', 'search-facets', '--search-query', 'invented', stdout=output)
            report = json.loads(output.getvalue())['sources']['search-facets']
            self.assertEqual((report['status'], report['shown_values'], report['full_values']), ('ok', 10, 12))
            self.assertNotIn('Invented Private Name', output.getvalue())
            full.assert_called_with([('q', 'invented'), ('f_name', 'affiliations')])
            full.return_value = []
            output = io.StringIO()
            with self.assertRaises(SystemExit):
                call_command('check_dev_sources', '--source', 'search-facets', stdout=output)
            report = json.loads(output.getvalue())['sources']['search-facets']
            self.assertEqual((report['status'], report['shown_values'], report['full_values']), ('error', 10, 0))

    def test_default_checks_configuration_without_source_requests(self) -> None:
        """
        Checks the default command reads settings without contacting services.
        """
        output = io.StringIO()
        with patch('vivo_app.management.commands.check_dev_sources.source_check') as source:
            call_command('check_dev_sources', stdout=output)
        self.assertEqual(json.loads(output.getvalue()), {'configuration': {'status': 'ok'}, 'sources': {}})
        source.assert_not_called()

    @override_settings(SOLR_URL='')
    def test_missing_configuration_reports_failure(self) -> None:
        """
        Checks a missing required setting produces a nonzero result without private values.
        """
        output = io.StringIO()
        with self.assertRaises(SystemExit) as caught:
            call_command('check_dev_sources', stdout=output)
        self.assertEqual(caught.exception.code, 1)
        self.assertEqual(json.loads(output.getvalue())['configuration']['status'], 'error')

    @override_settings(SOLR_URL='')
    def test_selected_sources_skip_unrelated_configuration_checks(self) -> None:
        """
        Checks explicit probes contact only named sources, once each.
        """
        output = io.StringIO()
        with patch('vivo_app.management.commands.check_dev_sources.source_check', return_value={'status': 'ok'}) as source:
            call_command('check_dev_sources', '--source', 'solr', '--source', 'solr', '--source', 'viz', stdout=output)
        self.assertEqual(list(json.loads(output.getvalue())['sources']), ['solr', 'viz'])
        self.assertEqual(source.call_count, 2)
