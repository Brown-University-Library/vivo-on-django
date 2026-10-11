"""Checks the approved public report entry without reading report data."""

from unittest.mock import patch

from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings
from django.urls import get_script_prefix, set_script_prefix


@override_settings(SOLR_URL='https://source.invalid/solr', TURNSTILE_ENABLED=False)
class ReportEntryTests(SimpleTestCase):
    def test_public_entry_redirects_directly_home_without_source_reads(self) -> None:
        """
        Checks both entry forms redirect directly home without rendering a report.
        """
        with (
            self.subTest(),
            override_settings(),
            patch('vivo_app.views.render_or_stub') as render_report,
        ):
            for path in ('/reports/subject-lib', '/reports/subject-lib/'):
                response = self.client.get(path)
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response['Location'], '/')
            render_report.assert_not_called()

    def test_mounted_entry_drops_query_parameters(self) -> None:
        """
        Checks query values cannot change the mounted home destination or render data.
        """
        previous_prefix = get_script_prefix()
        set_script_prefix('/mounted-app/')
        try:
            with patch('vivo_app.views.render_or_stub') as render_report:
                for path in ('/reports/subject-lib', '/reports/subject-lib/'):
                    response = self.client.get(path, {'format': 'json', 'page': '2'}, SCRIPT_NAME='/mounted-app')
                    assert isinstance(response, HttpResponse)
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(response['Location'], '/mounted-app/')
                render_report.assert_not_called()
        finally:
            set_script_prefix(previous_prefix)
