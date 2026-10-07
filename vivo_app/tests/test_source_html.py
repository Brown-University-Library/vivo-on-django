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

    def test_email_link_preserves_destination_and_visible_formatting(self) -> None:
        """
        Checks an overview retains its email destination while escaping attributes.
        """
        html = render_profile_html(
            '<p>Contact <a href="mailto:editor@example.invalid?subject=A&amp;body=&quot;B&quot;" '
            'onclick="run()"><strong>the editor</strong></a>.</p>'
        )
        self.assertEqual(
            html,
            '<p>Contact <a href="mailto:editor@example.invalid?subject=A&amp;body=&quot;B&quot;">'
            '<strong>the editor</strong></a>.</p>',
        )

    def test_empty_email_and_non_email_destinations_keep_only_visible_text(self) -> None:
        """
        Checks empty email addresses, unexpected authorities and controls are rejected.
        """
        for href in (
            'mailto:',
            'mailto:?subject=Hello',
            'mailto://example.invalid/editor',
            'mailto:\neditor@example.invalid',
        ):
            with self.subTest(href=href):
                self.assertEqual(render_profile_html(f'<a href="{href}">Contact</a>'), 'Contact')
