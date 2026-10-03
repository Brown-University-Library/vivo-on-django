"""
Applies the public citation model's text, quotation, and punctuation rules.
"""

from vivo_app.lib.source_html import render_citation_html


def citation_text(value: object) -> str:
    """
    Reads text and numeric source citation values without displaying other objects.

    Called by: source_pages.publication_html(), source_pages.publication_book_html(), source_pages.publication_book_section_html()
    """
    if isinstance(value, list):
        value = value[0] if value else None
    result = str(value).strip() if isinstance(value, (str, int, float)) and not isinstance(value, bool) else ''
    return result


def citation_period(value: str) -> str:
    """
    Adds a final period without removing existing periods or earlier commas.

    Called by: source_pages.publication_html(), source_pages.publication_book_html(), source_pages.publication_book_section_html()
    """
    result = value.strip()
    if not result.endswith('.'):
        result = result.removesuffix(',') + '.'
    return result


def citation_append(value: str, detail: str, delimiter: str = ',') -> str:
    """
    Appends one citation detail with one required trailing separator.

    Called by: source_pages.publication_html(), source_pages.publication_book_html(), source_pages.publication_book_section_html()
    """
    result = value
    clean_detail = detail.strip()
    if clean_detail:
        result = (value.rstrip() + ' ' if value else '') + clean_detail
        if not result.endswith(delimiter):
            result += delimiter
    return result


def citation_title(value: object) -> str:
    """
    Quotes a title once while retaining nested quotes and existing final periods.

    Called by: source_pages.publication_html(), source_pages.publication_book_section_html()
    """
    text = citation_text(value)
    result = ''
    if text:
        text = text.removeprefix('“').removesuffix('”')
        if not text.startswith('"'):
            text = '"' + text
        if not text.endswith('"'):
            text += '"'
        if len(text) < 2 or text[-2] != '.':
            text = text[:-1] + '."'
        result = render_citation_html(text)
    return result
