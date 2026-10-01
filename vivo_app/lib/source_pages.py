"""
Turns recorded or live Solr documents into the existing page templates' data.
"""

import json
import math
import re
from collections import Counter
from collections.abc import Callable
from datetime import date
from html import escape
from urllib.parse import quote, urlencode, urlsplit

from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone

from vivo_app.lib.prepared_data import MissingRecordError, PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RequestKey
from vivo_app.lib.source_html import render_profile_html
from vivo_app.lib.source_requests import (
    FACETS,
    FACET_TITLES,
    image_path,
    local_document_url,
    member_details_key,
    member_key,
    profile_key,
    read_source,
    search_key,
    source_origin,
    team_member_key,
)

SourceReader = Callable[[RequestKey, str], RecordedResponse]


def response_object(key: RequestKey, mode: str, reader: SourceReader) -> dict[str, object]:
    """
    Requires one valid Solr JSON response with a successful application status.

    Called by: search_data(), profile_data(), organization_thumbnail()
    """
    response = reader(key, mode)
    try:
        value: object = json.loads(response.body)
    except (ValueError, UnicodeError) as exc:
        raise PageDataError('Solr returned invalid JSON.') from exc
    if not isinstance(value, dict) or not isinstance(value.get('responseHeader'), dict):
        raise PageDataError('Solr returned an unexpected response.')
    if value['responseHeader'].get('status') != 0 or not isinstance(value.get('response'), dict):
        raise PageDataError('Solr did not complete the requested query.')
    return value


def documents(response: dict[str, object]) -> tuple[list[dict[str, object]], int]:
    """
    Extracts documents and an exact result count from a Solr response.

    Called by: search_data(), profile_data(), organization_thumbnail()
    """
    body = response.get('response')
    if not isinstance(body, dict) or not isinstance(body.get('docs'), list):
        raise PageDataError('Solr returned an unexpected document list.')
    count = body.get('numFound')
    if type(count) is not int or count < 0:
        raise PageDataError('Solr returned an invalid result count.')
    docs: list[dict[str, object]] = []
    for value in body['docs']:
        if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
            raise PageDataError('Solr returned an invalid document.')
        docs.append(value)
    return docs, count


def first_text(value: object) -> str:
    """
    Reads a single text value from Solr's scalar or one-element array fields.

    Called by: record_data(), search_data(), profile_data(), organization_thumbnail()
    """
    if isinstance(value, list):
        value = value[0] if value else None
    return value if isinstance(value, str) else ''


def record_data(doc: dict[str, object]) -> dict[str, object]:
    """
    Parses the JSON record embedded in a Solr document.

    Called by: search_data(), profile_data()
    """
    raw = first_text(doc.get('json_txt'))
    try:
        value: object = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise PageDataError('A Solr document contains invalid record JSON.') from exc
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise PageDataError('A Solr document contains an invalid record.')
    return value


def record_id(doc: dict[str, object]) -> str:
    """
    Reads a safe short identifier from a canonical Solr document ID.

    Called by: search_data(), profile_data(), organization_thumbnail()
    """
    value = first_text(doc.get('id'))
    prefix = 'http://vivo.brown.edu/individual/'
    identifier = value.removeprefix(prefix) if value.startswith(prefix) else ''
    if re.fullmatch(r'[A-Za-z0-9_-]{1,80}', identifier) is None:
        raise PageDataError('A Solr document has an unsupported identifier.')
    return identifier


def thumbnail_url(doc: dict[str, object], organization: bool = False) -> str:
    """
    Uses a source image URL or the site's type-specific placeholder.

    Called by: search_data(), profile_data(), organization_thumbnail()
    """
    path = image_path(doc.get('thumbnail_file_path_s'))
    fallback = 'images/org_placeholder.png' if organization else 'images/person_placeholder.jpg'
    result = reverse('source_image', kwargs={'filename': path.lstrip('/')}) if path else static(fallback)
    return result


def search_inputs(pairs: list[tuple[str, str]]) -> tuple[str, int, list[tuple[str, str]]]:
    """
    Accepts the first journey's query, page, and repeated facet filters.

    Called by: search_data()
    """
    if any(key not in {'q', 'page', 'fq'} and re.fullmatch(r'fq_[0-9]+', key) is None for key, _ in pairs):
        raise PageDataError('This live search option has not been implemented.')
    queries = [value for key, value in pairs if key == 'q']
    pages = [value for key, value in pairs if key == 'page']
    if len(queries) > 1 or len(pages) > 1 or (pages and re.fullmatch(r'[1-9][0-9]{0,2}', pages[0]) is None):
        raise PageDataError('The requested search query or page is invalid.')
    filters: list[tuple[str, str]] = []
    for key, value in pairs:
        if key == 'fq' or re.fullmatch(r'fq_[0-9]+', key):
            field, separator, text = value.partition('|')
            if not separator or field not in FACETS or not text:
                raise PageDataError('The requested search filter is unsupported.')
            if (field, text) not in filters:
                filters.append((field, text))
    return (queries[0] if queries else ''), (int(pages[0]) if pages else 1), filters


def search_url(query: str, page: int, filters: list[tuple[str, str]]) -> str:
    """
    Builds a local link while retaining selected filters and the search term.

    Called by: search_data(), facet_data()
    """
    params = [('q', query)] if query else []
    params.extend(('fq', field + '|' + value) for field, value in filters)
    if page != 1:
        params.append(('page', str(page)))
    return reverse('search').rstrip('/') + ('?' + urlencode(params) if params else '')


def search_facet_url(query: str, filters: list[tuple[str, str]], field: str) -> str:
    """
    Builds the local URL that retrieves every value of one search facet.

    Called by: facet_data()
    """
    params = [('q', query)] if query else []
    params.extend(('fq', name + '|' + value) for name, value in filters)
    params.append(('f_name', field))
    return reverse('search_facets').rstrip('/') + '?' + urlencode(params)


