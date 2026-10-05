"""
Checks browsers receive new asset addresses after stylesheet or script updates.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.core.checks import Tags, run_checks
from django.template import Context, Template
from django.test import SimpleTestCase

from vivo_app.checks import check_static_collection
from vivo_app.lib.static_assets import collected_asset_differences, versioned_asset_url


class StaticAssetTests(SimpleTestCase):
    def test_updated_contents_change_the_browser_address(self) -> None:
        """
        Checks unchanged files reuse an address and changed contents get a new one.
        """
        with TemporaryDirectory() as directory:
            script = Path(directory) / 'example.js'
            script.write_text('first version', encoding='utf-8')
            with patch('vivo_app.lib.static_assets.finders.find', return_value=str(script)):
                first = versioned_asset_url('js/example.js')
                self.assertEqual(versioned_asset_url('js/example.js'), first)
                script.write_text('second version', encoding='utf-8')
                second = versioned_asset_url('js/example.js')
            self.assertNotEqual(first, second)
            self.assertEqual(urlsplit(first).path, urlsplit(second).path)
            self.assertTrue(parse_qs(urlsplit(second).query)['v'][0])

    def test_missing_asset_keeps_its_delivery_address(self) -> None:
        """
        Checks a missing file does not receive a made-up replacement or version.
        """
        with (
            patch('vivo_app.lib.static_assets.finders.find', return_value=None),
            patch('vivo_app.lib.static_assets.static', return_value='/static/missing.js'),
        ):
            self.assertEqual(versioned_asset_url('missing.js'), '/static/missing.js')

    def test_template_preserves_configured_prefix_and_query(self) -> None:
        """
        Checks the template tag keeps configured paths, query values, and fragments.
        """
        with TemporaryDirectory() as directory:
            style = Path(directory) / 'example.css'
            style.write_text('body {}', encoding='utf-8')
            with (
                patch('vivo_app.lib.static_assets.finders.find', return_value=str(style)),
                patch('vivo_app.lib.static_assets.static', return_value='/prefix/static/example.css?key=a&key=b#part'),
            ):
                rendered = Template('{% load asset_urls %}{% versioned_static "example.css" %}').render(Context())
        parts = urlsplit(rendered.replace('&amp;', '&'))
        self.assertEqual(parts.path, '/prefix/static/example.css')
        self.assertEqual(parts.fragment, 'part')
        self.assertEqual(parse_qs(parts.query)['key'], ['a', 'b'])
        self.assertIn('v', parse_qs(parts.query))

    def test_profile_template_versions_changed_section_script(self) -> None:
        """
        Checks the profile template requests the section script with a content version.
        """
        markup = Template('{% include "display/show.html" %}').render(Context({'entity': {'label': 'Example'}}))
        self.assertIn(versioned_asset_url('js/tabs.js'), markup)


class StaticCollectionTests(SimpleTestCase):
    def setUp(self) -> None:
        """
        Prepares made-up application sources and collected copies.

        Called by: unittest.TestCase.run()
        """
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.source = self.root / 'vivo_app' / 'static'
        self.collected = self.root / 'collected'
        (self.source / 'css').mkdir(parents=True)
        (self.source / 'js').mkdir()
        (self.collected / 'css').mkdir(parents=True)
        (self.collected / 'js').mkdir()
        (self.source / 'css' / 'example.css').write_text('body {}')
        (self.source / 'js' / 'example.js').write_text('first version')
        (self.collected / 'css' / 'example.css').write_text('body {}')
        (self.collected / 'js' / 'example.js').write_text('first version')

    def test_matching_copies_pass_without_checking_other_assets(self) -> None:
        """
        Checks matching scripts and styles pass while unrelated images remain separate.
        """
        (self.source / 'example.png').write_bytes(b'made-up image')
        with self.settings(BASE_DIR=self.root, STATIC_ROOT=self.collected):
            self.assertEqual(check_static_collection(), [])

    def test_missing_and_stale_copies_fail_without_disclosing_directories(self) -> None:
        """
        Checks missing styles and stale scripts produce a useful deployment error.
        """
        (self.collected / 'css' / 'example.css').unlink()
        (self.collected / 'js' / 'example.js').write_text('older version')
        self.assertEqual(collected_asset_differences(self.source, self.collected), ['css/example.css', 'js/example.js'])
        with self.settings(BASE_DIR=self.root, STATIC_ROOT=self.collected):
            messages = check_static_collection()
        self.assertEqual([message.id for message in messages], ['vivo_app.E002'])
        self.assertIn('2 collected', messages[0].msg)
        self.assertIn('collectstatic', str(messages[0].hint))
        self.assertNotIn(str(self.root), str(messages[0]))

    def test_comparison_uses_the_same_source_as_versioned_urls(self) -> None:
        """
        Checks a configured source override supplies the contents to compare.
        """
        (self.source / 'css' / 'example.css').unlink()
        override = self.root / 'override.js'
        override.write_text('overridden version')
        (self.collected / 'js' / 'example.js').write_text('overridden version')
        with patch('vivo_app.lib.static_assets.finders.find', return_value=str(override)):
            self.assertEqual(collected_asset_differences(self.source, self.collected), [])

    def test_missing_root_and_source_files_fail_explicitly(self) -> None:
        """
        Checks unavailable collection settings or application sources cannot pass.
        """
        with self.settings(BASE_DIR=self.root, STATIC_ROOT=''):
            self.assertEqual([message.id for message in check_static_collection()], ['vivo_app.E002'])
        with self.settings(BASE_DIR=self.root / 'absent', STATIC_ROOT=self.collected):
            self.assertEqual([message.id for message in check_static_collection()], ['vivo_app.E003'])

    def test_check_runs_only_when_deployment_checks_are_requested(self) -> None:
        """
        Checks ordinary startup skips the file comparison while deployment checks run it.
        """
        (self.collected / 'js' / 'example.js').write_text('older version')
        with self.settings(BASE_DIR=self.root, STATIC_ROOT=self.collected):
            ordinary = run_checks(tags=[Tags.staticfiles])
            deployment = run_checks(tags=[Tags.staticfiles], include_deployment_checks=True)
        self.assertNotIn('vivo_app.E002', [message.id for message in ordinary])
        self.assertIn('vivo_app.E002', [message.id for message in deployment])
