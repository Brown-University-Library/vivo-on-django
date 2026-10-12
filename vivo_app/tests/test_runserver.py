"""
Checks asset delivery and useful diagnostics for ordinary local previews.
"""

from io import StringIO

from django.conf import settings
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.management import get_commands
from django.http.response import HttpResponseBase
from django.test import RequestFactory, SimpleTestCase, override_settings

from vivo_app.management.commands.runserver import Command


@override_settings(STATIC_URL='/static/')
class RunserverTests(SimpleTestCase):
    """Checks Django's actual static handler without starting a network server."""

    @override_settings(DEBUG=True, REPORTS_ALLOW_LOCAL_DEVELOPMENT=True, REPORTS_LOCAL_RUNSERVER=False)
    def test_report_development_access_requires_loopback_binding(self) -> None:
        """
        Checks only an explicit loopback binding enables the requested local report exception.
        """
        command = Command()
        for address, expected in [('127.0.0.1', True), ('::1', True), ('0.0.0.0', False), ('192.0.2.1', False)]:
            command.addr = address
            command.get_handler(use_static_handler=True, insecure_serving=False)
            self.assertEqual(settings.REPORTS_LOCAL_RUNSERVER, expected)
        command.addr = '127.0.0.1'
        with override_settings(DEBUG=False):
            command.get_handler(use_static_handler=True, insecure_serving=True)
            self.assertFalse(settings.REPORTS_LOCAL_RUNSERVER)
        with override_settings(REPORTS_ALLOW_LOCAL_DEVELOPMENT=False):
            command.get_handler(use_static_handler=True, insecure_serving=False)
            self.assertFalse(settings.REPORTS_LOCAL_RUNSERVER)

    @override_settings(DEBUG=True)
    def test_local_preview_serves_styles(self) -> None:
        """
        Checks that ordinary local runserver serves the public page stylesheet.
        """
        self.assertEqual(get_commands()['runserver'], 'vivo_app')
        errors = StringIO()
        handler = Command(stderr=errors).get_handler(use_static_handler=True, insecure_serving=False)
        self.assertIsInstance(handler, StaticFilesHandler)
        response = handler.get_response(RequestFactory().get('/static/css/public.css'))
        assert isinstance(response, HttpResponseBase)
        try:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'text/css')
        finally:
            response.close()
        self.assertEqual(errors.getvalue(), '')

    @override_settings(DEBUG=False)
    def test_disabled_debug_explains_missing_styles(self) -> None:
        """
        Checks that a missing CSS response is accompanied by concrete restart instructions.
        """
        errors = StringIO()
        handler = Command(stderr=errors).get_handler(use_static_handler=True, insecure_serving=False)
        response = handler.get_response(RequestFactory().get('/static/css/public.css'))
        assert isinstance(response, HttpResponseBase)
        self.assertEqual(response.status_code, 404)
        self.assertIn('DJANGO_DEBUG=True', errors.getvalue())
        self.assertIn('stop and restart runserver', errors.getvalue())
        self.assertIn('runserver --insecure', errors.getvalue())
        self.assertFalse(settings.DEBUG)

    @override_settings(DEBUG=False)
    def test_explicit_local_static_option_serves_styles(self) -> None:
        """
        Checks that --insecure retains Django's local static serving with debug disabled.
        """
        errors = StringIO()
        handler = Command(stderr=errors).get_handler(use_static_handler=True, insecure_serving=True)
        self.assertIsInstance(handler, StaticFilesHandler)
        response = handler.get_response(RequestFactory().get('/static/css/public.css'))
        assert isinstance(response, HttpResponseBase)
        try:
            self.assertEqual(response.status_code, 200)
        finally:
            response.close()
        self.assertEqual(errors.getvalue(), '')

    @override_settings(DEBUG=True)
    def test_nostatic_explains_missing_styles(self) -> None:
        """
        Checks that --nostatic remains effective and identifies why styles will be absent.
        """
        errors = StringIO()
        handler = Command(stderr=errors).get_handler(use_static_handler=False, insecure_serving=True)
        self.assertNotIsInstance(handler, StaticFilesHandler)
        self.assertIn('--nostatic', errors.getvalue())
