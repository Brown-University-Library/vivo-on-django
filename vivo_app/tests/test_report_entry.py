"""Checks the approved public report entry without reading report data."""

from unittest.mock import patch

from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings
from django.urls import get_script_prefix, set_script_prefix


@override_settings(
    SOLR_URL='https://source.invalid/solr',
    UPSTREAM_RECORDING_MANIFEST='unused-recordings.json',
    TURNSTILE_ENABLED=False,
)
class ReportEntryTests(SimpleTestCase):
    def test_public_entry_redirects_directly_home_in_source_modes(self) -> None:
        """
        Checks both entry forms redirect directly home without rendering a report.
        """
        for mode in ('live', 'replay', 'prepared'):
            with (
                self.subTest(mode=mode),
                override_settings(PAGE_DATA_MODE=mode),
                patch('vivo_app.views.render_or_stub') as render_report,
            ):
                for path in ('/reports/subject-lib', '/reports/subject-lib/'):
                    response = self.client.get(path)
                    assert isinstance(response, HttpResponse)
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(response['Location'], '/')
                render_report.assert_not_called()

    @override_settings(PAGE_DATA_MODE='live')
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

    @override_settings(PAGE_DATA_MODE='prototype')
    def test_sample_entry_keeps_existing_rendering(self) -> None:
        """
        Checks the local sample entry still delegates to its existing template.
        """
        with patch('vivo_app.views.render_or_stub', return_value=HttpResponse(b'Sample report')) as render_report:
            response = self.client.get('/reports/subject-lib/')
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'Sample report')
        self.assertEqual(render_report.call_args.args[1], 'reports/subject_lib_list.html')