def facet_data(response: dict[str, object], query: str, filters: list[tuple[str, str]]) -> list[dict[str, object]]:
    """
    Converts Solr's alternating facet values and counts to local links.

    Called by: search_data()
    """
    counts = response.get('facet_counts')
    fields = counts.get('facet_fields') if isinstance(counts, dict) else None
    if not isinstance(fields, dict):
        raise PageDataError('Solr did not return search facets.')
    facets: list[dict[str, object]] = []
    for field, title in zip(FACETS, FACET_TITLES, strict=True):
        raw = fields.get(field)
        if not isinstance(raw, list) or len(raw) % 2:
            raise PageDataError('Solr returned an invalid facet list.')
        values: list[dict[str, object]] = []
        for index in range(0, len(raw), 2):
            label, count = raw[index : index + 2]
            if not isinstance(label, str) or type(count) is not int or count < 0:
                continue
            selected = (field, label) in filters
            next_filters = [item for item in filters if item != (field, label)] if selected else [*filters, (field, label)]
            values.append({'text': label, 'count': count, 'selected': selected, 'url': search_url(query, 1, next_filters)})
        if values:
            visible = values[:10] + [value for value in values[10:] if value['selected']]
            has_more = len(values) > 10
            facets.append(
                {
                    'name': field,
                    'title': title,
                    'values': visible,
                    'has_more': has_more,
                    'more_url': search_facet_url(query, filters, field) if has_more else '',
                    'more_values': [],
                }
            )
    return facets


def selected_highlights(fields: dict[str, object], limit: int = 5) -> list[tuple[str, str]]:
    """
    Chooses distinct search terms before filling the remaining match slots.

    Called by: match_html(), tests
    """
    hits = [
        (field, value.strip())
        for field, values in fields.items()
        if isinstance(values, list)
        for value in values
        if isinstance(value, str)
    ]
    terms = list(dict.fromkeys(term.upper() for _, value in hits for term in re.findall(r'<strong>.*?</strong>', value)))
    selected: list[tuple[str, str]] = []
    seen: set[str] = set()
    for term in terms:
        for hit in hits:
            if term in hit[1].upper() and hit[1] not in seen:
                selected.append(hit)
                seen.add(hit[1])
                break
        if len(selected) >= limit:
            break
    for hit in hits:
        if len(selected) >= limit:
            break
        if hit[1] not in seen:
            selected.append(hit)
            seen.add(hit[1])
    return selected


def safe_match_text(value: str) -> str:
    """
    Shows source markup as text while preserving Solr's bold match markers.

    Called by: match_html(), tests
    """
    cleaned = value.replace('Agent Faculty Member Organization or Person at Brown Person', '')
    result = escape(cleaned).replace('&#x27;', '&#39;')
    result = result.replace('&lt;strong&gt;', '<strong>').replace('&lt;/strong&gt;', '</strong>')
    return result.replace('&lt;', '&lsaquo;').replace('&gt;', '&rsaquo;')


def match_html(response: dict[str, object], doc: dict[str, object]) -> str:
    """
    Shows a small escaped preview when Solr highlights a result.

    Called by: search_data()
    """
    all_highlights = response.get('highlighting')
    identifier = first_text(doc.get('id'))
    fields = all_highlights.get('vitroIndividual:' + identifier) if isinstance(all_highlights, dict) else None
    if not isinstance(fields, dict):
        return ''
    selected = selected_highlights(fields)
    captions = (
        ('department_t', 'Department'),
        ('research_areas_en', 'Research areas'),
        ('affiliations_en', 'Affiliations'),
        ('overview_en', 'Overview'),
    )
    paragraphs: list[str] = []
    for field, caption in captions:
        values = [value for name, value in selected if name == field]
        if values:
            joined = ', '.join(values).replace('<p>', '').replace('</p>', '').replace('\u00a0', ' ')
            joined = re.sub(r'\s{2,}', ' ', joined)
            safe_value = safe_match_text(joined)
            paragraphs.append('<p>' + caption + ': ' + safe_value + '</p>')
    caption_fields = {field for field, _ in captions}
    for field, value in selected:
        if field not in caption_fields:
            safe_value = safe_match_text(value)
            paragraphs.append('<p>' + safe_value + '</p>')
    return ''.join(paragraphs)


def search_data(pairs: list[tuple[str, str]], mode: str, reader: SourceReader | None = None) -> dict[str, object]:
    """
    Supplies a rendered search state from the same parser in live and replay.

    Called by: page_data.get_search_data(), tools.source_capture.capture_journey(), tests
    """
    if reader is None:
        reader = read_source
    query, page, filters = search_inputs(pairs)
    response = response_object(search_key(query, page, filters), mode, reader)
    docs, total = documents(response)
    results: list[dict[str, object]] = []
    for doc in docs:
        kind = first_text(doc.get('record_type'))
        if kind not in {'PEOPLE', 'ORGANIZATION'}:
            continue
        try:
            item = record_data(doc)
            identifier = record_id(doc)
        except PageDataError:
            continue
        name = first_text(doc.get('display_name_s')) or first_text(item.get('name'))
        title = first_text(item.get('title'))
        if not name:
            continue
        result: dict[str, object] = {
            'id': identifier,
            'name': name,
            'schema_type': 'http://schema.org/Person' if kind == 'PEOPLE' else 'http://schema.org/Organization',
            'title': title[:47] + '...' if len(title) > 50 else title,
            'email': first_text(item.get('email')),
            'url': reverse('display_show_public', args=[identifier]),
            'thumbnail': thumbnail_url(doc, kind == 'ORGANIZATION'),
        }
        matches = match_html(response, doc)
        if matches:
            result['matches_html'] = matches
            result['matches_url'] = reverse('display_show_public', args=[identifier]) + '#All'
        results.append(result)
    page_count = math.ceil(total / 20)
    if page_count <= 10:
        first_page = 1
    elif page + 10 <= page_count:
        first_page = page
    else:
        first_page = page_count - 9
    pagination = [
        {'label': str(number), 'url': search_url(query, number, filters), 'current': number == page}
        for number in range(first_page, min(page_count, first_page + 9) + 1)
    ]
    selected_filters = [
        {
            'label': value,
            'category': FACET_TITLES[FACETS.index(field)],
            'value': value,
            'url': search_url(query, 1, [item for item in filters if item != (field, value)]),
        }
        for field, value in filters
    ]
    return {
        'query': '' if query == '*' else query,
        'page': page,
        'page_size': 20,
        'total': total,
        'start': (page - 1) * 20 + 1,
        'end': min(page * 20, total),
        'results': results,
        'facets': facet_data(response, query, filters),
        'pagination': pagination,
        'previous_url': search_url(query, page - 1, filters) if page > 1 else '',
        'next_url': search_url(query, page + 1, filters) if page * 20 < total else '',
        'remove_query_url': search_url('', 1, filters),
        'selected_filters': selected_filters,
        'form_filters': [
            {'name': f'fq_{index}', 'value': field + '|' + value} for index, (field, value) in enumerate(filters)
        ],
    }


