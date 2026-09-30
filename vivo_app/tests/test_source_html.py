"""
Checks safe rendering of source profile text.
"""

from django.test import SimpleTestCase

from vivo_app.lib.source_html import render_profile_html


class SourceHTMLTests(SimpleTestCase):
    """Checks formatting and links without allowing source markup to run code."""

    def test_basic_formatting_and_link_are_preserved(self) -> None:
        """
        Checks an awards list keeps its readable structure and web link.
        """
        html = render_profile_html(
            '<ul><li><strong>Winner</strong> <a href="https://example.invalid/award">Award</a></li></ul>'
        )
        self.assertEqual(
            html,
            '<ul><li><strong>Winner</strong> <a href="https://example.invalid/award">Award</a></li></ul>',
        )

    def test_active_markup_and_unsafe_links_are_removed(self) -> None:
        """
        Checks scripts, event handlers, and unsafe links do not enter the page.
        """
        html = render_profile_html(
            '<p onclick="run()">A &amp; B <a href="javascript:run()">bad</a> '
            '<a href="https://example.invalid/?q=&quot;x&quot;" onmouseover="run()">good</a>'
            '<script>run()</script><img src="x" onerror="run()"></p>'
        )
        self.assertEqual(html, '<p>A &amp; B bad <a href="https://example.invalid/?q=&quot;x&quot;">good</a></p>')
