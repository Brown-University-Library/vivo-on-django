"""
Checks configuration failures and shared external-input validation without source access.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings

from vivo_app.checks import check_page_data
from vivo_app.lib.source_types import SourceDataError, external_path, json_object


class SourceConfigurationTests(SimpleTestCase):
    @override_settings(SOLR_URL='https://source.invalid/solr')
    def test_configuration_check_does_not_contact_sources(self) -> None:
        """
        Checks configured sources pass the local check without opening a connection.
        """
        self.assertEqual(check_page_data(), [])

    @override_settings(SOLR_URL='')
    def test_missing_configuration_rejects_requests(self) -> None:
        """
        Checks an absent required setting fails startup checks and requests consistently.
        """
        messages = check_page_data()
        self.assertEqual([message.id for message in messages], ['vivo_app.E001'])
        response = self.client.get('/search?q=Example')
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 503)
        self.assertContains(response, 'Search and profiles require SOLR_URL.', status_code=503)

    def test_external_inputs_stay_outside_git_checkouts(self) -> None:
        """
        Checks external input validation handles both Git directories and worktree marker files.
        """
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(external_path(root / 'input.json'), root.resolve() / 'input.json')
            marker = root / '.git'
            marker.mkdir()
            with self.assertRaises(SourceDataError):
                external_path(root / 'nested/input.json')
            marker.rmdir()
            marker.write_text('gitdir: elsewhere')
            with self.assertRaises(SourceDataError):
                external_path(root / 'input.json')

    def test_json_objects_require_string_keys(self) -> None:
        """
        Checks developer-tool input parsing rejects arrays and non-string mapping keys.
        """
        self.assertEqual(json_object({'cases': []}), {'cases': []})
        for value in (None, [], {1: 'value'}):
            with self.subTest(value=value), self.assertRaises(SourceDataError):
                json_object(value)