def search_json_data(
    pairs: list[tuple[str, str]], mode: str, site_origin: str, reader: SourceReader | None = None
) -> list[dict[str, object]]:
    """
    Returns the public search JSON fields from the same Solr request as HTML search.

    Called by: views.search(), tests
    """
    if reader is None:
        reader = read_source
    query, page, filters = search_inputs(pairs)
    response = response_object(search_key(query, page, filters), mode, reader)
    docs, _ = documents(response)
    highlighting = response.get('highlighting')
    result: list[dict[str, object]] = []
    for doc in docs:
        kind = first_text(doc.get('record_type'))
        if kind not in {'PEOPLE', 'ORGANIZATION'}:
            continue
        try:
            item = record_data(doc)
            identifier = record_id(doc)
        except PageDataError:
            continue
        name = first_text(doc.get('display_name_s')) or first_text(item.get('name'))
        if not name:
            continue
        raw_highlights = (
            highlighting.get('vitroIndividual:' + first_text(doc.get('id'))) if isinstance(highlighting, dict) else None
        )
        hits: list[dict[str, object]] = []
        if isinstance(raw_highlights, dict):
            for field, values in raw_highlights.items():
                if isinstance(field, str) and isinstance(values, list) and all(isinstance(value, str) for value in values):
                    hits.append({'field': field, 'values': [value.strip() for value in values]})
        path = image_path(doc.get('thumbnail_file_path_s'))
        thumbnail = (
            source_origin('images') + path
            if path
            else ('person_placeholder.jpg' if kind == 'PEOPLE' else 'org_placeholder.png')
        )
        title = first_text(item.get('title'))
        result.append(
            {
                'id': first_text(doc.get('id')),
                'vivo_id': identifier,
                'uri': site_origin.rstrip('/') + '/display/' + identifier,
                'name': name,
                'thumbnail': thumbnail,
                'title': title[:47] + '...' if len(title) > 50 else title,
                'email': first_text(item.get('email')),
                'type': kind,
                'highlights': {'highlights': hits},
            }
        )
    return result


def facet_values_data(
    pairs: list[tuple[str, str]], mode: str, reader: SourceReader | None = None
) -> list[dict[str, object]]:
    """
    Returns every value of one search facet using a full Solr facet response.

    Called by: views.search_facets(), tools.source_capture.capture_journey(), tests
    """
    if reader is None:
        reader = read_source
    names = [value for key, value in pairs if key == 'f_name']
    if len(names) != 1 or names[0] not in FACETS:
        raise PageDataError('The requested search facet is unsupported.')
    query, page, filters = search_inputs([(key, value) for key, value in pairs if key != 'f_name'])
    response = response_object(search_key(query, page, filters, -1), mode, reader)
    fields = response.get('facet_counts')
    values = fields.get('facet_fields') if isinstance(fields, dict) else None
    raw = values.get(names[0]) if isinstance(values, dict) else None
    if not isinstance(raw, list) or len(raw) % 2:
        raise PageDataError('Solr returned an invalid facet list.')
    result: list[dict[str, object]] = []
    for index in range(0, len(raw), 2):
        label, count = raw[index : index + 2]
        if not isinstance(label, str) or type(count) is not int or count < 0:
            continue
        selected = (names[0], label) in filters
        remaining = [item for item in filters if item != (names[0], label)]
        result.append(
            {
                'text': label,
                'count': count,
                'remove_url': search_url(query, 1, remaining) if selected else None,
                'add_url': search_url(query, 1, [*filters, (names[0], label)]),
                'range_start': None,
                'range_end': None,
            }
        )
    return result


def entries(item: dict[str, object], name: str) -> list[dict[str, object]]:
    """
    Reads an optional array of structured source records.

    Called by: profile_data(), publications(), profile_sections()
    """
    raw = item.get(name, [])
    if not isinstance(raw, list):
        return []
    return [value for value in raw if isinstance(value, dict)]


def safe_url(value: object) -> str:
    """
    Keeps only absolute HTTP links from source records.

    Called by: publications(), profile_sections(), profile_data()
    """
    result = ''
    if isinstance(value, str):
        parsed = urlsplit(value)
        if parsed.scheme in {'http', 'https'} and parsed.netloc and not any(ord(char) < 32 for char in value):
            result = value
    return result


def website_icon(url: str) -> str:
    """
    Selects the same local website badge rules used by the Rails page.

    Called by: profile_sections()
    """
    icons = (
        ('brown.edu/', 'brown_shield_logo.gif'),
        ('academia.edu/', 'academia_logo.png'),
        ('facebook.com/', 'facebook_logo.png'),
        ('linkedin.com/', 'linkedin_logo.png'),
        ('researchgate.net/', 'researchgate_logo.png'),
        ('orcid.org/', 'orcid_logo.png'),
        ('scholar.google.com/', 'google_scholar_logo.png'),
        ('twitter.com/', 'twitter_logo.png'),
    )
    result = next((static('images/' + image) for needle, image in icons if needle in url), '')
    return result


def website_rank(value: object) -> int:
    """
    Reads the whole-number part of a website's saved rank as Rails does.

    Called by: profile_sections(), source_formats.organization_json_data()
    """
    text = str(value) if isinstance(value, (int, float, str)) else ''
    match = re.match(r'\s*[+-]?\d+', text)
    return int(match.group()) if match else 0


def publication_type(item: dict[str, object]) -> tuple[str, str]:
    """
    Turns the citation class into Rails-style filter labels and identifiers.

    Called by: publications()
    """
    prefix = 'http://vivo.brown.edu/ontology/citation#'
    raw = first_text(item.get('type'))
    if not raw.startswith(prefix) or re.fullmatch(r'[A-Za-z]+', raw.removeprefix(prefix)) is None:
        return '', 'Other'
    kind = raw.removeprefix(prefix)
    label = 'Other' if kind == 'Citation' else re.sub(r'(?<!^)(?=[A-Z])', ' ', kind)
    return '_' + label.lower().replace(' ', '_'), label


