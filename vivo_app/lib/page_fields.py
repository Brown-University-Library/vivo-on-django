"""
Checks the fields shared by prepared pages and future source processing.
"""

from html.parser import HTMLParser
from urllib.parse import urlsplit

from vivo_app.lib.prepared_data import PageDataError, object_value


class LocalHTML(HTMLParser):
    """Checks rich text for automatic loads outside the prepared assets."""

    def __init__(self, assets: set[str]) -> None:
        """
        Sets the available local assets.

        Called by: validate_page()
        """
        super().__init__()
        self.assets = assets

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """
        Rejects executable markup and checks embedded image references.

        Called by: HTMLParser.feed()
        """
        if tag not in {
            'a',
            'p',
            'div',
            'span',
            'br',
            'hr',
            'strong',
            'b',
            'i',
            'em',
            'u',
            's',
            'sub',
            'sup',
            'h2',
            'h3',
            'h4',
            'h5',
            'h6',
            'ul',
            'ol',
            'li',
            'dl',
            'dt',
            'dd',
            'table',
            'thead',
            'tbody',
            'tr',
            'th',
            'td',
            'blockquote',
            'img',
            'section',
            'small',
            'abbr',
            'cite',
        }:
            raise PageDataError('Profile rich text contains an unsupported HTML element.')
        for key, value in attrs:
            if key.lower().startswith('on') or key in {'style', 'srcset', 'background'}:
                raise PageDataError('Profile rich text contains an unsupported HTML attribute.')
            if key == 'src':
                if tag != 'img' or value is None:
                    raise PageDataError('Only local image sources are supported in profile rich text.')
                asset_url(value, self.assets)
            if key == 'href' and value:
                parsed = urlsplit(value)
                if parsed.scheme not in {'', 'https', 'http', 'mailto', 'tel'} or value.startswith('//'):
                    raise PageDataError('Profile rich text contains an unsupported link.')


def string_field(data: dict[str, object], name: str) -> str:
    """
    Requires a text field, permitting deliberately empty text.

    Called by: validate_page(), validate_search(), validate_profile(), validate_links()
    """
    value = data.get(name)
    if not isinstance(value, str):
        raise PageDataError(f'Prepared page field {name} must be text.')
    return value


def integer_field(data: dict[str, object], name: str, minimum: int = 0) -> int:
    """
    Requires an integer with a lower bound, excluding booleans.

    Called by: validate_search()
    """
    value = data.get(name)
    if type(value) is not int or value < minimum:
        raise PageDataError(f'Prepared page field {name} must be an integer of at least {minimum}.')
    return value


def object_list(data: dict[str, object], name: str) -> list[dict[str, object]]:
    """
    Requires a list of JSON objects.

    Called by: validate_search(), validate_profile(), validate_links()
    """
    value = data.get(name)
    if not isinstance(value, list):
        raise PageDataError(f'Prepared page field {name} must be a list.')
    return [object_value(item) for item in value]


def local_url(value: str) -> None:
    """
    Requires navigation within the local site.

    Called by: validate_links(), validate_search()
    """
    if not value.startswith('/') or value.startswith('//') or '\\' in value or any(c in value for c in '\r\n'):
        raise PageDataError('Prepared navigation must use site-relative URLs.')


def asset_url(value: str, assets: set[str]) -> None:
    """
    Requires an image or font already included in the validated bundle.

    Called by: LocalHTML.handle_starttag(), validate_search(), validate_profile()
    """
    prefix = '/__prepared_assets/'
    if not value.startswith(prefix) or value.removeprefix(prefix) not in assets:
        raise PageDataError('A page references an asset absent from the bundle.')


def validate_links(data: dict[str, object], name: str) -> None:
    """
    Checks labeled navigation links.

    Called by: validate_search()
    """
    for link in object_list(data, name):
        string_field(link, 'label')
        local_url(string_field(link, 'url'))


def validate_search(data: dict[str, object], assets: set[str]) -> None:
    """
    Checks result counts, pagination, filters, and required result fields.

    Called by: validate_page()
    """
    string_field(data, 'query')
    page, page_size = integer_field(data, 'page', 1), integer_field(data, 'page_size', 1)
    total = integer_field(data, 'total')
    results = object_list(data, 'results')
    if len(results) > page_size or len(results) > total or (results and (page - 1) * page_size + len(results) > total):
        raise PageDataError('Search results disagree with the saved counts or page number.')
    ids: set[str] = set()
    for result in results:
        for field in ('id', 'name', 'title', 'email'):
            string_field(result, field)
        identifier = string_field(result, 'id')
        if not identifier or identifier in ids:
            raise PageDataError('Search result identifiers must be present and unique within a page.')
        ids.add(identifier)
        local_url(string_field(result, 'url'))
        asset_url(string_field(result, 'thumbnail'), assets)
    validate_links(data, 'pagination')
    validate_links(data, 'selected_filters')
    for field in ('previous_url', 'next_url', 'remove_query_url'):
        value = string_field(data, field)
        if value:
            local_url(value)
    for facet in object_list(data, 'facets'):
        string_field(facet, 'name')
        string_field(facet, 'title')
        for value in object_list(facet, 'values'):
            string_field(value, 'text')
            integer_field(value, 'count')
            local_url(string_field(value, 'url'))
            if type(value.get('selected')) is not bool:
                raise PageDataError('Facet selection must be true or false.')


def validate_profile(data: dict[str, object], assets: set[str]) -> None:
    """
    Checks profile identity, optional sections, and local image dependencies.

    Called by: validate_page()
    """
    for field in ('id', 'name', 'title'):
        string_field(data, field)
    asset_url(string_field(data, 'thumbnail'), assets)
    sections = object_list(data, 'sections')
    names: set[str] = set()
    for section in sections:
        name = string_field(section, 'id')
        if name not in {'Overview', 'Publications', 'Research', 'Background', 'Affiliations', 'Teaching'} or name in names:
            raise PageDataError('Profile sections must have unique supported names.')
        names.add(name)
        string_field(section, 'label')
        parser = LocalHTML(assets)
        parser.feed(string_field(section, 'html'))
        parser.close()
    if not sections or sections[0].get('id') != 'Overview':
        raise PageDataError('Profiles must begin with the Overview section.')


def validate_page(family: str, data: dict[str, object], assets: set[str]) -> None:
    """
    Validates a page before any template can use it.

    Called by: prepared_data.read_entry()
    """
    if family == 'search':
        validate_search(data, assets)
    elif family == 'profile':
        validate_profile(data, assets)
