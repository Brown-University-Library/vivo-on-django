import io
import os
import runpy
from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from dotenv import dotenv_values

BOOLEAN_SETTINGS = {
    'DJANGO_DEBUG': 'DEBUG',
    'DJANGO_BROWSER_RELOAD': 'ENABLE_BROWSER_RELOAD',
    'EMAIL_USE_TLS': 'EMAIL_USE_TLS',
    'TURNSTILE_ENABLED': 'TURNSTILE_ENABLED',
    'VIZ_ENABLED': 'VIZ_ENABLED',
}


def read_settings(content: str) -> dict[str, object]:
    """
    Reads made-up dotenv strings through the actual settings without loading private files.

    Called by: EnvironmentSettingsTests
    """
    environment = {
        'ALLOWED_HOSTS_JSON': '["localhost"]',
        'STATIC_URL': '/static/',
        'STATIC_ROOT': '../staticfiles',
    }
    for key, value in dotenv_values(stream=io.StringIO(content)).items():
        if isinstance(value, str):
            environment[key] = value
    settings_path = Path(__file__).resolve().parents[2] / 'config/settings.py'
    with patch.dict(os.environ, environment, clear=True), patch('dotenv.load_dotenv'):
        result = runpy.run_path(str(settings_path))
    return result


class EnvironmentSettingsTests(SimpleTestCase):
    def test_vivo_download_cache_has_a_separate_short_lifetime(self) -> None:
        """
        Checks VIVO downloads default to sixty seconds, support disabling caching, and reject invalid lifetimes.
        """
        self.assertEqual(read_settings('')['VIVO_EXPORT_CACHE_TIMEOUT_SECONDS'], 60)
        for value in ('0', '30', '1_200'):
            configured = read_settings(f'VIVO_EXPORT_CACHE_TIMEOUT_SECONDS="{value}"')
            self.assertEqual(configured['VIVO_EXPORT_CACHE_TIMEOUT_SECONDS'], int(value))
            self.assertEqual(configured['REPORT_CACHE_TIMEOUT_SECONDS'], 28800)
            self.assertEqual(configured['DISPLAY_JSONLD_CACHE_TIMEOUT_SECONDS'], 60)
        for value in ('-1', 'invalid'):
            with self.assertRaisesRegex(
                ImproperlyConfigured, 'VIVO_EXPORT_CACHE_TIMEOUT_SECONDS must be a nonnegative integer'
            ):
                read_settings(f'VIVO_EXPORT_CACHE_TIMEOUT_SECONDS="{value}"')

    def test_display_cache_has_a_separate_short_lifetime(self) -> None:
        """
        Checks display JSON-LD defaults to sixty seconds and rejects invalid cache settings.
        """
        self.assertEqual(read_settings('')['DISPLAY_JSONLD_CACHE_TIMEOUT_SECONDS'], 60)
        for value in ('0', '30', '1_200'):
            configured = read_settings(f'DISPLAY_JSONLD_CACHE_TIMEOUT_SECONDS="{value}"')
            self.assertEqual(configured['DISPLAY_JSONLD_CACHE_TIMEOUT_SECONDS'], int(value))
            self.assertEqual(configured['REPORT_CACHE_TIMEOUT_SECONDS'], 28800)
        self.assertEqual(read_settings('REPORT_CACHE_TIMEOUT_SECONDS="0"')['DISPLAY_JSONLD_CACHE_TIMEOUT_SECONDS'], 60)
        for value in ('-1', 'invalid'):
            with self.assertRaisesRegex(
                ImproperlyConfigured, 'DISPLAY_JSONLD_CACHE_TIMEOUT_SECONDS must be a nonnegative integer'
            ):
                read_settings(f'DISPLAY_JSONLD_CACHE_TIMEOUT_SECONDS="{value}"')

    def test_chart_cache_lifetime_is_short_configurable_and_validated(self) -> None:
        """
        Checks charts default to sixty seconds, can be disabled, and identify an invalid setting.
        """
        self.assertEqual(read_settings('')['CHART_CACHE_TIMEOUT_SECONDS'], 60)
        for value in ('0', '30', '1_200'):
            configured = read_settings(f'CHART_CACHE_TIMEOUT_SECONDS="{value}"')
            self.assertEqual(configured['CHART_CACHE_TIMEOUT_SECONDS'], int(value))
            self.assertEqual(configured['REPORT_CACHE_TIMEOUT_SECONDS'], 28800)
            self.assertEqual(configured['MEDIA_CACHE_TIMEOUT_SECONDS'], 60)
        for value in ('-1', 'invalid'):
            with self.assertRaisesRegex(ImproperlyConfigured, 'CHART_CACHE_TIMEOUT_SECONDS must be a nonnegative integer'):
                read_settings(f'CHART_CACHE_TIMEOUT_SECONDS="{value}"')

    def test_media_cache_lifetime_is_short_configurable_and_validated(self) -> None:
        """
        Checks media defaults to sixty seconds, can be disabled, and names its own invalid setting.
        """
        self.assertEqual(read_settings('')['MEDIA_CACHE_TIMEOUT_SECONDS'], 60)
        for value in ('0', '30', '1_200'):
            configured = read_settings(f'MEDIA_CACHE_TIMEOUT_SECONDS="{value}"')
            self.assertEqual(configured['MEDIA_CACHE_TIMEOUT_SECONDS'], int(value))
            self.assertEqual(configured['REPORT_CACHE_TIMEOUT_SECONDS'], 28800)
        for value in ('-1', 'invalid'):
            with self.assertRaisesRegex(ImproperlyConfigured, 'MEDIA_CACHE_TIMEOUT_SECONDS must be a nonnegative integer'):
                read_settings(f'MEDIA_CACHE_TIMEOUT_SECONDS="{value}"')

    def test_boolean_strings_use_the_same_case_rules(self) -> None:
        """
        Checks quoted boolean strings and earlier mixed-case values for every boolean setting.
        """
        for value in ('true', 'false', 'True', 'False', 'TRUE', 'FALSE', '', 'not-a-boolean'):
            with self.subTest(value=value):
                content = '\n'.join(f'{key}="{value}"' for key in BOOLEAN_SETTINGS)
                configured = read_settings(content)
                for setting_name in BOOLEAN_SETTINGS.values():
                    self.assertIs(configured[setting_name], value.lower() == 'true', setting_name)

    def test_defaults_preserve_existing_behavior(self) -> None:
        """
        Checks that omitted boolean settings keep their existing defaults.
        """
        configured = read_settings('')
        for setting_name in ('DEBUG', 'EMAIL_USE_TLS', 'VIZ_ENABLED'):
            self.assertIs(configured[setting_name], True, setting_name)
        for setting_name in ('ENABLE_BROWSER_RELOAD', 'TURNSTILE_ENABLED'):
            self.assertIs(configured[setting_name], False, setting_name)

    def test_quoted_ports_json_and_text_keep_their_intended_types(self) -> None:
        """
        Checks that ports and JSON are converted while ordinary text remains a string.
        """
        configured = read_settings(
            'EMAIL_PORT="2525"\n'
            'BOOK_COVER_DB_PORT="3307"\n'
            'ALLOWED_HOSTS_JSON=\'["localhost", "127.0.0.1"]\'\n'
            'NOTICE_BANNER="True"\n'
            'TEAM_SOURCE_MANIFEST="../team_source_manifest.local.json"\n'
        )
        self.assertEqual(configured['EMAIL_PORT'], 2525)
        self.assertIsInstance(configured['EMAIL_PORT'], int)
        self.assertEqual(configured['BOOK_COVER_DB_PORT'], 3307)
        self.assertIsInstance(configured['BOOK_COVER_DB_PORT'], int)
        self.assertEqual(configured['ALLOWED_HOSTS'], ['localhost', '127.0.0.1'])
        self.assertEqual(configured['NOTICE_BANNER'], 'True')
        self.assertEqual(configured['TEAM_SOURCE_MANIFEST'], '../team_source_manifest.local.json')

    def test_invalid_ports_and_json_are_rejected(self) -> None:
        """
        Checks that quoting does not make malformed ports or JSON acceptable.
        """
        for content in (
            'EMAIL_PORT="invalid"',
            'BOOK_COVER_DB_PORT="invalid"',
            'ALLOWED_HOSTS_JSON="invalid"',
            'ADMINS_JSON="invalid"',
        ):
            with self.subTest(content=content), self.assertRaises(ValueError):
                read_settings(content)

    def test_administrator_email_settings(self) -> None:
        """
        Checks that administrator recipients and the error sender come from the environment.
        """
        configured = read_settings(
            'ADMINS_JSON=\'[["Local administrator", "admin@example.com"]]\'\n'
            'SERVER_EMAIL="errors@example.com"\n'
            'DEFAULT_FROM_EMAIL="webmaster@example.com"\n'
        )
        self.assertEqual(configured['ADMINS'], [['Local administrator', 'admin@example.com']])
        self.assertEqual(configured['SERVER_EMAIL'], 'errors@example.com')

    def test_administrator_email_defaults(self) -> None:
        """
        Checks that omitted recipients disable email and the sender falls back to the default.
        """
        configured = read_settings('DEFAULT_FROM_EMAIL="webmaster@example.com"')
        self.assertEqual(configured['ADMINS'], [])
        self.assertEqual(configured['SERVER_EMAIL'], 'webmaster@example.com')