def publication_year(item: dict[str, object]) -> str:
    """
    Keeps the year range accepted by the public publication model.

    Called by: publication_html(), publication_book_html(), publication_book_section_html(), publication_citation(), publications()
    """
    value = item.get('date')
    text = str(value) if isinstance(value, (str, int)) and not isinstance(value, bool) else ''
    match = re.match(r'\s*[+-]?\d+', text)
    year = int(match.group()) if match else 0
    return str(year) if 1900 <= year <= 2200 else ''


def publication_book_html(item: dict[str, object]) -> str:
    """
    Formats a book title, publisher details, and year like the public page.

    Called by: publication_html()
    """
    title = first_text(item.get('title')).strip().strip('“”"')
    book = first_text(item.get('book')).strip()
    title_parts = [part for part in (title, book) if part]
    citation = '<i>' + escape(' '.join(title_parts)) + '</i>.' if title_parts else ''
    details = []
    editors = first_text(item.get('editors')).strip()
    if editors:
        details.append('edited by ' + escape(editors))
    for field in ('location_label', 'publisher_label'):
        value = first_text(item.get(field)).strip()
        if value:
            details.append(escape(value))
    year = publication_year(item)
    if year:
        details.append(year)
    if details:
        citation += (' ' if citation else '') + ', '.join(details) + '.'
    return citation


def publication_book_section_html(item: dict[str, object]) -> str:
    """
    Formats a book chapter with its parent book and publishing details.

    Called by: publication_html()
    """
    title = first_text(item.get('title')).strip().strip('“”"')
    book = first_text(item.get('book')).strip()
    heading = '"' + escape(title.rstrip('.')) + '."' if title else ''
    if book:
        heading += (' ' if heading else '') + '<i>' + escape(book) + '</i>'
    details = []
    editors = first_text(item.get('editors')).strip()
    if editors:
        details.append('edited by ' + escape(editors))
    for field in ('location_label', 'publisher_label'):
        value = first_text(item.get(field)).strip()
        if value:
            details.append(escape(value))
    year = publication_year(item)
    if year:
        details.append(year)
    pages = first_text(item.get('pages')).strip()
    if pages:
        details.append('pp. ' + escape(pages))
    return heading + (', ' if heading and details else '') + ', '.join(details) + ('.' if heading or details else '')


def publication_html(item: dict[str, object]) -> str:
    """
    Formats one citation with escaped text and vetted outgoing links.

    Called by: publications()
    """
    authors = first_text(item.get('authors')).strip().rstrip(',.')
    title = first_text(item.get('title')).strip().strip('“”"')
    venue = first_text(item.get('published_in')) or first_text(item.get('venue'))
    year = publication_year(item)
    parts = []
    title_text = '"' + escape(title.rstrip('.')) + '." ' if title else ''
    if venue:
        parts.append('<i>' + escape(venue) + '</i>')
    for field, prefix in (('volume', 'vol. '), ('issue', 'no. ')):
        value = first_text(item.get(field))
        if value:
            parts.append(prefix + escape(value))
    if year:
        parts.append(year)
    pages = first_text(item.get('pages'))
    if pages:
        parts.append('pp. ' + escape(pages))
    kind, _ = publication_type(item)
    if kind == '_book':
        citation_body = publication_book_html(item)
    elif kind == '_book_section':
        citation_body = publication_book_section_html(item)
    else:
        citation_body = title_text + ', '.join(parts) + '.'
    citation = ('<span class="listDateTime">' + escape(authors) + '. </span>' if authors else '') + citation_body
    doi = first_text(item.get('doi'))
    external = safe_url(item.get('url'))
    full_text = (
        external
        if external.startswith('https://repository.library.brown.edu/') or external == 'https://repository.library.brown.edu'
        else ('https://doi.org/' + quote(doi, safe='/') if doi else '')
    )
    pub_med_id = first_text(item.get('pub_med_id'))
    pub_med_url = (
        'https://www.ncbi.nlm.nih.gov/pubmed/?term=' + quote(pub_med_id, safe='')
        if re.fullmatch(r'[A-Za-z0-9_-]{1,80}', pub_med_id)
        else ''
    )
    links = []
    for label, url in (
        ('Full Text', full_text),
        ('PubMed', pub_med_url),
        ('More Info', external if not full_text and not pub_med_url else ''),
    ):
        if url:
            links.append(
                '<a class="pub-item-tag full-text-link" target="_blank" rel="noopener" href="'
                + escape(url, quote=True)
                + '">'
                + label
                + '</a>'
            )
    if links:
        citation += ' <div class="no-orphans">' + ' '.join(links) + '</div>'
    return citation


def publication_citation(item: dict[str, object]) -> str:
    """
    Formats the citation cell used by the public organization TSV download.

    Called by: organization_publications_data(), tests
    """
    title = first_text(item.get('title')).strip(' \t\r\n\v\f').removeprefix('“')
    text = ''
    if title:
        title = title.strip('"')
        text = '"' + title.rstrip('.') + '." '
    venue = first_text(item.get('published_in')) or first_text(item.get('venue'))
    fields = [('<i>' + venue + '</i>') if venue else '']
    for name, prefix in (('volume', 'vol. '), ('issue', 'no. ')):
        value = first_text(item.get(name))
        if value:
            fields.append(prefix + value)
    year = publication_year(item)
    if year:
        fields.append(year)
    pages = first_text(item.get('pages'))
    if pages:
        fields.append('pp. ' + pages)
    parts = [field for field in fields if field]
    text += (' ' if text and parts else '') + ', '.join(parts)
    return text.rstrip(' ,.') + '.'


def tsv_field(value: str) -> str:
    """
    Keeps source line breaks and tabs inside one download column.

    Called by: organization_publications_data()
    """
    return re.sub(r'[\t\r\n]+', ' ', value)


