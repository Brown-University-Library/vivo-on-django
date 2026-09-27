"""
Checks the fields shared by prepared pages and future source processing.
"""

import math
import re
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


class SearchMatchHTML(HTMLParser):
    """Checks the small amount of formatting allowed in a search-match preview."""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """
        Allows text formatting without links, embedded resources, or attributes.

        Called by: HTMLParser.feed()
        """
        if tag not in {'p', 'strong', 'b', 'em', 'br'} or attrs:
            raise PageDataError('Search-match previews may contain only simple text formatting.')


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
        if 'matches_html' in result or 'matches_url' in result:
            markup = string_field(result, 'matches_html')
            destination = string_field(result, 'matches_url')
            if bool(markup) != bool(destination):
                raise PageDataError('Search-match previews need both text and a destination.')
            if destination:
                local_url(destination)
                target = urlsplit(destination)
                if target.path != urlsplit(string_field(result, 'url')).path or target.fragment != 'All':
                    raise PageDataError('Search-match links must open all sections of the same result.')
            parser = SearchMatchHTML()
            parser.feed(markup)
            parser.close()
    validate_links(data, 'pagination')
    validate_links(data, 'selected_filters')
    for selected in object_list(data, 'selected_filters'):
        if ('category' in selected or 'value' in selected) and (
            not string_field(selected, 'category').strip() or not string_field(selected, 'value').strip()
        ):
            raise PageDataError('Selected filters need both a category and a value when supplied separately.')
    for field in ('previous_url', 'next_url', 'remove_query_url'):
        value = string_field(data, field)
        if value:
            local_url(value)
    facet_names: set[str] = set()
    for facet in object_list(data, 'facets'):
        name = string_field(facet, 'name')
        if not re.fullmatch(r'[a-z][a-z0-9_]*', name) or name in facet_names:
            raise PageDataError('Facet names must be unique lowercase identifiers.')
        facet_names.add(name)
        string_field(facet, 'title')
        validate_facet_values(object_list(facet, 'values'))
        if 'more_values' in facet:
            validate_facet_values(object_list(facet, 'more_values'))


def validate_facet_values(values: list[dict[str, object]]) -> None:
    """
    Checks visible and complete facet lists before templates or scripts use them.

    Called by: validate_search()
    """
    names: set[str] = set()
    for value in values:
        name = string_field(value, 'text')
        if not name or name in names:
            raise PageDataError('Facet values must have unique nonempty labels.')
        names.add(name)
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
    validate_profile_details(data, assets, names)


def validate_profile_details(data: dict[str, object], assets: set[str], sections: set[str]) -> None:
    """
    Checks optional contact fields and exact publication groups in newer bundles.

    Called by: validate_profile()
    """
    if 'page_title' in data:
        string_field(data, 'page_title')
    if 'email' in data:
        email = string_field(data, 'email')
        if any(character in email for character in '\r\n'):
            raise PageDataError('Profile email must fit on one line.')
    if 'cv_url' in data:
        cv_url = string_field(data, 'cv_url')
        if cv_url:
            local_url(cv_url)
            if not urlsplit(cv_url).path.startswith('/docs/'):
                raise PageDataError('Profile CV links must name a prepared document.')
    if 'publications' in data or 'publication_filters' in data:
        counts: dict[str, int] = {}
        for publication in object_list(data, 'publications'):
            kind = string_field(publication, 'type')
            if not re.fullmatch(r'_[a-z_]+', kind):
                raise PageDataError('Publication types must use supported identifier characters.')
            counts[kind] = counts.get(kind, 0) + 1
            parser = LocalHTML(assets)
            parser.feed(string_field(publication, 'html'))
            parser.close()
        filters: dict[str, int] = {}
        for item in object_list(data, 'publication_filters'):
            kind = string_field(item, 'id')
            if kind in filters or not string_field(item, 'label').strip():
                raise PageDataError('Publication filters need unique types and labels.')
            filters[kind] = integer_field(item, 'count', 1)
        if filters != counts or bool(counts) != ('Publications' in sections):
            raise PageDataError('Publication filters, rows, and sections must agree.')


