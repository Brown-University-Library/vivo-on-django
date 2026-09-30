import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast
from unittest.mock import MagicMock, patch

from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from vivo_app.lib.error_check import IntentionalErrorCheckError
from vivo_app.lib.version_helper import GatherCommitAndBranchData


class ErrorCheckTests(SimpleTestCase):
    @override_settings(DEBUG=True)
    def test_debug_error_check_raises(self) -> None:
        """
        Checks that the development endpoint raises its intentional exception.
        """
        with self.assertRaisesRegex(IntentionalErrorCheckError, 'Raising intentional exception'):
            self.client.get(reverse('error_check'))

    @override_settings(DEBUG=False)
    def test_production_error_check_returns_not_found(self) -> None:
        """
        Checks that the production endpoint does not expose an error trigger.
        """
        response = cast(HttpResponse, self.client.get(reverse('error_check')))

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, '404 / Not Found', status_code=404)


class VersionEndpointTests(SimpleTestCase):
    @patch('vivo_app.views.version_helper.LOADED_VERSION', 'main loaded123')
    @patch('vivo_app.views.GatherCommitAndBranchData')
    def test_version_returns_standard_response(self, gatherer_class: MagicMock) -> None:
        """
        Checks the version endpoint's standard JSON response.
        """
        gatherer = gatherer_class.return_value
        gatherer.branch = 'main'
        gatherer.commit = 'abc123'

        response = cast(HttpResponse, self.client.get(reverse('version')))
        payload: dict[str, dict[str, str]] = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/json; charset=utf-8')
        self.assertEqual(payload['request']['url'], 'http://127.0.0.1/version/')
        self.assertIn('timestamp', payload['request'])
        self.assertEqual(payload['response']['ip'], '127.0.0.1')
        self.assertEqual(payload['response']['version'], 'main abc123')
        self.assertEqual(payload['response']['loaded_version'], 'main loaded123')
        self.assertNotIn('mount_check', payload['response'])
        self.assertIn('timetaken', payload['response'])
        gatherer.gather.assert_called_once_with()

    def test_version_handles_missing_git_metadata(self) -> None:
        """
        Checks that the version endpoint returns clear fallback values without Git metadata.
        """
        with TemporaryDirectory() as temp_directory, override_settings(BASE_DIR=Path(temp_directory)):
            response = cast(HttpResponse, self.client.get(reverse('version')))

        payload: dict[str, dict[str, str]] = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload['response']['version'], 'branch_not_found commit_not_found')


class VersionHelperTests(SimpleTestCase):
    def test_gather_reads_git(self) -> None:
        """
        Checks branch and commit collection.
        """
        with TemporaryDirectory() as temp_directory:
            base_directory = Path(temp_directory)
            ref_directory = base_directory / '.git' / 'refs' / 'heads'
            ref_directory.mkdir(parents=True)
            (base_directory / '.git' / 'HEAD').write_text('ref: refs/heads/main\n', encoding='utf-8')
            (ref_directory / 'main').write_text('abc123\n', encoding='utf-8')
            with override_settings(BASE_DIR=base_directory):
                gatherer = GatherCommitAndBranchData()
                gatherer.gather()

        self.assertEqual(gatherer.branch, 'main')
        self.assertEqual(gatherer.commit, 'abc123')
