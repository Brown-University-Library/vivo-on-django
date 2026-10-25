"""
Checks email filtering leaves unrelated server errors visible to administrators.
"""

import logging
from unittest.mock import patch

from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from vivo_app.lib.page_errors import PageDataError, SourceTimeoutError
from vivo_app.lib.reports import ReportError
from vivo_app.lib.request_logging import SkipSourceTimeoutEmails
from vivo_app.lib.search_errors import ReferenceSearchError


def raise_unexpected_failure(*args: object, **kwargs: object) -> None:
    """
    Raises a made-up programming error with an underlying cause and a real traceback.

    Called by: ErrorEmailTracebackTests.test_unexpected_errors_email_one_complete_traceback()
    """
    try:
        raise ValueError('Made-up underlying cause.')
    except ValueError as exc:
        raise RuntimeError('Made-up programming failure.') from exc


def raise_report_failure(*args: object, **kwargs: object) -> None:
    """
    Raises a report failure at a recognizable traceback location.

    Called by: ErrorEmailTracebackTests.test_handled_report_errors_log_tracebacks_without_email()
    """
    raise ReportError('Made-up report failure.')


def raise_search_failure(*args: object, **kwargs: object) -> None:
    """
    Raises the existing special search error at a recognizable traceback location.

    Called by: ErrorEmailTracebackTests.test_handled_search_errors_send_no_email()
    """
    raise ReferenceSearchError('Made-up search failure.')


