import os
from unittest.mock import patch

from django.test import SimpleTestCase

from run_tests import configure_test_environment


class TestRunnerTests(SimpleTestCase):
    def test_configure_test_environment_selects_prototype_mode(self) -> None:
        """
        Checks that the test runner does not inherit the application's private data mode.
        """
        with patch.dict(os.environ, {'PAGE_DATA_MODE': 'prepared'}):
            configure_test_environment()

            self.assertEqual(os.environ['PAGE_DATA_MODE'], 'prototype')
