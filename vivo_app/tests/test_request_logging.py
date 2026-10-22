"""
Checks email filtering leaves unrelated server errors visible to administrators.
"""

import logging

from django.test import RequestFactory, SimpleTestCase

from vivo_app.lib.request_logging import SkipDisplayTimeoutEmails


class RequestLoggingTests(SimpleTestCase):
    def test_filter_requires_both_handled_timeout_and_503(self) -> None:
        """
        Checks unmarked requests, absent requests, and later 500 errors are never excluded from email.
        """
        email_filter = SkipDisplayTimeoutEmails()
        request = RequestFactory().get('/display/invented-a')
        values: dict[str, object] = {'msg': 'Example request failure', 'status_code': 503}
        self.assertTrue(email_filter.filter(logging.makeLogRecord(values)))
        values['request'] = request
        self.assertTrue(email_filter.filter(logging.makeLogRecord(values)))
        request.META['vivo.display_timeout'] = True
        self.assertFalse(email_filter.filter(logging.makeLogRecord(values)))
        values['status_code'] = 500
        self.assertTrue(email_filter.filter(logging.makeLogRecord(values)))
