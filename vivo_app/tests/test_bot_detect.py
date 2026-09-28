"""
Checks the enabled and disabled browser challenge without contacting Turnstile.
"""

import json
from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase, override_settings

from vivo_app.lib.bot_detect import VERIFY_URL, verify_token


class BotDetectTests(TestCase):
    """Checks search protection and server-side token handling."""

    @override_settings(TURNSTILE_ENABLED=False)
    def test_disabled_challenge_does_not_contact_verifier(self) -> None:
        """
        Checks ordinary searches work and direct challenge requests return 404.
        """
        with patch('vivo_app.lib.bot_detect.httpx2.Client') as client:
            search = self.client.get('/search?q=example')
            challenge = self.client.get('/challenge')
            post = self.client.post(
                '/challenge', data=json.dumps({'cf_turnstile_response': 'fake'}), content_type='application/json'
            )
        assert isinstance(search, HttpResponse) and isinstance(challenge, HttpResponse)
        assert isinstance(post, HttpResponse)
        self.assertNotEqual(search.status_code, 307)
        self.assertEqual(challenge.status_code, 404)
        self.assertEqual(post.status_code, 404)
        client.assert_not_called()

    @override_settings(
        PAGE_DATA_MODE='prototype',
        TURNSTILE_ENABLED=True,
        CF_TURNSTILE_SITEKEY='invented-site-key',
        CF_TURNSTILE_SECRET_KEY='invented-secret-key',
        ALLOWED_IP_RANGES='',
    )
    def test_successful_challenge_allows_same_visitor(self) -> None:
        """
        Checks an enabled search redirects until a verified token sets a session pass.
        """
        before = self.client.get('/search?q=example')
        assert isinstance(before, HttpResponse)
        self.assertEqual(before.status_code, 307)
        self.assertIn('/challenge?dest=', before['Location'])
        page = self.client.get(before['Location'])
        assert isinstance(page, HttpResponse)
        self.assertContains(page, 'data-sitekey="invented-site-key"')
        with patch('vivo_app.views.verify_token', return_value=True) as verify:
            result = self.client.post(
                '/challenge', data=json.dumps({'cf_turnstile_response': 'invented-token'}), content_type='application/json'
            )
        assert isinstance(result, HttpResponse)
        self.assertEqual(json.loads(result.content), {'success': True, 'redirect_for_challenge': True})
        verify.assert_called_once_with('invented-token', '127.0.0.1')
        after = self.client.get('/search?q=example')
        assert isinstance(after, HttpResponse)
        self.assertNotEqual(after.status_code, 307)
        other_address = self.client.get('/search?q=example', REMOTE_ADDR='192.0.2.8')
        assert isinstance(other_address, HttpResponse)
        self.assertEqual(other_address.status_code, 307)

    @override_settings(
        PAGE_DATA_MODE='prototype',
        TURNSTILE_ENABLED=True,
        CF_TURNSTILE_SITEKEY='invented-site-key',
        CF_TURNSTILE_SECRET_KEY='invented-secret-key',
        ALLOWED_IP_RANGES='',
    )
    def test_failed_challenge_does_not_allow_search(self) -> None:
        """
        Checks an invalid token cannot set the search pass.
        """
        with patch('vivo_app.views.verify_token', return_value=False):
            result = self.client.post(
                '/challenge', data=json.dumps({'cf_turnstile_response': 'bad'}), content_type='application/json'
            )
        assert isinstance(result, HttpResponse)
        self.assertEqual(json.loads(result.content), {'success': False, 'redirect_for_challenge': False})
        blocked = self.client.get('/search?q=example')
        assert isinstance(blocked, HttpResponse)
        self.assertEqual(blocked.status_code, 307)

    @override_settings(
        PAGE_DATA_MODE='prototype',
        TURNSTILE_ENABLED=True,
        CF_TURNSTILE_SITEKEY='invented-site-key',
        CF_TURNSTILE_SECRET_KEY='invented-secret-key',
        ALLOWED_IP_RANGES='192.0.2.0/24',
    )
    def test_allowed_address_skips_challenge(self) -> None:
        """
        Checks a configured visitor range bypasses the challenge.
        """
        response = self.client.get('/search?q=example', REMOTE_ADDR='192.0.2.8')
        assert isinstance(response, HttpResponse)
        self.assertNotEqual(response.status_code, 307)

    @override_settings(CF_TURNSTILE_SECRET_KEY='invented-secret-key')
    def test_verifier_sends_token_and_accepts_only_success(self) -> None:
        """
        Checks one server-side validation request carries the token and visitor address.
        """
        with patch('vivo_app.lib.bot_detect.httpx2.Client') as client:
            transport = client.return_value.__enter__.return_value
            transport.post.return_value.status_code = 200
            transport.post.return_value.json.return_value = {'success': True}
            self.assertTrue(verify_token('invented-token', '192.0.2.8'))
            transport.post.assert_called_once_with(
                VERIFY_URL,
                data={'secret': 'invented-secret-key', 'response': 'invented-token', 'remoteip': '192.0.2.8'},
            )
            transport.post.return_value.json.return_value = {'success': False}
            self.assertFalse(verify_token('invented-token', '192.0.2.8'))
            self.assertFalse(verify_token('x' * 2049, '192.0.2.8'))
