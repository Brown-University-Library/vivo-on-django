"""
Checks comparison rules with invented observations and images.
"""

import json
import tempfile
from importlib.util import find_spec
from pathlib import Path
from unittest import skipUnless

from django.test import SimpleTestCase

from tools.compare_sites import Case, compare_snapshots, image_difference, normalize_url, read_cases, select_cases


class ComparisonTests(SimpleTestCase):
    """Checks meaningful changes, missing comparison records, and portable case inputs."""

    def test_url_normalization_retains_repeated_values(self) -> None:
        """
        Checks site origins and parameter-name order normalize without losing filter order.
        """
        origin = 'https://example.invalid'
        self.assertEqual(
            normalize_url(origin + '/search?q=Example&fq=a&fq=b#All', origin), '/search?fq=a&fq=b&q=Example#All'
        )
        self.assertNotEqual(normalize_url('/search?fq=a&fq=b', origin), normalize_url('/search?fq=b&fq=a', origin))
        self.assertEqual(normalize_url('https://elsewhere.invalid/page', origin), 'https://elsewhere.invalid/page')

    def test_missing_evidence_is_not_a_pass(self) -> None:
        """
        Checks two empty or unsuccessful captures do not count as equivalent pages.
        """
        self.assertTrue(compare_snapshots({}, {}))
        snapshot: dict[str, object] = {'capture_error': 'Invented missing page'}
        self.assertIn('reference: capture_error', compare_snapshots(snapshot, snapshot))

    def test_changed_observations_are_reported(self) -> None:
        """
        Checks status, destination, type, text, and missing images independently.
        """
        expected: dict[str, object] = {
            'viewport': [800, 600],
            'status': 200,
            'content_type': 'text/html',
            'final_url': '/example',
            'title': 'Example',
            'text': {'heading': ['Example']},
            'images': [{'alt': 'Invented image', 'loaded': True}],
        }
        self.assertEqual(compare_snapshots(expected, expected), [])
        for field, replacement in [
            ('status', 404),
            ('content_type', 'text/plain'),
            ('final_url', '/moved'),
            ('text', {'heading': ['Different']}),
        ]:
            with self.subTest(field=field):
                self.assertIn('Changed ' + field, compare_snapshots(expected, {**expected, field: replacement}))
        changed = {**expected, 'images': [{'alt': 'Invented image', 'loaded': False}]}
        self.assertIn('current: missing image', compare_snapshots(expected, changed))

    @skipUnless(find_spec('PIL') is not None, 'Pillow is available in the local and staging dependency groups.')
    def test_pixel_changes_and_size_changes(self) -> None:
        """
        Checks a one-pixel layout change and different image dimensions cannot pass.
        """
        from PIL import Image

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = Image.new('RGB', (20, 20), 'white')
            image.save(root / 'expected.png')
            image.save(root / 'same.png')
            self.assertEqual(
                image_difference(root / 'expected.png', root / 'same.png', root / 'same-diff.png')['changed_ratio'], 0
            )
            image.putpixel((4, 4), (0, 0, 0))
            image.save(root / 'changed.png')
            self.assertEqual(
                image_difference(root / 'expected.png', root / 'changed.png', root / 'diff.png')['changed_pixels'], 1
            )
            Image.new('RGB', (21, 20)).save(root / 'size.png')
            self.assertTrue(
                image_difference(root / 'expected.png', root / 'size.png', root / 'size-diff.png')['different_size']
            )

    def test_manifest_rejects_repeated_case_ids(self) -> None:
        """
        Checks malformed or repeated identifiers cannot overwrite saved comparisons.
        """
        case = {
            'id': 'invented',
            'path': '/example',
            'width': 800,
            'height': 600,
            'selectors': {'heading': 'h1'},
            'screenshot_css': '.dynamic-image { background-image: none !important; }',
        }
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / 'cases.json'
            manifest.write_text(json.dumps({'cases': [case]}))
            parsed_case = read_cases(manifest)[1][0]
            self.assertEqual(parsed_case.id, 'invented')
            self.assertIn('background-image', parsed_case.screenshot_css)
            manifest.write_text(json.dumps({'cases': [case, case]}))
            with self.assertRaises(ValueError):
                read_cases(manifest)

    def test_case_selection_preserves_manifest_order(self) -> None:
        """
        Checks named cases retain manifest order and unknown names fail clearly.
        """
        cases = [Case('first', '/first', 800, 600, {}), Case('second', '/second', 800, 600, {})]
        self.assertEqual([case.id for case in select_cases(cases, ['second', 'first'], None)], ['first', 'second'])
        with self.assertRaisesRegex(ValueError, 'Unknown case IDs: missing'):
            select_cases(cases, ['missing'], None)

    def test_failed_case_selection_reads_an_earlier_report(self) -> None:
        """
        Checks an earlier report selects only cases that did not pass.
        """
        cases = [Case('first', '/first', 800, 600, {}), Case('second', '/second', 800, 600, {})]
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / 'report.json'
            report.write_text(
                json.dumps(
                    {
                        'cases': [
                            {'case': 'first', 'result': 'pass'},
                            {'case': 'second', 'result': 'needs_review'},
                        ]
                    }
                )
            )
            self.assertEqual([case.id for case in select_cases(cases, [], report)], ['second'])
