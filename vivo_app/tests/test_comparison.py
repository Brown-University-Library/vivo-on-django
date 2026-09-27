"""
Checks comparison rules with invented observations and images.
"""

import json
import tempfile
from pathlib import Path

from PIL import Image
from django.test import SimpleTestCase

from tools.compare_sites import compare_snapshots, image_difference, normalize_url, read_cases


class ComparisonTests(SimpleTestCase):
    """Checks meaningful changes, missing evidence, and portable case inputs."""

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
        self.assertIn('local: missing image', compare_snapshots(expected, changed))

    def test_pixel_changes_and_size_changes(self) -> None:
        """
        Checks a one-pixel layout change and different image dimensions cannot pass.
        """
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
        Checks malformed or repeated identifiers cannot overwrite comparison evidence.
        """
        case = {'id': 'invented', 'path': '/example', 'width': 800, 'height': 600, 'selectors': {'heading': 'h1'}}
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / 'cases.json'
            manifest.write_text(json.dumps({'cases': [case]}))
            self.assertEqual(read_cases(manifest)[1][0].id, 'invented')
            manifest.write_text(json.dumps({'cases': [case, case]}))
            with self.assertRaises(ValueError):
                read_cases(manifest)
