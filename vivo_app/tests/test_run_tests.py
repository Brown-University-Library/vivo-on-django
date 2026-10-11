import os
from unittest.mock import patch

from django.test import SimpleTestCase

from run_tests import configure_test_environment


class TestRunnerTests(SimpleTestCase):
    def test_configure_test_environment_selects_test_source_settings(self) -> None:
        """
        Checks that the test runner does not inherit the application's private source configuration.
        """
        with patch.dict(
            os.environ, {'SOLR_URL': 'https://private.invalid/', 'STATIC_URL': 'https://example.invalid/assets/'}
        ):
            configure_test_environment()

            self.assertEqual(os.environ['SOLR_URL'], 'https://source.invalid/solr')
            self.assertEqual(os.environ['STATIC_URL'], '/static/')
