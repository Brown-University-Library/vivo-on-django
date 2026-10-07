import io
import os
import runpy
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase
from dotenv import dotenv_values

BOOLEAN_SETTINGS = {
    'DJANGO_DEBUG': 'DEBUG',
    'DJANGO_BROWSER_RELOAD': 'ENABLE_BROWSER_RELOAD',
    'EMAIL_USE_TLS': 'EMAIL_USE_TLS',
    'BOOK_COVER_STUB': 'BOOK_COVER_STUB',
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
        for setting_name in ('DEBUG', 'EMAIL_USE_TLS', 'BOOK_COVER_STUB', 'VIZ_ENABLED'):
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
        for content in ('EMAIL_PORT="invalid"', 'BOOK_COVER_DB_PORT="invalid"', 'ALLOWED_HOSTS_JSON="invalid"'):
            with self.subTest(content=content), self.assertRaises(ValueError):
                read_settings(content)