def ordered_publication_rows(item: dict[str, object]) -> list[dict[str, object]]:
    """
    Orders source publications by valid year and trimmed title.

    Called by: publications(), organization_publications_data()
    """
    raw = entries(item, 'contributor_to')
    raw.sort(
        key=lambda row: (
            -int(publication_year(row) or 0),
            first_text(row.get('title')).strip().lower(),
        )
    )
    return raw


def publications(item: dict[str, object]) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    """
    Sorts source publications and builds the matching type-filter counts.

    Called by: profile_data()
    """
    raw = ordered_publication_rows(item)
    result: list[dict[str, str]] = []
    labels: dict[str, str] = {}
    for row in raw:
        kind, label = publication_type(row)
        labels[kind] = label
        result.append({'type': kind, 'html': publication_html(row)})
    counts = Counter(publication['type'] for publication in result)
    filters = [{'id': kind, 'label': label, 'count': counts[kind]} for kind, label in labels.items()]
    return result, filters


def organization_thumbnail(uri: str, mode: str, reader: SourceReader) -> str:
    """
    Looks up an affiliation logo using the same Solr source as its profile.

    Called by: profile_sections()
    """
    identifier = uri.rsplit('/', 1)[-1]
    result = static('images/org_placeholder.png')
    try:
        response = response_object(profile_key(identifier), mode, reader)
        docs, _ = documents(response)
        if docs:
            if record_id(docs[0]) != identifier or first_text(docs[0].get('record_type')) != 'ORGANIZATION':
                raise PageDataError('Solr returned an unrelated affiliation logo.')
            result = thumbnail_url(docs[0], True)
    except PageDataError:
        if mode == 'replay':
            raise
    return result


def profile_date(value: object) -> date | None:
    """
    Reads an optional source date for profile rows.

    Called by: profile_year_range(), profile_sections()
    """
    text = first_text(value).split('T', 1)[0]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def profile_year_range(row: dict[str, object]) -> str:
    """
    Shows the available start and end years as Rails does.

    Called by: profile_sections()
    """
    years: list[str] = []
    for field in ('start_date', 'end_date'):
        value = profile_date(row.get(field))
        if value is None:
            years.append('')
        elif value.year > timezone.localdate().year:
            years.append('Present')
        else:
            years.append(str(value.year))
    return '-'.join(year for year in years if year)