def validate_organization(data: dict[str, object], assets: set[str]) -> None:
    """
    Checks organization content, ordered roles, and local member images.

    Called by: validate_page()
    """
    for field in ('id', 'name', 'page_title'):
        if not string_field(data, field).strip():
            raise PageDataError('Organization identity and title must be present.')
    asset_url(string_field(data, 'image'), assets)
    parser = LocalHTML(assets)
    parser.feed(string_field(data, 'overview_html'))
    parser.close()
    for link in object_list(data, 'website_links'):
        string_field(link, 'label')
        url = string_field(link, 'url')
        parsed = urlsplit(url)
        if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
            raise PageDataError('Organization website links need an HTTP address.')
    for group in ('administrative_positions', 'faculty_positions'):
        for member in object_list(data, group):
            for field in ('name', 'title'):
                string_field(member, field)
            url = string_field(member, 'url')
            local_url(url)
            if not urlsplit(url).path.startswith('/display/'):
                raise PageDataError('Organization member links must open a local display page.')
            asset_url(string_field(member, 'image'), assets)
    visual_url = string_field(data, 'visualization_url')
    if visual_url:
        local_url(visual_url)
        if urlsplit(visual_url).path != '/display/' + string_field(data, 'id') + '/viz/collab':
            raise PageDataError('Organization visualization must match its identity.')
    graph = object_value(data.get('visualization_graph'))
    view_box = string_field(graph, 'view_box')
    if len(view_box.split()) != 4 or any(not valid_graph_number(value) for value in view_box.split()):
        raise PageDataError('Organization graph needs a numeric view box.')
    for line in object_list(graph, 'lines'):
        if any(not valid_graph_number(line.get(field)) for field in ('x1', 'y1', 'x2', 'y2')):
            raise PageDataError('Organization graph lines need numeric coordinates.')
    for node in object_list(graph, 'nodes'):
        if any(not valid_graph_number(node.get(field)) for field in ('x', 'y', 'radius')):
            raise PageDataError('Organization graph nodes need numeric coordinates and sizes.')
        if node.get('color') not in {'rgb(174, 199, 232)', 'rgb(31, 119, 180)', 'rgb(255, 127, 14)'}:
            raise PageDataError('Organization graph nodes need a supported color.')


def valid_graph_number(value: object) -> bool:
    """
    Accepts finite numbers in saved SVG geometry without executable text.

    Called by: validate_organization()
    """
    result = False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        result = math.isfinite(value)
    elif isinstance(value, str) and re.fullmatch(r'-?\d+(?:\.\d+)?', value):
        result = math.isfinite(float(value))
    return result


def validate_home(data: dict[str, object], assets: set[str]) -> None:
    """
    Checks saved homepage backgrounds, book groups, image bytes, and profile links.

    Called by: validate_page()
    """
    backgrounds = data.get('backgrounds')
    if not isinstance(backgrounds, list) or not backgrounds:
        raise PageDataError('The homepage needs saved backgrounds.')
    for background in backgrounds:
        if not isinstance(background, str):
            raise PageDataError('Homepage backgrounds must be text URLs.')
        asset_url(background, assets)
    pages = data.get('book_covers_paginated')
    if not isinstance(pages, list) or not pages:
        raise PageDataError('The homepage needs at least one saved book group.')
    for page in pages:
        if not isinstance(page, list) or not 1 <= len(page) <= 4:
            raise PageDataError('Each homepage book group needs one to four covers.')
        for item in page:
            book = object_value(item)
            string_field(book, 'title')
            author_url = string_field(book, 'author_url')
            local_url(author_url)
            if not urlsplit(author_url).path.startswith('/display/'):
                raise PageDataError('A book cover must link to a local display page.')
            asset_url(string_field(book, 'image_url'), assets)


def validate_page(family: str, data: dict[str, object], assets: set[str]) -> None:
    """
    Validates a page before any template can use it.

    Called by: prepared_data.read_entry()
    """
    if family == 'search':
        validate_search(data, assets)
    elif family == 'profile':
        validate_profile(data, assets)
    elif family == 'organization':
        validate_organization(data, assets)
    elif family == 'home':
        validate_home(data, assets)
