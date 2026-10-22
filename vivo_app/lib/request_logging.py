"""
Keeps handled display timeouts in the logs without sending administrator email.
"""

import logging

from django.http import HttpRequest


class SkipDisplayTimeoutEmails(logging.Filter):
    """Excludes only a handled display timeout's 503 response from administrator email."""

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Allows other request errors through even when a timeout preceded a later failure.

        Called by: django.utils.log.AdminEmailHandler.handle()
        """
        request = getattr(record, 'request', None)
        handled_timeout = (
            isinstance(request, HttpRequest)
            and request.META.get('vivo.display_timeout') is True
            and getattr(record, 'status_code', None) == 503
        )
        return not handled_timeout
