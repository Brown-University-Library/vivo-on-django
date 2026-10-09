"""
Checks display failures return the shared Rails error page using made-up records.
"""

from unittest.mock import patch
from urllib.parse import quote

from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings
from django.urls import get_script_prefix, set_script_prefix

from vivo_app.lib.prepared_data import MissingRecordError, PageDataError


@override_settings(
    TURNSTILE_ENABLED=False,
    CONTACT_US_URL_TEMPLATE='https://example.invalid/feedback?url={LINK}',
    STATIC_URL='/static/',
    UPSTREAM_RECORDING_MANIFEST='unused-example-manifest.json',
)
class DisplayErrorTests(SimpleTestCase):
    def test_source_and_unexpected_errors_show_recovery_page(self) -> None:
        """
        Checks live and replay display failures show HTML, feedback and search without exposing the error.
        """
        cases = (
            ('org-example', 'get_organization_data'),
            ('example-person', 'get_profile_data'),
            ('example-person?format=json', 'profile_json_data'),
            ('org-example.json', 'organization_json_data'),
            ('org-example?format=json_txt', 'raw_record_json_data'),
        )
        for mode in ('live', 'replay'):
            for identifier, loader in cases:
                for error_type in (PageDataError, ValueError):
                    with (
                        self.subTest(mode=mode, identifier=identifier, error_type=error_type),
                        override_settings(PAGE_DATA_MODE=mode, DEBUG=True),
                        patch('vivo_app.views.' + loader, side_effect=error_type('Example private error detail')),
                        patch('vivo_app.views.custom_organization_members', return_value=[]),
                        self.assertLogs('vivo_app.views', level='ERROR') as logs,
                    ):
                        response = self.client.get('/display/' + identifier)
                    assert isinstance(response, HttpResponse)
                    self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
                    self.assertTemplateUsed(response, 'search/error.html')
                    self.assertContains(response, 'Oops! Something went wrong', status_code=500)
                    self.assertContains(response, "We've logged the error and will review it.", status_code=500)
                    self.assertContains(response, '>Contact Us</a>', status_code=500)
                    self.assertContains(response, 'id="search-homepage" action="/search"', status_code=500)
                    self.assertContains(response, 'name="q"', status_code=500)
                    self.assertContains(response, 'autofocus', status_code=500)
                    self.assertContains(response, 'Researchers at Brown', status_code=500)
                    self.assertNotContains(response, 'Example private error detail', status_code=500)
                    self.assertNotContains(response, 'Page data unavailable', status_code=500)
                    self.assertIn('Example private error detail', logs.output[0])
                    self.assertIsNotNone(logs.records[0].exc_info)

    @override_settings(PAGE_DATA_MODE='live', DEBUG=False)
    def test_error_links_use_the_mounted_app_and_current_page(self) -> None:
        """
        Checks the search and feedback links still work when the app is mounted below the site root.
        """
        prefix = '/mounted-app'
        original_prefix = get_script_prefix()
        try:
            set_script_prefix(prefix)
            with patch('vivo_app.views.get_organization_data', side_effect=PageDataError('Example source failure')):
                response = self.client.get('/display/org-example', SCRIPT_NAME=prefix)
            assert isinstance(response, HttpResponse)
            self.assertContains(response, f'action="{prefix}/search"', status_code=500)
            page_url = quote('http://testserver' + prefix + '/display/org-example')
            self.assertContains(response, f'href="https://example.invalid/feedback?url={page_url}"', status_code=500)
        finally:
            set_script_prefix(original_prefix)

    @override_settings(PAGE_DATA_MODE='live')
    def test_missing_record_still_returns_not_found(self) -> None:
        """
        Checks an absent organization remains a 404 rather than a server error.
        """
        with patch('vivo_app.views.get_organization_data', side_effect=MissingRecordError('Example absent record')):
            response = self.client.get('/display/org-example')
        assert isinstance(response, HttpResponse)
        self.assertContains(response, 'Page not found', status_code=404)

    @override_settings(PAGE_DATA_MODE='prepared')
    def test_missing_saved_inputs_keep_the_existing_response(self) -> None:
        """
        Checks unavailable saved inputs keep their existing offline response.
        """
        with patch('vivo_app.views.get_organization_data', side_effect=PageDataError('Example absent saved input')):
            response = self.client.get('/display/org-example')
        assert isinstance(response, HttpResponse)
        self.assertContains(response, 'Page data unavailable', status_code=503)
