"""
Checks whether search needs a challenge and verifies submitted Turnstile tokens.
"""

import ipaddress
from datetime import datetime, timedelta

import httpx2
from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.http import HttpRequest
from django.utils import timezone

SESSION_KEY = 'bot_detection-passed'
VERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'


def allowed_address(address: str) -> bool:
    """
    Checks the configured challenge exemption ranges.

    Called by: challenge_passed()
    """
    result = False
    try:
        visitor = ipaddress.ip_address(address)
        for value in settings.ALLOWED_IP_RANGES.split(','):
            if value.strip() and visitor in ipaddress.ip_network(value.strip(), strict=False):
                result = True
                break
    except ValueError:
        result = False
    return result


def challenge_passed(request: HttpRequest) -> bool:
    """
    Accepts an allowed address or a recent pass tied to the visitor's address.

    Called by: middleware.TurnstileSearchMiddleware.process_view()
    """
    address = request.META.get('REMOTE_ADDR', '')
    result = allowed_address(address)
    if not result:
        session = getattr(request, 'session', None)
        saved = session.get(SESSION_KEY) if isinstance(session, SessionBase) else None
        if isinstance(saved, dict) and saved.get('ip') == address:
            raw_time = saved.get('time')
            if isinstance(raw_time, str):
                try:
                    passed_at = datetime.fromisoformat(raw_time)
                    result = passed_at.tzinfo is not None and timedelta(0) <= timezone.now() - passed_at < timedelta(
                        hours=24
                    )
                except ValueError:
                    result = False
    return result


def verify_token(token: str, address: str) -> bool:
    """
    Sends one bounded validation request and accepts only an explicit success.

    Called by: views.bot_detect_challenge()
    """
    if not token or len(token) > 2048 or not settings.CF_TURNSTILE_SECRET_KEY:
        return False
    try:
        with httpx2.Client(timeout=3.0, trust_env=False) as client:
            response = client.post(
                VERIFY_URL,
                data={'secret': settings.CF_TURNSTILE_SECRET_KEY, 'response': token, 'remoteip': address},
            )
        value = response.json() if response.status_code == 200 else None
        result = isinstance(value, dict) and value.get('success') is True
    except (httpx2.HTTPError, ValueError):
        result = False
    return result
