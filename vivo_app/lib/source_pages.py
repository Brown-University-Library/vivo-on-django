"""
Turns recorded or live Solr documents into the existing page templates' data.
"""

import json
import math
import re
from collections import Counter
from collections.abc import Callable
from html import escape
from urllib.parse import quote, urlencode, urlsplit

from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import strip_tags

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RequestKey
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
    fallback = 'images/org_placeholder.png' if organization else 'images/vivo_blank_profile.jpg'
    result = reverse('source_image', kwargs={'filename': path.lstrip('/')}) if path else static(fallback)
    return result


def search_inputs(pairs: list[tuple[str, str]]) -> tuple[str, int, list[tuple[str, str]]]:
    """
    Accepts the first journey's query, page, and repeated facet filters.

    Called by: search_data()
    """
    if any(key not in {'q', 'page', 'fq'} for key, _ in pairs):
        raise PageDataError('This live search option has not been implemented.')
    queries = [value for key, value in pairs if key == 'q']
    pages = [value for key, value in pairs if key == 'page']
    if len(queries) > 1 or len(pages) > 1 or (pages and re.fullmatch(r'[1-9][0-9]{0,2}', pages[0]) is None):
        raise PageDataError('The requested search query or page is invalid.')
    filters: list[tuple[str, str]] = []
    for key, value in pairs:
        if key == 'fq':
            field, separator, text = value.partition('|')
            if not separator or field not in FACETS or not text:
                raise PageDataError('The requested search filter is unsupported.')
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
                raise PageDataError('Solr returned an invalid facet value.')
            selected = (field, label) in filters
            next_filters = [item for item in filters if item != (field, label)] if selected else [*filters, (field, label)]
            values.append({'text': label, 'count': count, 'selected': selected, 'url': search_url(query, 1, next_filters)})
        if values:
            facets.append({'name': field, 'title': title, 'values': values, 'more_values': []})
    return facets