class RequestLoggingTests(SimpleTestCase):
    def test_filter_requires_both_handled_timeout_and_503(self) -> None:
        """
        Checks unmarked requests, absent requests, and later 500 errors are never excluded from email.
        """
        email_filter = SkipSourceTimeoutEmails()
        request = RequestFactory().get('/display/invented-a')
        values: dict[str, object] = {'msg': 'Example request failure', 'status_code': 503}
        self.assertTrue(email_filter.filter(logging.makeLogRecord(values)))
        values['request'] = request
        self.assertTrue(email_filter.filter(logging.makeLogRecord(values)))
        request.META['vivo.source_timeout'] = True
        self.assertFalse(email_filter.filter(logging.makeLogRecord(values)))
        values['status_code'] = 500
        self.assertTrue(email_filter.filter(logging.makeLogRecord(values)))


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    ADMINS=[('Test administrator', 'admin@example.invalid')],
    SERVER_EMAIL='errors@example.invalid',
    TURNSTILE_ENABLED=False,
    CHART_CACHE_TIMEOUT_SECONDS=0,
)
class ErrorEmailTracebackTests(SimpleTestCase):
    def test_handled_source_problems_send_no_email(self) -> None:
        """
        Checks recognized source failures keep their responses and warning logs without email in either debug mode.
        """
        cases = (
            ('/display/org-example/viz/publications', 'publication_history_data', 503),
            ('/display/org-example/viz/research', 'research_areas_data', 503),
            ('/display/invented-a', 'cached_display_data', 500),
            ('/source-documents/docs/i/invented_cv.pdf', 'cached_media', 503),
            ('/individual/invented-a/invented-a.rdf', 'cached_representation', 503),
            ('/search', 'get_search_data', 503),
            ('/status', 'status_data', 500),
        )
        messages: list[EmailMultiAlternatives] = vars(mail)['outbox']
        for debug in (False, True):
            for path, loader, expected_status in cases:
                with (
                    self.subTest(debug=debug, path=path),
                    override_settings(DEBUG=debug),
                    patch('vivo_app.views.' + loader, side_effect=PageDataError('Made-up unavailable data.')),
                    patch.object(
                        logging.getLogger('django.request'), 'warning', wraps=logging.getLogger('django.request').warning
                    ) as warning,
                ):
                    response = self.client.get(path)
                    assert isinstance(response, HttpResponse)
                    self.assertEqual(response.status_code, expected_status)
                    self.assertEqual(messages, [])
                    warning.assert_called_once()
                    self.assertIsInstance(warning.call_args.kwargs['exc_info'], PageDataError)
                    self.assertNotIn(b'Traceback', response.content)

    def test_handled_source_configuration_error_sends_no_email(self) -> None:
        """
        Checks a recognized configuration failure before the view logs a warning without administrator email.
        """
        with patch('vivo_app.middleware.check_source_configuration', side_effect=PageDataError('Made-up configuration.')):
            response = self.client.get('/status')
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(vars(mail)['outbox'], [])

    def test_known_unavailable_routes_send_no_email(self) -> None:
        """
        Checks deliberate unavailable responses without exceptions do not generate status-only administrator emails.
        """
        for path in ('/display/invented-a/viz/', '/side_stuff/brown_classic/'):
            with self.subTest(path=path):
                response = self.client.get(path)
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.content, b'This endpoint is not connected to source data yet.')
                self.assertEqual(vars(mail)['outbox'], [])

    def test_unexpected_errors_email_one_complete_traceback(self) -> None:
        """
        Checks programming errors send one email containing the original traceback, cause, and request in either debug mode.
        """
        cases = (
            ('/display/org-example/viz/publications', 'publication_history_data', 500),
            ('/display/org-example/viz/research', 'research_areas_data', 500),
            ('/display/invented-a', 'cached_display_data', 500),
            ('/source-documents/docs/i/invented_cv.pdf', 'cached_media', 500),
            ('/individual/invented-a/invented-a.rdf', 'cached_representation', 500),
            ('/search', 'get_search_data', 500),
            ('/status', 'status_data', 500),
        )
        self.client.raise_request_exception = False
        messages: list[EmailMultiAlternatives] = vars(mail)['outbox']
        for debug in (False, True):
            for path, loader, expected_status in cases:
                messages.clear()
                with (
                    self.subTest(debug=debug, path=path),
                    override_settings(DEBUG=debug),
                    patch('vivo_app.views.' + loader, side_effect=raise_unexpected_failure),
                ):
                    response = self.client.get(path)
                    assert isinstance(response, HttpResponse)
                    self.assertEqual(response.status_code, expected_status)
                    self.assertEqual(len(messages), 1)
                    message = messages[0]
                    self.assertIn('raise_unexpected_failure', message.body)
                    self.assertIn('Made-up underlying cause.', message.body)
                    self.assertIn('RuntimeError', message.body)
                    self.assertIn(path, message.body)
                    self.assertEqual(len(message.alternatives), 1)
                    self.assertIn('raise_unexpected_failure', message.alternatives[0].content)
                    if not debug:
                        self.assertNotIn(b'Traceback', response.content)
                        self.assertNotIn(b'Made-up underlying cause.', response.content)

    def test_handled_report_errors_log_tracebacks_without_email(self) -> None:
        """
        Checks handled report errors retain their traceback in warning logs without sending administrator email.
        """
        messages: list[EmailMultiAlternatives] = vars(mail)['outbox']
        for path in ('/reports/subject-lib', '/reports/subject-lib/1'):
            messages.clear()
            with (
                self.subTest(path=path),
                patch('vivo_app.views.report_access', return_value=True),
                patch('vivo_app.views.load_reports', side_effect=raise_report_failure),
                self.assertLogs('django.request', level='WARNING') as logs,
            ):
                response = self.client.get(path)
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, 500)
                self.assertEqual(messages, [])
                self.assertIn('raise_report_failure', logs.output[0])
                self.assertEqual(logs.records[0].levelname, 'WARNING')
                self.assertNotIn(b'Traceback', response.content)

    def test_handled_search_errors_send_no_email(self) -> None:
        """
        Checks recognized HTML, JSON, and facet search failures retain their responses without administrator email.
        """
        messages: list[EmailMultiAlternatives] = vars(mail)['outbox']
        for path, loader in (
            ('/search', 'get_search_data'),
            ('/search?format=json', 'search_json_data'),
            ('/search_facets?f_name=record_type', 'facet_values_data'),
        ):
            messages.clear()
            with self.subTest(path=path), patch('vivo_app.views.' + loader, side_effect=raise_search_failure):
                response = self.client.get(path)
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, 500)
                self.assertEqual(messages, [])
                self.assertNotIn(b'Traceback', response.content)

    def test_handled_display_and_download_timeouts_still_send_no_email(self) -> None:
        """
        Checks traceback reporting preserves warning-only handling for display and download timeouts.
        """
        messages: list[EmailMultiAlternatives] = vars(mail)['outbox']
        for path, loader in (
            ('/display/invented-a', 'cached_display_data'),
            ('/individual/invented-a/invented-a.rdf', 'cached_representation'),
        ):
            with (
                self.subTest(path=path),
                patch('vivo_app.views.' + loader, side_effect=SourceTimeoutError('Made-up timeout.')),
            ):
                response = self.client.get(path)
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response['Retry-After'], '60')
                self.assertEqual(messages, [])
