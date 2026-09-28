"""
Checks offline replay using invented data written outside the repository.
"""

import hashlib
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from tools.validate_recordings import main as validate_recordings
from vivo_app.lib.recorded_responses import RecordingError, RequestKey, load_recordings


class RecordedResponseTests(unittest.TestCase):
    def setUp(self) -> None:
        """Checks replay with two invented upstream response bodies."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.manifest_path = self.root / 'manifest.json'
        self.query = (('q', 'sample topic'), ('fq', 'type:PEOPLE'), ('fq', 'area:Sample'), ('empty', ''))
        self.search_request = RequestKey('solr', '/select', self.query)
        search = b'{"response":{"numFound":1,"docs":[{"id":"sample-a"}]},"facet_counts":{}}'
        profile = b'{"response":{"numFound":1,"docs":[{"id":"sample-a","json_txt":["{}"]}]}}'
        self.entries: list[dict[str, object]] = []
        for name, body, query in (
            ('search', search, self.query),
            ('profile', profile, (('q', 'id:sample-a'),)),
        ):
            filename = f'{name}.json'
            (self.root / filename).write_bytes(body)
            self.entries.append(
                {
                    'id': name,
                    'request': {'service': 'solr', 'method': 'GET', 'path': '/select', 'query': query, 'headers': []},
                    'response': {
                        'status': 200,
                        'headers': [['Content-Type', 'application/json']],
                        'body_file': filename,
                        'sha256': hashlib.sha256(body).hexdigest(),
                    },
                }
            )
        self.manifest: dict[str, object] = {
            'schema_version': 1,
            'data_kind': 'synthetic',
            'captured_at': '2026-01-01T00:00:00Z',
            'recordings': self.entries,
            'cases': {'SEARCH_DEMO': ['search'], 'PROFILE_DEMO': ['profile']},
        }
        self.save_manifest()

    def save_manifest(self) -> None:
        """
        Writes the current invented manifest into the temporary directory.

        Called by: setUp(), tests
        """
        self.manifest_path.write_text(json.dumps(self.manifest))

    def test_repeatable_search_and_profile_without_network(self) -> None:
        """Checks unchanged bytes, JSON parsing, and repeatability without network access."""
        with patch('socket.socket', side_effect=AssertionError('Network access is forbidden')):
            first = load_recordings(self.manifest_path)
            second = load_recordings(self.manifest_path)
            response = first.get('SEARCH_DEMO', self.search_request)
            self.assertEqual(response, second.get('SEARCH_DEMO', self.search_request))
            self.assertEqual(response.body, (self.root / 'search.json').read_bytes())
            self.assertEqual(response.status, 200)
            parsed = response.json()
            self.assertIsInstance(parsed, dict)
            profile = first.get('PROFILE_DEMO', RequestKey('solr', '/select', (('q', 'id:sample-a'),)))
            self.assertEqual(profile.body, (self.root / 'profile.json').read_bytes())
            self.assertEqual(first.data_kind, 'synthetic')

    def test_validation_command_reads_selected_case(self) -> None:
        """Checks the development command reads a case and rejects synthetic data when requested."""
        output = StringIO()
        with (
            patch('sys.argv', ['validate_recordings', str(self.manifest_path), '--case', 'SEARCH_DEMO']),
            redirect_stdout(output),
        ):
            validate_recordings()
        self.assertIn('Validated 1 selected cases (synthetic)', output.getvalue())
        with (
            patch(
                'sys.argv',
                ['validate_recordings', str(self.manifest_path), '--case', 'SEARCH_DEMO', '--require-recorded'],
            ),
            redirect_stderr(StringIO()),
            self.assertRaises(SystemExit),
        ):
            validate_recordings()

    def test_query_changes_fail_instead_of_falling_back(self) -> None:
        """Checks that missing, reordered, duplicated, or changed filters cannot reuse a response."""
        recordings = load_recordings(self.manifest_path)
        for query in (self.query[:2], self.query[::-1], self.query + self.query[-1:], (('q', 'other topic'),)):
            with self.subTest(query=query), self.assertRaises(RecordingError):
                recordings.get('SEARCH_DEMO', RequestKey('solr', '/select', query))

    def test_case_selection_and_headers_are_part_of_matching(self) -> None:
        """Checks that another case or changed request headers cannot supply a response."""
        recordings = load_recordings(self.manifest_path)
        with self.assertRaises(RecordingError):
            recordings.get('PROFILE_DEMO', self.search_request)
        with self.assertRaises(RecordingError):
            recordings.for_case('MISSING')
        with self.assertRaises(RecordingError):
            recordings.get('SEARCH_DEMO', RequestKey('solr', '/select', self.query, (('Accept', 'text/plain'),)))

    def test_missing_and_changed_bodies_fail(self) -> None:
        """Checks that absent and modified body files cannot pass validation."""
        path = self.root / 'search.json'
        path.unlink()
        with self.assertRaisesRegex(RecordingError, 'missing'):
            load_recordings(self.manifest_path)
        path.write_bytes(b'changed')
        with self.assertRaisesRegex(RecordingError, 'checksum'):
            load_recordings(self.manifest_path)

    def test_duplicate_requests_fail(self) -> None:
        """Checks that ambiguous repeated requests are rejected."""
        self.entries.append({**self.entries[0], 'id': 'duplicate'})
        self.save_manifest()
        with self.assertRaisesRegex(RecordingError, 'unique'):
            load_recordings(self.manifest_path)

    def test_missing_case_dependency_fails(self) -> None:
        """Checks that an incomplete case cannot appear ready."""
        self.manifest['cases'] = {'PROFILE_DEMO': ['profile', 'missing-type-lookup']}
        self.save_manifest()
        with self.assertRaisesRegex(RecordingError, 'absent'):
            load_recordings(self.manifest_path)

    def test_body_paths_cannot_escape_bundle(self) -> None:
        """Checks traversal and symlinks cannot read data outside the bundle."""
        response = self.entries[0]['response']
        self.assertIsInstance(response, dict)
        if not isinstance(response, dict):
            self.fail('Invalid test response')
        for filename in ('../outside.json', '/outside.json'):
            with self.subTest(filename=filename):
                response['body_file'] = filename
                self.save_manifest()
                with self.assertRaises(RecordingError):
                    load_recordings(self.manifest_path)
        (self.root / 'outside-link').symlink_to(self.root.parent / 'outside.json')
        response['body_file'] = 'outside-link'
        self.save_manifest()
        with self.assertRaises(RecordingError):
            load_recordings(self.manifest_path)

    def test_recordings_inside_git_fail(self) -> None:
        """Checks the same storage rule for synthetic and real recordings."""
        (self.root / '.git').write_text('gitdir: ignored-for-this-check')
        with self.assertRaisesRegex(RecordingError, 'outside Git'):
            load_recordings(self.manifest_path)

    def test_invalid_metadata_and_pairs_fail(self) -> None:
        """Checks required provenance, version, and repeated-parameter representation."""
        for field, value in (('schema_version', True), ('data_kind', 'unknown'), ('captured_at', '2026-01-01')):
            original = self.manifest[field]
            self.manifest[field] = value
            self.save_manifest()
            with self.subTest(field=field), self.assertRaises(RecordingError):
                load_recordings(self.manifest_path)
            self.manifest[field] = original
        request = self.entries[0]['request']
        if not isinstance(request, dict):
            self.fail('Invalid test request')
        request['query'] = {'q': 'collapsed pairs'}
        self.save_manifest()
        with self.assertRaisesRegex(RecordingError, 'pairs'):
            load_recordings(self.manifest_path)

    def test_saved_http_error_is_preserved(self) -> None:
        """Checks a saved service error is returned without becoming a successful sample."""
        response = self.entries[0]['response']
        if not isinstance(response, dict):
            self.fail('Invalid test response')
        response['status'] = 503
        self.save_manifest()
        result = load_recordings(self.manifest_path).get('SEARCH_DEMO', self.search_request)
        self.assertEqual(result.status, 503)

    def test_invalid_json_body_reports_parse_failure(self) -> None:
        """Checks intact bytes may still fail JSON parsing and never become empty data."""
        body = b'not JSON'
        (self.root / 'search.json').write_bytes(body)
        response = self.entries[0]['response']
        if not isinstance(response, dict):
            self.fail('Invalid test response')
        response['sha256'] = hashlib.sha256(body).hexdigest()
        self.save_manifest()
        result = load_recordings(self.manifest_path).get('SEARCH_DEMO', self.search_request)
        with self.assertRaisesRegex(RecordingError, 'valid JSON'):
            result.json()