def profile_entries_newest_first(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """
    Orders dated profile rows like Rails, including rows with equal dates.

    Called by: profile_sections()
    """
    ordered = sorted(rows, key=lambda row: profile_date(row.get('start_date')) or date(1900, 1, 1))
    ordered.reverse()
    return ordered


def profile_sections(
    item: dict[str, object], mode: str, reader: SourceReader, publication_count: int, collaborator_visualization_url: str
) -> list[dict[str, str]]:
    """
    Builds the visible profile sections from its source fields and lookups.

    Called by: profile_data()
    """
    sections: list[dict[str, str]] = []
    overview = '<h3>Overview</h3><p>' + render_profile_html(first_text(item.get('overview'))) + '</p>'
    affiliations = [
        row
        for row in entries(item, 'affiliations')
        if first_text(row.get('name'))
        and re.fullmatch(r'http://vivo\.brown\.edu/individual/[A-Za-z0-9_-]{1,80}', first_text(row.get('uri')))
    ]
    if affiliations:
        overview += (
            '<h4 class="brown-affiliations panel-heading">Brown Affiliations</h4><ul class="brown-affiliations-list">'
        )
        for affiliation in sorted(affiliations, key=lambda row: first_text(row.get('name')).lower()):
            uri = first_text(affiliation.get('uri'))
            name = first_text(affiliation.get('name'))
            identifier = uri.rsplit('/', 1)[-1]
            image = organization_thumbnail(uri, mode, reader)
            overview += (
                '<li><img src="'
                + escape(image, quote=True)
                + '" alt="'
                + escape(name, quote=True)
                + ' logo" width="36"> <a href="'
                + escape(reverse('display_show_public', args=[identifier]), quote=True)
                + '">'
                + escape(name)
                + '</a></li>'
            )
        overview += '</ul>'
    raw_areas = item.get('research_areas', [])
    areas = [area for area in raw_areas if isinstance(area, str) and area.strip()] if isinstance(raw_areas, list) else []
    if areas:
        overview += '<h4 class="research-areas panel-heading">Research Areas</h4><div class="brown-research-areas-list">'
        overview += ' &nbsp;|&nbsp; '.join(
            '<a href="'
            + escape(reverse('search').rstrip('/'), quote=True)
            + '?'
            + escape(urlencode({'fq': 'research_areas|' + str(area)}), quote=True)
            + '">'
            + escape(str(area))
            + '</a>'
            for area in sorted(areas, key=lambda value: str(value).casefold())
        )
        overview += '</div>'
    websites = [row for row in entries(item, 'on_the_web') if safe_url(first_text(row.get('url')).strip())]
    if websites:
        overview += '<h4 class="research-areas panel-heading">On the Web</h4><div id="on-the-web-list" class="brown-research-areas-list">'
        for website in sorted(websites, key=lambda row: website_rank(row.get('rank'))):
            raw_url = website.get('url')
            url = safe_url(raw_url.strip() if isinstance(raw_url, str) else raw_url)
            if url:
                label = first_text(website.get('text')).strip() or url
                icon = website_icon(url)
                badge = (
                    '<img src="' + escape(icon, quote=True) + '" width="17" alt="' + escape(label, quote=True) + '">'
                    if icon
                    else '<span class="glyphicon glyphicon-link" aria-hidden="true"></span>'
                )
                overview += (
                    '<li>'
                    + badge
                    + ' <a href="'
                    + escape(url, quote=True)
                    + '" target="_blank" rel="noopener">'
                    + escape(label)
                    + '</a></li>'
                )
        overview += '</div>'
    overview += '<br/><br/>'
    sections.append({'id': 'Overview', 'label': 'Overview', 'html': overview})
    if publication_count:
        sections.append({'id': 'Publications', 'label': 'Publications', 'html': ''})
    research_fields = (
        ('research_overview', 'Research Overview'),
        ('research_statement', 'Research Statement'),
        ('funded_research', 'Funded Research'),
        ('scholarly_work', 'Scholarly Work'),
    )
    research = ''.join(
        '<div class="panel-heading"><h4 class="panel-title">'
        + label
        + '</h4></div><div class="panel-body"><div class="property-list">'
        + render_profile_html(first_text(item.get(field)))
        + '</div></div>'
        for field, label in research_fields
        if first_text(item.get(field))
    )
    if research:
        sections.append({'id': 'Research', 'label': 'Research', 'html': '<h3>Research</h3>' + research})
    education = entries(item, 'education')
    background = '<h3>Background</h3>'
    if education:
        background += '<div class="panel-heading"><h4 class="panel-title">Education and Training</h4></div><div class="panel-body"><table class="table table-hover background__education"><tbody><tr><th>Year</th><th>Degree</th><th>Institution</th></tr>'
        ordered_education = sorted(education, key=lambda entry: first_text(entry.get('date')))
        ordered_education.reverse()
        for row in ordered_education:
            school = first_text(row.get('school_name')).strip()
            url = reverse('search').rstrip('/') + '?' + urlencode({'q': 'alumni_of:"' + school + '"'})
            background += (
                '<tr class="tableRow"><td>'
                + escape(first_text(row.get('date')))
                + '</td><td>'
                + escape(first_text(row.get('degree')))
                + '</td><td><a href="'
                + escape(url, quote=True)
                + '">'
                + escape(school)
                + '</a></td></tr>'
            )
        background += '</tbody></table></div>'
    training = entries(item, 'training')
    if training:
        background += (
            '<div class="panel-heading"><h4 class="panel-title">Postdoctoral/Other Training</h4></div>'
            '<div class="panel-body panel-body-postdoc"><table class="table table-hover"><tbody>'
        )
        for row in profile_entries_newest_first(training):
            organization = ', '.join(
                first_text(row.get(field)) for field in ('org_name', 'hospital_name', 'specialty_name') if row.get(field)
            )
            location = ', '.join(first_text(row.get(field)) for field in ('city', 'state', 'country') if row.get(field))
            background += (
                '<tr class="tableRow" role="listitem"><td>'
                + escape(first_text(row.get('name')))
                + '</td><td>'
                + escape(organization)
                + '</td><td>'
                + escape(profile_year_range(row))
                + '</td><td>'
                + escape(location)
                + '</td></tr>'
            )
        background += '</tbody></table></div>'
    awards = first_text(item.get('awards'))
    if awards:
        background += (
            '<div class="panel-heading"><h4 class="panel-title">Honors and Awards</h4></div>'
            '<div class="panel-body"><div class="property-list" role="list" displaylimit="5">'
            + render_profile_html(awards)
            + '</div></div>'
        )
    if education or awards or training:
        sections.append({'id': 'Background', 'label': 'Background', 'html': background})
    appointments = entries(item, 'appointments')
    collaborators = entries(item, 'collaborators')
    affiliation_text = first_text(item.get('affiliations_text'))
    affiliation_html = '<h3>Affiliations'
    if collaborator_visualization_url:
        affiliation_html += (
            '<a id="viz_collab" class="btn btn-default" style="float:right;" href="'
            + escape(collaborator_visualization_url, quote=True)
            + '" target="_blank" rel="noopener" title="Visualize collaborators network">Visualize it '
            '<i class="glyphicon glyphicon-signal" style="color:rgb(232, 217, 139);" aria-hidden="true"></i></a>'
        )
    affiliation_html += '</h3>'
    if collaborators:
        affiliation_html += (
            '<div class="panel-heading"><h4 id="relatedBy-Authorship" class="panel-title">Collaborators</h4></div>'
            '<div class="panel-body panel-body-collaborators"><table class="table table-hover"><tbody>'
            '<tr><th>Name</th><th>Title</th></tr>'
        )
        for collaborator in sorted(collaborators, key=lambda row: first_text(row.get('name')).casefold()):
            name = first_text(collaborator.get('name'))
            title = first_text(collaborator.get('title'))
            uri = first_text(collaborator.get('uri'))
            identifier = (
                uri.removeprefix('http://vivo.brown.edu/individual/')
                if uri.startswith('http://vivo.brown.edu/individual/')
                else ''
            )
            display_name = escape(name)
            if re.fullmatch(r'[A-Za-z0-9_-]{1,80}', identifier):
                display_name = (
                    '<a href="'
                    + escape(reverse('display_show_public', args=[identifier]), quote=True)
                    + '">'
                    + display_name
                    + '</a>'
                )
            affiliation_html += (
                '<tr class="tableRow" role="listitem"><td><span class="listDateTime">'
                + display_name
                + '</span></td><td><span class="listDateTime">'
                + escape(title)
                + '</span></td></tr>'
            )
        affiliation_html += '</tbody></table></div>'
    if affiliation_text:
        affiliation_html += (
            '<div class="panel-heading"><h4 class="panel-title">Affiliations</h4></div><div class="panel-body">'
            '<div class="property-list" role="list" displaylimit="5">'
            + render_profile_html(affiliation_text)
            + '</div></div>'
        )
    credentials = entries(item, 'credentials')
    if credentials:
        affiliation_html += (
            '<div class="panel-heading"><h4 class="panel-title">Credentials/Licenses</h4></div>'
            '<div class="panel-body panel-body-credentials"><table class="table table-hover"><tbody>'
        )
        for row in profile_entries_newest_first(credentials):
            grantor = ', '.join(
                value[:1].upper() + value[1:]
                for field in ('grantor_name', 'specialty_name')
                if (value := first_text(row.get(field)))
            )
            number = first_text(row.get('number'))
            affiliation_html += (
                '<tr class="tableRow" role="listitem"><td>'
                + escape(first_text(row.get('name')))
                + '</td><td>'
                + escape(grantor)
                + '</td><td>'
                + escape(profile_year_range(row))
                + '</td><td>'
                + escape('#' + number if number else '')
                + '</td></tr>'
            )
        affiliation_html += '</tbody></table></div>'
    if appointments:
        affiliation_html += '<div class="panel-heading"><h4 class="panel-title">Appointments</h4></div><div class="panel-body"><table class="table table-hover"><tbody>'
        for row in profile_entries_newest_first(appointments):
            name = first_text(row.get('name'))
            org = first_text(row.get('hospital_name')) or first_text(row.get('org_name'))
            department = first_text(row.get('department'))
            affiliation_html += '<tr class="tableRow" role="listitem"><td><span>' + escape(name) + '</span>.'
            if org:
                url = reverse('search').rstrip('/') + '?' + urlencode({'q': '"' + org + '"'})
                affiliation_html += ' <a href="' + escape(url, quote=True) + '">' + escape(org) + '</a>,'
            if department:
                affiliation_html += ' <span>' + escape(department) + '</span>'
            affiliation_html += ' <span>' + escape(profile_year_range(row)) + '</span></td></tr>'
        affiliation_html += '</tbody></table></div>'
    if appointments or affiliation_text or collaborators or credentials:
        sections.append({'id': 'Affiliations', 'label': 'Affiliations', 'html': affiliation_html})
    teaching = item.get('teacher_for', [])
    teaching = (
        [course for course in teaching if isinstance(course, str) and course.strip()] if isinstance(teaching, list) else []
    )
    teaching_overview = first_text(item.get('teaching_overview'))
    if teaching or teaching_overview:
        teaching_html = '<h3>Teaching</h3>'
        if teaching_overview:
            teaching_html += (
                '<div class="panel-heading"><h4 class="panel-title">Teaching Overview</h4></div><div class="panel-body">'
                '<div class="property-list" role="list" displaylimit="5">'
                + render_profile_html(teaching_overview)
                + '</div></div>'
            )
        if teaching:
            teaching_html += '<div class="panel-heading"><h4 class="panel-title">Teaching</h4></div><div class="panel-body"><table class="table table-hover"><tbody>'
            teaching_html += ''.join(
                '<tr class="tableRow"><td class="citation-data"><span class="listDateTime">'
                + escape(course)
                + '</span></td></tr>'
                for course in sorted(teaching, key=str.lower)
            )
            teaching_html += '</tbody></table></div>'
        sections.append({'id': 'Teaching', 'label': 'Teaching', 'html': teaching_html})
    return sections


def profile_data(identifier: str, mode: str, reader: SourceReader | None = None) -> dict[str, object]:
    """
    Supplies a person profile from one Solr record and required lookups.

    Called by: page_data.get_profile_data(), tools.source_capture.capture_journey(), tests
    """
    if reader is None:
        reader = read_source
    response = response_object(profile_key(identifier), mode, reader)
    docs, _ = documents(response)
    if not docs:
        raise MissingRecordError('The requested profile is absent from Solr.')
    doc = docs[0]
    if first_text(doc.get('record_type')) != 'PEOPLE' or record_id(doc) != identifier:
        raise PageDataError('The requested source record is not a person profile.')
    item = record_data(doc)
    name = first_text(doc.get('display_name_s')) or first_text(item.get('name'))
    if not name:
        raise PageDataError('The source profile has no display name.')
    publications_data, publication_filters = publications(item)
    coauthor_visualization_url = ''
    collaborator_visualization_url = ''
    if settings.VIZ_ENABLED and publications_data and first_text(doc.get('show_visualizations_s')) == 'true':
        from vivo_app.lib.source_graph import visualization_list

        try:
            available_coauthors = visualization_list('coauthors', mode, reader)
            if first_text(doc.get('id')) in available_coauthors:
                coauthor_visualization_url = reverse('visualization_coauthor', args=[identifier])
        except PageDataError:
            if mode == 'replay':
                raise
    if settings.VIZ_ENABLED and entries(item, 'collaborators') and first_text(doc.get('show_visualizations_s')) == 'true':
        from vivo_app.lib.source_graph import visualization_list

        try:
            available_collaborators = visualization_list('collaborators', mode, reader)
            if first_text(doc.get('id')) in available_collaborators:
                collaborator_visualization_url = reverse('visualization_collab', args=[identifier])
        except PageDataError:
            if mode == 'replay':
                raise
    cv_entries = entries(item, 'cv')
    cv_url = safe_url(cv_entries[0].get('cv_link')) if cv_entries else ''
    return {
        'id': identifier,
        'name': name,
        'page_title': first_text(item.get('name')) or name,
        'hidden': item.get('hidden') is True,
        'title': first_text(item.get('title')),
        'email': first_text(item.get('email')),
        'thumbnail': thumbnail_url(doc),
        'sections': profile_sections(item, mode, reader, len(publications_data), collaborator_visualization_url),
        'publications': publications_data,
        'publication_filters': publication_filters,
        'coauthor_visualization_url': coauthor_visualization_url,
        'cv_url': local_document_url(cv_url) if cv_url else '',
    }


def organization_members(
    item: dict[str, object], extra_member_ids: list[str], mode: str, reader: SourceReader
) -> list[dict[str, object]]:
    """
    Adds the configured faculty that Rails places on a custom organization page.

    Called by: organization_data(), organization_publications_data()
    """
    members = [
        member
        for member in entries(item, 'people')
        if re.fullmatch(r'http://vivo\.brown\.edu/individual/[A-Za-z0-9_-]{1,80}', first_text(member.get('faculty_uri')))
    ]
    known = {record_id({'id': first_text(member.get('faculty_uri'))}) for member in members}
    if extra_member_ids:
        response = response_object(team_member_key(extra_member_ids), mode, reader)
        docs, _ = documents(response)
        found: set[str] = set()
        for doc in docs:
            member_id = record_id(doc)
            if member_id not in extra_member_ids or first_text(doc.get('record_type')) != 'PEOPLE' or member_id in found:
                raise PageDataError('Solr returned an unrelated custom-organization member.')
            found.add(member_id)
            if member_id not in known:
                person = record_data(doc)
                members.append(
                    {
                        'faculty_uri': first_text(doc.get('id')),
                        'label': first_text(person.get('name')),
                        'specific_position': first_text(person.get('title')),
                        'general_position': 'general position',
                    }
                )
    return members


def organization_preview_graph() -> dict[str, object]:
    """
    Supplies the fixed decorative network shown beside organization visualizations.

    Called by: organization_data(), source_teams.team_data()
    """
    points = [
        (502.67, 350.69, 15, 'rgb(174, 199, 232)'),
        (402.73, 416.59, 15, 'rgb(174, 199, 232)'),
        (499.79, 237.86, 15, 'rgb(174, 199, 232)'),
        (565.55, 443.74, 11, 'rgb(255, 127, 14)'),
        (384.64, 335.43, 15, 'rgb(174, 199, 232)'),
        (597.28, 294.16, 11, 'rgb(31, 119, 180)'),
        (457.79, 418.67, 15, 'rgb(174, 199, 232)'),
        (429.55, 302.86, 15, 'rgb(174, 199, 232)'),
    ]
    edges = [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (6, 7)]
    lines = [
        {'x1': points[left][0], 'y1': points[left][1], 'x2': points[right][0], 'y2': points[right][1]}
        for left, right in edges
    ]
    nodes = [{'x': x, 'y': y, 'radius': radius, 'color': color} for x, y, radius, color in points]
    return {'view_box': '10 -30 960 700', 'lines': lines, 'nodes': nodes}


def organization_data(
    identifier: str, mode: str, reader: SourceReader | None = None, extra_member_ids: list[str] | None = None
) -> dict[str, object]:
    """
    Builds an organization and its member portraits from exact Solr responses.

    Called by: page_data.get_organization_data(), tools.source_capture.capture_journey(), tests
    """
    if reader is None:
        reader = read_source
    response = response_object(profile_key(identifier), mode, reader)
    docs, _ = documents(response)
    if not docs:
        raise MissingRecordError('The requested organization is absent from Solr.')
    doc = docs[0]
    if first_text(doc.get('record_type')) != 'ORGANIZATION' or record_id(doc) != identifier:
        raise PageDataError('The requested source record is not an organization.')
    item = record_data(doc)
    name = first_text(item.get('name')) or first_text(doc.get('display_name_s'))
    if not name:
        raise PageDataError('The source organization has no display name.')
    members = organization_members(item, extra_member_ids or [], mode, reader)
    member_ids: list[str] = []
    for member in members:
        uri = first_text(member.get('faculty_uri'))
        member_ids.append(record_id({'id': uri}))
    identifiers = sorted(set(member_ids))
    portraits: dict[str, str] = {}
    for start in range(0, len(identifiers), 100):
        batch = identifiers[start : start + 100]
        member_response = response_object(member_key(batch), mode, reader)
        member_docs, _ = documents(member_response)
        for member_doc in member_docs:
            member_id = record_id(member_doc)
            if member_id not in batch or first_text(member_doc.get('record_type')) != 'PEOPLE' or member_id in portraits:
                raise PageDataError('Solr returned an unrelated organization member.')
            portraits[member_id] = thumbnail_url(member_doc)
    administrative: list[dict[str, str]] = []
    faculty: list[dict[str, str]] = []
    for member, member_id in sorted(
        zip(members, member_ids, strict=True), key=lambda pair: first_text(pair[0].get('label')).lower()
    ):
        row = {
            'name': first_text(member.get('label')),
            'title': first_text(member.get('specific_position')),
            'url': reverse('display_show_public', args=[member_id]),
            'image': portraits.get(member_id, static('images/person_placeholder.jpg')),
        }
        if first_text(member.get('general_position')) == 'http://vivoweb.org/ontology/core#FacultyAdministrativePosition':
            administrative.append(row)
        else:
            faculty.append(row)
    websites: list[dict[str, str]] = []
    for website in sorted(entries(item, 'web_pages'), key=lambda row: website_rank(row.get('rank'))):
        raw_url = website.get('url')
        url = safe_url(raw_url.strip() if isinstance(raw_url, str) else raw_url)
        if url:
            websites.append({'url': url, 'label': first_text(website.get('text')).strip() or url})
    overview = first_text(item.get('overview'))
    return {
        'id': identifier,
        'name': name,
        'page_title': name,
        'image': (
            thumbnail_url(doc, True)
            if image_path(doc.get('thumbnail_file_path_s'))
            else static('images/org_placeholder_noborder.png')
        ),
        'website_links': websites,
        'overview_html': '<p>' + render_profile_html(overview) + '</p>' if overview else '',
        'visualization_url': reverse('visualization_collab', args=[identifier]) if settings.VIZ_ENABLED and members else '',
        'visualization_graph': organization_preview_graph() if settings.VIZ_ENABLED and members else {},
        'administrative_positions': administrative,
        'faculty_positions': faculty,
    }


def organization_publications_data(
    identifier: str, mode: str, reader: SourceReader | None = None, extra_member_ids: list[str] | None = None
) -> str:
    """
    Builds the public TSV download from an organization's Solr member records.

    Called by: views.organization_publications_tsv(), tests
    """
    if reader is None:
        reader = read_source
    response = response_object(profile_key(identifier), mode, reader)
    docs, _ = documents(response)
    if not docs or first_text(docs[0].get('record_type')) != 'ORGANIZATION' or record_id(docs[0]) != identifier:
        raise PageDataError('The requested source record is not an organization.')
    organization = record_data(docs[0])
    members = organization_members(organization, extra_member_ids or [], mode, reader)
    member_ids = list(dict.fromkeys(record_id({'id': first_text(member.get('faculty_uri'))}) for member in members))
    member_docs: list[dict[str, object]] = []
    for start in range(0, len(member_ids), 20):
        batch = member_ids[start : start + 20]
        member_response = response_object(member_details_key(batch), mode, reader)
        docs, _ = documents(member_response)
        found = {record_id(doc) for doc in docs}
        if not found.issubset(batch) or len(docs) != len(found):
            raise PageDataError('Solr returned an unrelated organization member.')
        member_docs.extend(docs)
    lines = ['Id\tFaculty\tTitle\tAuthors\tYear\tType\tCitation\n']
    for doc in member_docs:
        if first_text(doc.get('record_type')) != 'PEOPLE':
            raise PageDataError('Solr returned an unrelated organization member.')
        person = record_data(doc)
        publications_data = ordered_publication_rows(person)
        for publication in publications_data:
            _, kind = publication_type(publication)
            fields = (
                first_text(doc.get('id')),
                first_text(person.get('name')),
                first_text(publication.get('title')),
                first_text(publication.get('authors')),
                publication_year(publication),
                kind,
                publication_citation(publication),
            )
            lines.append('\t'.join(tsv_field(field) for field in fields) + '\n')
    return ''.join(lines)
