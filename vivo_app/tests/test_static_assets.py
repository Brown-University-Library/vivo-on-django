"""
Checks browsers receive new asset addresses after stylesheet or script updates.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.template import Context, Template
from django.test import SimpleTestCase

from vivo_app.lib.static_assets import versioned_asset_url


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
