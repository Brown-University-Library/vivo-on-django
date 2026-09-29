"""
Checks server diagnostics without contacting external services.
"""

import io
import json
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase, override_settings

from vivo_app.lib.recorded_responses import RecordedResponse
from vivo_app.management.commands.check_dev_sources import source_check


class CheckDevSourcesTests(SimpleTestCase):
    """Checks safe reports and explicit source selection."""

    @override_settings(PAGE_DATA_MODE='prepared')
    def test_default_checks_prepared_bundle_without_source_requests(self) -> None:
        """
        Checks the default command reads only the prepared bundle.
        """
        output = io.StringIO()
        with (
            patch('vivo_app.management.commands.check_dev_sources.prepared_check', return_value={'status': 'ok'}),
            patch('vivo_app.management.commands.check_dev_sources.source_check') as source,
        ):
            call_command('check_dev_sources', stdout=output)
        report = json.loads(output.getvalue())
        self.assertEqual(report['page_data_mode']['value'], 'prepared')
        self.assertEqual(report['prepared_bundle']['status'], 'ok')
        self.assertEqual(report['sources'], {})
        source.assert_not_called()

    @override_settings(PAGE_DATA_MODE='prepared')
    def test_missing_bundle_exits_after_safe_report(self) -> None:
        """
        Checks a missing bundle causes a nonzero result with no filesystem path.
        """
        output = io.StringIO()
        with (
            patch(
                'vivo_app.management.commands.check_dev_sources.prepared_check',
                return_value={'status': 'error', 'reason': 'The prepared manifest is missing or unreadable.'},
            ),
            self.assertRaises(SystemExit) as exit_status,
        ):
            call_command('check_dev_sources', stdout=output)
        self.assertEqual(exit_status.exception.code, 1)
        self.assertIn('missing or unreadable', output.getvalue())

    @override_settings(PAGE_DATA_MODE='prepared', PREPARED_FIXTURE_DIR='missing-directory')
    def test_selected_sources_skip_unrelated_page_data_checks(self) -> None:
        """
        Checks source probes succeed without a prepared directory or mode check.
        """
        output = io.StringIO()
        with (
            patch('vivo_app.management.commands.check_dev_sources.source_check', return_value={'status': 'ok'}) as source,
            patch('vivo_app.management.commands.check_dev_sources.prepared_check') as prepared,
            patch('vivo_app.management.commands.check_dev_sources.selected_mode') as mode,
        ):
            call_command('check_dev_sources', '--source', 'solr', '--source', 'solr', '--source', 'viz', stdout=output)
        report = json.loads(output.getvalue())
        self.assertEqual(list(report), ['sources'])
        self.assertEqual(list(report['sources']), ['solr', 'viz'])
        self.assertEqual(source.call_count, 2)
        prepared.assert_not_called()
        mode.assert_not_called()

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
        response = RecordedResponse(200, (), b'invented record content')
        with patch('vivo_app.management.commands.check_dev_sources.read_source', return_value=response):
            result = source_check('vivo', 'invented-a')
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['http_status'], 200)
        digest = result.get('sha256')
        assert isinstance(digest, str)
        self.assertEqual(len(digest), 64)
        self.assertNotIn('invented record content', json.dumps(result))
