"""
Preserves basic formatting in source profile text without trusting its markup.
"""

from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit

TEXT_TAGS = {'p', 'div', 'span', 'ul', 'ol', 'li', 'strong', 'b', 'em', 'i', 'u', 'blockquote', 'sup', 'sub'}
BLOCKED_TAGS = {'script', 'style', 'iframe', 'object', 'svg', 'math', 'template', 'form'}


def safe_profile_link(value: str) -> bool:
    """
    Accepts an absolute web link without control characters.

    Called by: ProfileHTML.handle_starttag()
    """
    parsed = urlsplit(value)
    return parsed.scheme in {'http', 'https'} and bool(parsed.netloc) and not any(ord(char) < 32 for char in value)


class ProfileHTML(HTMLParser):
    """Builds a small set of safe tags from source profile text."""

    def __init__(self) -> None:
        """
        Starts a parser with escaped text and no open tags.

        Called by: render_profile_html()
        """
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.open_tags: list[tuple[str, str]] = []
        self.blocked_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """
        Keeps basic formatting and safe links while discarding active content.

        Called by: HTMLParser.feed()
        """
        if self.blocked_depth:
            if tag in BLOCKED_TAGS:
                self.blocked_depth += 1
        elif tag in BLOCKED_TAGS:
            self.blocked_depth = 1
        elif tag == 'br':
            self.parts.append('<br>')
        elif tag == 'a':
            href = next((value for name, value in attrs if name == 'href' and value is not None), '')
            if safe_profile_link(href):
                self.parts.append('<a href="' + escape(href, quote=True) + '">')
                self.open_tags.append((tag, tag))
            else:
                self.open_tags.append((tag, ''))
        elif tag in TEXT_TAGS:
            self.parts.append('<' + tag + '>')
            self.open_tags.append((tag, tag))
        else:
            self.open_tags.append((tag, ''))

    def handle_endtag(self, tag: str) -> None:
        """
        Closes only tags emitted by this parser.

        Called by: HTMLParser.feed()
        """
        if self.blocked_depth:
            if tag in BLOCKED_TAGS:
                self.blocked_depth -= 1
        else:
            matching = next(
                (index for index in range(len(self.open_tags) - 1, -1, -1) if self.open_tags[index][0] == tag), -1
            )
            if matching >= 0:
                for _, emitted in reversed(self.open_tags[matching:]):
                    if emitted:
                        self.parts.append('</' + emitted + '>')
                del self.open_tags[matching:]

    def handle_data(self, data: str) -> None:
        """
        Escapes visible text outside blocked tags.

        Called by: HTMLParser.feed()
        """
        if not self.blocked_depth:
            self.parts.append(escape(data))

    def html(self) -> str:
        """
        Closes remaining safe tags and returns the rendered HTML.

        Called by: render_profile_html()
        """
        self.close()
        for _, emitted in reversed(self.open_tags):
            if emitted:
                self.parts.append('</' + emitted + '>')
        return ''.join(self.parts)


def render_profile_html(raw: str) -> str:
    """
    Keeps basic source formatting and web links for a profile text field.

    Called by: source_pages.profile_sections()
    """
    parser = ProfileHTML()
    parser.feed(raw)
    return parser.html()
