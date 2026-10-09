"""
Checks the enabled and disabled browser challenge without contacting Turnstile.
"""

import json
from unittest.mock import patch

from django.http import HttpResponse
from django.test import Client, TestCase, override_settings
from django.urls import get_script_prefix, set_script_prefix

from vivo_app.lib.bot_detect import VERIFY_URL, verify_token


class BotDetectTests(TestCase):
    """Checks search protection and server-side token handling."""

    @override_settings(TURNSTILE_ENABLED=False, CF_TURNSTILE_SITEKEY='', CF_TURNSTILE_SECRET_KEY='')
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
        TURNSTILE_ENABLED=False,
        CF_TURNSTILE_SITEKEY='invented-site-key',
        CF_TURNSTILE_SECRET_KEY='invented-secret-key',
    )
    def test_configured_challenge_does_not_enable_search_protection(self) -> None:
        """
        Checks a configured direct challenge works without changing ordinary search access.
        """
        page = self.client.get('/challenge')
        assert isinstance(page, HttpResponse)
        self.assertContains(page, 'data-sitekey="invented-site-key"')
        self.assertContains(page, '<title>Researchers @ Brown</title>')
        self.assertContains(page, '<h1 class="brand-alt-h1 mb-4">Traffic control and bot detection...</h1>')
        self.assertContains(page, 'If you still have trouble, please <a href=')
        self.assertContains(page, '>get in touch</a>')
        self.assertNotContains(page, 'invented-secret-key')
        search = self.client.get('/search?q=example')
        assert isinstance(search, HttpResponse)
        self.assertNotEqual(search.status_code, 307)
        with patch('vivo_app.views.verify_token', return_value=True) as verify:
            result = self.client.post(
                '/challenge', data=json.dumps({'cf_turnstile_response': 'invented-token'}), content_type='application/json'
            )
        assert isinstance(result, HttpResponse)
        self.assertEqual(json.loads(result.content), {'success': True, 'redirect_for_challenge': True})
        verify.assert_called_once_with('invented-token', '127.0.0.1')

    @override_settings(
        PAGE_DATA_MODE='live',
        SOLR_URL='http://127.0.0.1:8983/solr/example',
        TURNSTILE_ENABLED=False,
        CF_TURNSTILE_SITEKEY='invented-site-key',
        CF_TURNSTILE_SECRET_KEY='invented-secret-key',
    )
    def test_live_challenge_get_does_not_contact_data_services(self) -> None:
        """
        Checks the live challenge renders without contacting Turnstile or the search index.
        """
        with patch('vivo_app.lib.bot_detect.httpx2.Client') as client:
            page = self.client.get('/challenge/')
        assert isinstance(page, HttpResponse)
        self.assertContains(page, 'data-sitekey="invented-site-key"')
        self.assertContains(page, 'content="noindex"')
        client.assert_not_called()

    @override_settings(
        TURNSTILE_ENABLED=False,
        CF_TURNSTILE_SITEKEY='invented-site-key',
        CF_TURNSTILE_SECRET_KEY='invented-secret-key',
        UPSTREAM_RECORDING_MANIFEST='unused-offline-manifest.json',
    )
    def test_offline_modes_do_not_serve_configured_challenge(self) -> None:
        """
        Checks offline modes never load the widget or verify tokens even with configured keys.
        """
        with patch('vivo_app.views.verify_token') as verify:
            for mode in ('prepared', 'replay'):
                with self.subTest(mode=mode), override_settings(PAGE_DATA_MODE=mode):
                    for method in ('get', 'post'):
                        response = getattr(self.client, method)('/challenge')
                        assert isinstance(response, HttpResponse)
                        self.assertEqual(response.status_code, 404)
                        self.assertNotContains(response, 'challenges.cloudflare.com', status_code=404)
        verify.assert_not_called()

    @override_settings(
        PAGE_DATA_MODE='prototype',
        TURNSTILE_ENABLED=True,
        CF_TURNSTILE_SITEKEY='invented-site-key',
        CF_TURNSTILE_SECRET_KEY='',
    )
    def test_missing_key_does_not_load_widget_or_verify(self) -> None:
        """
        Checks incomplete configuration reports unavailable without contacting the verifier.
        """
        with patch('vivo_app.views.verify_token') as verify:
            for method in ('get', 'post'):
                response = getattr(self.client, method)('/challenge')
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, 503)
                self.assertNotContains(response, 'challenges.cloudflare.com', status_code=503)
        verify.assert_not_called()

    @override_settings(
        PAGE_DATA_MODE='prototype',
        TURNSTILE_ENABLED=False,
        CF_TURNSTILE_SITEKEY='invented-site-key',
        CF_TURNSTILE_SECRET_KEY='invented-secret-key',
    )
    def test_mounted_challenge_uses_local_post_url_and_requires_csrf(self) -> None:
        """
        Checks the mounted page submits locally and rejects a POST without its CSRF token.
        """
        client = Client(enforce_csrf_checks=True)
        previous_prefix = get_script_prefix()
        try:
            set_script_prefix('/preview/')
            page = client.get('/challenge', SCRIPT_NAME='/preview')
        finally:
            set_script_prefix(previous_prefix)
        assert isinstance(page, HttpResponse)
        self.assertContains(page, "fetch('/preview/challenge'")
        with patch('vivo_app.views.verify_token', return_value=True) as verify:
            response = client.post(
                '/challenge', data=json.dumps({'cf_turnstile_response': 'invented-token'}), content_type='application/json'
            )
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 403)
        verify.assert_not_called()
        with patch('vivo_app.views.verify_token', return_value=True) as verify:
            accepted = client.post(
                '/challenge',
                data=json.dumps({'cf_turnstile_response': 'invented-token'}),
                content_type='application/json',
                HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value,
            )
        assert isinstance(accepted, HttpResponse)
        self.assertEqual(json.loads(accepted.content), {'success': True, 'redirect_for_challenge': True})
        verify.assert_called_once_with('invented-token', '127.0.0.1')

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
