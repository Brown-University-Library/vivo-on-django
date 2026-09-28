"""
Checks that public templates and every declared font load from application static files.
"""

import re
from pathlib import Path
from urllib.parse import urljoin

from django.contrib.staticfiles import finders
from django.http import FileResponse
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, override_settings

from vivo_app.management.commands.runserver import Command


@override_settings(DEBUG=True, STATIC_URL='/static/')
class FontTests(SimpleTestCase):
    """Checks font delivery independently of prepared page bundles or remote services."""

    def test_public_templates_share_local_fonts(self) -> None:
        """
        Checks that prototype and prepared pages select the same local font stylesheet.
        """
        request = RequestFactory().get('/')
        for mode in ['prototype', 'prepared']:
            with self.subTest(mode=mode), override_settings(PAGE_DATA_MODE=mode):
                html = render_to_string('base.html', request=request)
                self.assertIn('/static/css/fonts.css', html)
                self.assertNotIn('fonts.googleapis.com', html)
                self.assertNotIn('/__prepared_assets/source-sans-pro.ttf', html)

    @override_settings(PAGE_DATA_MODE='prototype')
    def test_declared_fonts_are_served_locally(self) -> None:
        """
        Checks that the character subsets and icon font all resolve to real local WOFF2 responses.
        """
        handler = Command().get_handler(use_static_handler=True, insecure_serving=False)
        fonts: set[str] = set()
        for stylesheet in ['fonts.css', 'bootstrap.css']:
            path = finders.find('css/' + stylesheet)
            assert isinstance(path, str)
            css = Path(path).read_text()
            sources = re.findall(r'url\([\'"]?([^\s)\'"]+\.woff2)[\'"]?\)', css)
            fonts.update(urljoin('/static/css/' + stylesheet, source) for source in sources)
        self.assertEqual(len(fonts), 8)
        for url in sorted(fonts):
            with self.subTest(url=url):
                self.assertTrue(url.startswith('/static/fonts/'))
                response = handler.get_response(RequestFactory().get(url))
                assert isinstance(response, FileResponse)
                try:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response['Content-Type'], 'font/woff2')
                    self.assertTrue(response.getvalue().startswith(b'wOF2'))
                finally:
                    response.close()