def match_html(response: dict[str, object], doc: dict[str, object]) -> str:
    """
    Shows a small escaped preview when Solr highlights a result.

    Called by: search_data()
    """
    all_highlights = response.get('highlighting')
    identifier = first_text(doc.get('id'))
    fields = all_highlights.get('vitroIndividual:' + identifier) if isinstance(all_highlights, dict) else None
    snippets: list[str] = []
    if isinstance(fields, dict):
        for field in (
            'department_t',
            'research_areas_en',
            'affiliations_en',
            'overview_en',
            'ALLTEXT',
            'email_s',
            'short_id_s',
        ):
            values = fields.get(field)
            if isinstance(values, list):
                snippets.extend(value for value in values if isinstance(value, str))
    if not snippets:
        return ''
    selected = snippets[:5]
    safe = [
        escape(value).replace('&lt;strong&gt;', '<strong>').replace('&lt;/strong&gt;', '</strong>') for value in selected
    ]
    return ''.join('<p>' + value + '</p>' for value in safe)


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
            raise PageDataError('Solr returned an unsupported record type.')
        item = record_data(doc)
        identifier = record_id(doc)
        name = first_text(doc.get('display_name_s')) or first_text(item.get('name'))
        title = first_text(item.get('title'))
        if not name:
            raise PageDataError('A Solr result is missing its display name.')
        result: dict[str, object] = {
            'id': identifier,
            'name': name,
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
        'start': (page - 1) * 20 + 1 if total else 0,
        'end': min(page * 20, total),
        'results': results,
        'facets': facet_data(response, query, filters),
        'pagination': pagination,
        'previous_url': search_url(query, page - 1, filters) if page > 1 else '',
        'next_url': search_url(query, page + 1, filters) if page * 20 < total else '',
        'remove_query_url': search_url('', 1, filters),
        'selected_filters': selected_filters,
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
            raise PageDataError('Solr returned an unsupported record type.')
        item = record_data(doc)
        identifier = record_id(doc)
        name = first_text(doc.get('display_name_s')) or first_text(item.get('name'))
        if not name:
            raise PageDataError('A Solr result is missing its display name.')
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
            raise PageDataError('Solr returned an invalid facet value.')
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
    if not isinstance(raw, list) or any(not isinstance(value, dict) for value in raw):
        raise PageDataError(f'A Solr profile contains invalid {name} data.')
    return list(raw)


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


def publication_type(item: dict[str, object]) -> tuple[str, str]:
    """
    Turns the citation class into Rails-style filter labels and identifiers.

    Called by: publications()
    """
    raw = first_text(item.get('type')).rsplit('#', 1)[-1]
    if not re.fullmatch(r'[A-Za-z]+', raw):
        raise PageDataError('A publication has an unsupported type.')
    label = 'Other' if raw == 'Citation' else re.sub(r'(?<!^)(?=[A-Z])', ' ', raw)
    return '_' + label.lower().replace(' ', '_'), label


def publication_html(item: dict[str, object]) -> str:
    """
    Formats one citation with escaped text and vetted outgoing links.

    Called by: publications()
    """
    authors = first_text(item.get('authors')).strip().rstrip(',.')
    title = first_text(item.get('title')).strip().strip('“”"')
    venue = first_text(item.get('published_in')) or first_text(item.get('venue'))
    year = first_text(item.get('date'))[:4]
    parts = []
    title_text = '"' + escape(title.rstrip('.')) + '." ' if title else ''
    if venue:
        parts.append('<i>' + escape(venue) + '</i>')
    for field, prefix in (('volume', 'vol. '), ('issue', 'no. ')):
        value = first_text(item.get(field))
        if value:
            parts.append(prefix + escape(value))
    if re.fullmatch(r'\d{4}', year):
        parts.append(year)
    pages = first_text(item.get('pages'))
    if pages:
        parts.append('pp. ' + escape(pages))
    citation = (
        ('<span class="listDateTime">' + escape(authors) + '. </span>' if authors else '')
        + title_text
        + ', '.join(parts)
        + '.'
    )
    doi = first_text(item.get('doi'))
    external = safe_url(item.get('url'))
    full_text = (
        external
        if external.startswith('https://repository.library.brown.edu/')
        else ('https://doi.org/' + quote(doi, safe='/') if doi else '')
    )
    if full_text:
        citation += (
            ' <div class="no-orphans"><a class="pub-item-tag full-text-link" target="_blank" rel="noopener" href="'
            + escape(full_text, quote=True)
            + '">Full Text</a></div>'
        )
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
    year = first_text(item.get('date'))[:4]
    if re.fullmatch(r'\d{4}', year):
        fields.append(year)
    pages = first_text(item.get('pages'))
    if pages:
        fields.append('pp. ' + pages)
    parts = [field for field in fields if field]
    text += (' ' if text and parts else '') + ', '.join(parts)
    return text.rstrip(' ,.') + '.'


def publications(item: dict[str, object]) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    """
    Sorts source publications and builds the matching type-filter counts.

    Called by: profile_data()
    """
    raw = entries(item, 'contributor_to')
    raw.sort(
        key=lambda row: (
            -int(first_text(row.get('date'))[:4]) if first_text(row.get('date'))[:4].isdigit() else 0,
            first_text(row.get('title')).lower(),
        )
    )
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
    response = response_object(profile_key(identifier), mode, reader)
    docs, _ = documents(response)
    result = thumbnail_url(docs[0], True) if docs else static('images/brown_logo_small.png')
    return result


def profile_sections(
    item: dict[str, object], mode: str, reader: SourceReader, publication_count: int
) -> list[dict[str, str]]:
    """
    Builds the visible profile sections from its source fields and lookups.

    Called by: profile_data()
    """
    sections: list[dict[str, str]] = []
    overview = '<h3>Overview</h3><p>' + escape(strip_tags(first_text(item.get('overview')))) + '</p>'
    affiliations = entries(item, 'affiliations')
    if affiliations:
        overview += (
            '<h4 class="brown-affiliations panel-heading">Brown Affiliations</h4><ul class="brown-affiliations-list">'
        )
        for affiliation in sorted(affiliations, key=lambda row: first_text(row.get('name')).lower()):
            uri = first_text(affiliation.get('uri'))
            name = first_text(affiliation.get('name'))
            if uri.startswith('http://vivo.brown.edu/individual/') and name:
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
    areas = item.get('research_areas', [])
    if isinstance(areas, list) and areas:
        overview += '<h4 class="research-areas panel-heading">Research Areas</h4><div class="brown-research-areas-list">'
        overview += ' &nbsp;|&nbsp; '.join(
            '<a href="'
            + escape(reverse('search').rstrip('/'), quote=True)
            + '?'
            + escape(urlencode({'fq': 'research_areas|' + str(area)}), quote=True)
            + '">'
            + escape(str(area))
            + '</a>'
            for area in areas
        )
        overview += '</div>'
    websites = entries(item, 'on_the_web')
    if websites:
        overview += '<h4 class="research-areas panel-heading">On the Web</h4><div id="on-the-web-list" class="brown-research-areas-list">'
        for website in websites:
            url = safe_url(website.get('url'))
            if url:
                icon = website_icon(url)
                badge = (
                    '<img src="'
                    + escape(icon, quote=True)
                    + '" width="17" alt="'
                    + escape(first_text(website.get('text')) or 'Website', quote=True)
                    + '">'
                    if icon
                    else '<span class="glyphicon glyphicon-link" aria-hidden="true"></span>'
                )
                overview += (
                    '<li>'
                    + badge
                    + ' <a href="'
                    + escape(url, quote=True)
                    + '" target="_blank" rel="noopener">'
                    + escape(first_text(website.get('text')) or 'Website')
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
        + escape(strip_tags(first_text(item.get(field))))
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
        for row in sorted(education, key=lambda entry: first_text(entry.get('date')), reverse=True):
            school = first_text(row.get('school_name'))
            url = '/search?' + urlencode({'q': 'alumni_of:"' + school + '"'})
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
    awards = first_text(item.get('awards'))
    if awards:
        background += (
            '<div class="panel-heading"><h4 class="panel-title">Honors and Awards</h4></div><div class="panel-body">'
            + escape(strip_tags(awards))
            + '</div>'
        )
    if education or awards or entries(item, 'training'):
        sections.append({'id': 'Background', 'label': 'Background', 'html': background})
    appointments = entries(item, 'appointments')
    affiliation_text = first_text(item.get('affiliations_text'))
    affiliation_html = '<h3>Affiliations</h3>'
    if affiliation_text:
        affiliation_html += (
            '<div class="panel-heading"><h4 class="panel-title">Affiliations</h4></div><div class="panel-body">'
            + escape(strip_tags(affiliation_text))
            + '</div>'
        )
    if appointments:
        affiliation_html += '<div class="panel-heading"><h4 class="panel-title">Appointments</h4></div><div class="panel-body"><table class="table table-hover"><tbody>'
        for row in appointments:
            name = first_text(row.get('name'))
            org = first_text(row.get('org_name'))
            start = first_text(row.get('start_date'))[:4]
            end = first_text(row.get('end_date'))[:4]
            url = reverse('search').rstrip('/') + '?' + urlencode({'q': '"' + org + '"'})
            affiliation_html += (
                '<tr class="tableRow"><td><span>'
                + escape(name)
                + '</span>. <a href="'
                + escape(url, quote=True)
                + '">'
                + escape(org)
                + '</a>, '
                + escape(start + ('-' + end if end else ''))
                + '</td></tr>'
            )
        affiliation_html += '</tbody></table></div>'
    if appointments or affiliation_text or entries(item, 'collaborators') or entries(item, 'credentials'):
        sections.append({'id': 'Affiliations', 'label': 'Affiliations', 'html': affiliation_html})
    teaching = item.get('teacher_for', [])
    if not isinstance(teaching, list) or any(not isinstance(course, str) for course in teaching):
        raise PageDataError('A Solr profile contains invalid teaching data.')
    teaching_overview = first_text(item.get('teaching_overview'))
    if teaching or teaching_overview:
        teaching_html = '<h3>Teaching</h3>'
        if teaching_overview:
            teaching_html += (
                '<div class="panel-heading"><h4 class="panel-title">Teaching Overview</h4></div><div class="panel-body">'
                + escape(strip_tags(teaching_overview))
                + '</div>'
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
        raise PageDataError('The requested profile is absent from Solr.')
    doc = docs[0]
    if first_text(doc.get('record_type')) != 'PEOPLE' or record_id(doc) != identifier:
        raise PageDataError('The requested source record is not a person profile.')
    item = record_data(doc)
    name = first_text(doc.get('display_name_s')) or first_text(item.get('name'))
    if not name:
        raise PageDataError('The source profile has no display name.')
    publications_data, publication_filters = publications(item)
    cv_entries = entries(item, 'cv')
    cv_url = safe_url(cv_entries[0].get('cv_link')) if cv_entries else ''
    return {
        'id': identifier,
        'name': name,
        'page_title': first_text(item.get('name')) or name,
        'title': first_text(item.get('title')),
        'email': first_text(item.get('email')),
        'thumbnail': thumbnail_url(doc),
        'sections': profile_sections(item, mode, reader, len(publications_data)),
        'publications': publications_data,
        'publication_filters': publication_filters,
        'cv_url': local_document_url(cv_url) if cv_url else '',
    }


def organization_members(
    item: dict[str, object], extra_member_ids: list[str], mode: str, reader: SourceReader
) -> list[dict[str, object]]:
    """
    Adds the configured faculty that Rails places on a custom organization page.

    Called by: organization_data(), organization_publications_data()
    """
    members = entries(item, 'people')
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
        raise PageDataError('The requested organization is absent from Solr.')
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
    if identifiers:
        member_response = response_object(member_key(identifiers), mode, reader)
        member_docs, _ = documents(member_response)
        for member_doc in member_docs:
            member_id = record_id(member_doc)
            if member_id not in identifiers or first_text(member_doc.get('record_type')) != 'PEOPLE':
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
            'image': portraits.get(member_id, static('images/vivo_blank_profile.jpg')),
        }
        if first_text(member.get('general_position')).endswith('#FacultyAdministrativePosition'):
            administrative.append(row)
        else:
            faculty.append(row)
    websites: list[dict[str, str]] = []
    for website in entries(item, 'web_pages'):
        url = safe_url(website.get('url'))
        if url:
            websites.append({'url': url, 'label': first_text(website.get('text')) or url})
    overview = first_text(item.get('overview'))
    return {
        'id': identifier,
        'name': name,
        'page_title': name,
        'image': thumbnail_url(doc, True),
        'website_links': websites,
        'overview_html': '<p>' + escape(strip_tags(overview)) + '</p>' if overview else '',
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
    if member_ids:
        member_response = response_object(member_details_key(member_ids), mode, reader)
        member_docs, _ = documents(member_response)
        found = {record_id(doc) for doc in member_docs}
        if found != set(member_ids) or len(member_docs) != len(member_ids):
            raise PageDataError('Solr did not return every organization member.')
    lines = ['Id\tFaculty\tTitle\tAuthors\tYear\tType\tCitation\n']
    for doc in member_docs:
        if first_text(doc.get('record_type')) != 'PEOPLE':
            raise PageDataError('Solr returned an unrelated organization member.')
        person = record_data(doc)
        publications_data = entries(person, 'contributor_to')
        publications_data.sort(
            key=lambda row: (
                -int(first_text(row.get('date'))[:4]) if first_text(row.get('date'))[:4].isdigit() else 0,
                first_text(row.get('title')).lower(),
            )
        )
        for publication in publications_data:
            _, kind = publication_type(publication)
            fields = (
                first_text(doc.get('id')),
                first_text(person.get('name')),
                first_text(publication.get('title')),
                first_text(publication.get('authors')),
                first_text(publication.get('date'))[:4],
                kind,
                publication_citation(publication),
            )
            lines.append('\t'.join(fields) + '\n')
    return ''.join(lines)
