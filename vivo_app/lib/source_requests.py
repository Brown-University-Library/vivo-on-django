"""
Builds and reads the upstream requests for a search-to-profile journey.
"""

import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit

import httpx2
from django.conf import settings
from django.urls import reverse

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RecordingError, RequestKey, load_recordings

SEARCH_FIELDS = (
    'short_id_s^2500 email_s^2500 nameText^2000 title_t^1600 department_t^1500 '
    'research_areas_en^400 affiliations_en^450 nameUnstemmed^4 nameStemmed^4 '
    'nameLowercase ALLTEXT^2 ALLTEXTUNSTEMMED^2'
)
FACETS = ('record_type', 'affiliations', 'research_areas', 'published_in')
FACET_TITLES = ('Type', 'Brown Affiliations', 'Research Areas', 'Published In')
COMMUNITY_RESEARCH_AREAS = (
    'community engagement',
    'engaged scholarship',
    'engaged teaching',
    'engaged research',
    'community-based participatory research',
    'community-based learning and research',
    'public service',
    'civic engagement',
    'service learning',
    'public scholarship',
    'publicly engaged scholarship',
    'scholarship of engagement',
    'community-based scholarship',
    'broader impact',
    'community-based',
)
MAX_RESPONSE_BYTES = 3_000_000
MAX_DOCUMENT_BYTES = 10_000_000


def quoted(value: str) -> str:
    """
    Quotes a value for a Solr field query after rejecting control characters.

    Called by: search_key(), profile_key(), member_key()
    """
    if any(ord(character) < 32 for character in value):
        raise PageDataError('Search and filter values cannot contain control characters.')
    result = '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return result


def search_key(query: str, page: int, filters: list[tuple[str, str]], facet_limit: int = 11) -> RequestKey:
    """
    Builds one bounded Solr search with the same main fields and ranking as Rails.

    Called by: source_pages.search_data(), source_pages.facet_values_data(), tests
    """
    if page < 1 or page > 1000 or len(query) > 300 or len(filters) > 12 or facet_limit not in {11, -1}:
        raise PageDataError('The requested search is outside the supported limits.')
    pairs = [
        ('q', query or '*'),
        ('defType', 'edismax'),
        ('qf', SEARCH_FIELDS),
        ('mm', '2<75%'),
        ('fq', 'record_type:(PEOPLE OR ORGANIZATION)'),
        ('fl', 'id,record_type,thumbnail_file_path_s,json_txt,display_name_s'),
        ('rows', '20'),
        ('start', str((page - 1) * 20)),
        ('facet', 'true'),
        ('facet.mincount', '1'),
        ('facet.limit', str(facet_limit)),
        ('hl', 'true'),
        ('hl.fl', 'department_t research_areas_en affiliations_en overview_en ALLTEXT email_s short_id_s'),
        ('hl.snippets', '30'),
        ('hl.simple.pre', '<strong>'),
        ('hl.simple.post', '</strong>'),
        ('wt', 'json'),
    ]
    if not query or query == '*':
        pairs.append(('sort', 'profile_updated_s desc'))
    for field, value in filters:
        if field not in FACETS or not value or len(value) > 200:
            raise PageDataError('The requested search filter is unsupported.')
        pairs.append(('fq', f'{field}:{quoted(value)}'))
    pairs.extend(('facet.field', field) for field in FACETS)
    return RequestKey('solr', '/select', tuple(pairs))


def profile_key(identifier: str) -> RequestKey:
    """
    Looks up one canonical person or organization by its public identifier.

    Called by: source_pages.profile_data(), source_pages.organization_data(), source_pages.organization_thumbnail(), tests
    """
    if re.fullmatch(r'[A-Za-z0-9_-]{1,80}', identifier) is None:
        raise PageDataError('The requested profile identifier is unsupported.')
    query = f'id:{quoted("http://vivo.brown.edu/individual/" + identifier)}'
    return RequestKey(
        'solr',
        '/select',
        (
            ('q', query),
            ('fl', 'id,record_type,thumbnail_file_path_s,json_txt,display_name_s,show_visualizations_s'),
            ('rows', '1'),
            ('wt', 'json'),
        ),
    )


def profile_export_key(identifier: str) -> RequestKey:
    """
    Looks up the additional Solr fields used by the public profile JSON response.

    Called by: source_pages.profile_json_data(), tests
    """
    base = profile_key(identifier)
    return RequestKey(
        'solr',
        base.path,
        tuple(
            (
                key,
                'id,record_type,thumbnail_file_path_s,json_txt,display_name_s,fis_updated_s,profile_updated_s,show_visualizations_s',
            )
            if key == 'fl'
            else (key, value)
            for key, value in base.query
        ),
    )


def member_key(identifiers: list[str]) -> RequestKey:
    """
    Looks up the portrait fields for an organization's distinct members in one Solr request.

    Called by: source_pages.organization_data(), tests
    """
    if not identifiers or len(identifiers) > 100 or len(set(identifiers)) != len(identifiers):
        raise PageDataError('The organization member list is outside the supported limits.')
    if any(re.fullmatch(r'[A-Za-z0-9_-]{1,80}', identifier) is None for identifier in identifiers):
        raise PageDataError('An organization member identifier is unsupported.')
    names = ['http://vivo.brown.edu/individual/' + identifier for identifier in identifiers]
    query = 'id:(' + ' OR '.join(quoted(name) for name in names) + ')'
    return RequestKey(
        'solr',
        '/select',
        (('q', query), ('fl', 'id,record_type,thumbnail_file_path_s'), ('rows', str(len(names))), ('wt', 'json')),
    )


def member_details_key(identifiers: list[str]) -> RequestKey:
    """
    Requests member records needed to produce an organization publication download.

    Called by: source_pages.organization_publications_data(), tests
    """
    portrait_key = member_key(identifiers)
    query = portrait_key.query[0][1]
    return RequestKey(
        'solr', '/select', (('q', query), ('fl', 'id,record_type,json_txt'), ('rows', str(len(identifiers))), ('wt', 'json'))
    )


def graph_root_key(identifiers: list[str]) -> RequestKey:
    """
    Requests complete root records for the faculty objects in calculated graph JSON.

    Called by: source_graph.custom_graph_records(), tests
    """
    base = member_details_key(identifiers)
    return RequestKey('solr', base.path, tuple((key, '*') if key == 'fl' else (key, value) for key, value in base.query))


def chart_member_key(identifiers: list[str]) -> RequestKey:
    """
    Adds public display names to the member records used by organization charts.

    Called by: source_org_charts.organization_chart_members(), tests
    """
    base = member_details_key(identifiers)
    query = tuple(
        (key, 'id,record_type,json_txt,display_name_s') if key == 'fl' else (key, value) for key, value in base.query
    )
    return RequestKey('solr', base.path, query)


def status_key() -> RequestKey:
    """
    Counts the person and organization records that the public search can show.

    Called by: source_status.status_data(), tests
    """
    return RequestKey(
        'solr',
        '/select',
        (('q', '*:*'), ('fq', 'record_type:(PEOPLE OR ORGANIZATION)'), ('rows', '0'), ('wt', 'json')),
    )


def vitro_key(identifier: str, fmt: str) -> RequestKey:
    """
    Names one original VIVO representation and its Rails request header.

    Called by: views.individual_export(), tests
    """
    formats = {'jsonld': 'application/json', 'ttl': 'text/turtle', 'rdf': 'application/rdf+xml'}
    content_type = formats.get(fmt)
    if re.fullmatch(r'[A-Za-z0-9_-]{1,80}', identifier) is None or content_type is None:
        raise PageDataError('The requested VIVO representation is unsupported.')
    return RequestKey('vitro', f'/individual/{identifier}/{identifier}.{fmt}', headers=(('Content-Type', content_type),))


def team_member_key(identifiers: list[str]) -> RequestKey:
    """
    Requests display names and portraits for a code-defined active team.

    Called by: source_teams.team_data(), tests
    """
    base = member_details_key(identifiers)
    return RequestKey(
        'solr',
        base.path,
        tuple(
            (key, 'id,record_type,json_txt,display_name_s,thumbnail_file_path_s') if key == 'fl' else (key, value)
            for key, value in base.query
        ),
    )


def community_research_members_key() -> RequestKey:
    """
    Requests the people selected by the public community-engagement directory.

    Called by: source_teams.custom_organization_members(), tests
    """
    values = ' OR '.join(quoted(area) for area in COMMUNITY_RESEARCH_AREAS)
    return RequestKey(
        'solr',
        '/select',
        (
            ('q', '*'),
            ('fq', 'record_type:PEOPLE'),
            ('fq', f'research_areas:({values})'),
            ('fl', 'id,record_type'),
            ('rows', '500'),
            ('wt', 'json'),
        ),
    )


def image_path(file_path: object) -> str | None:
    """
    Converts a VIVO thumbnail path to its public image-service path.

    Called by: source_pages.thumbnail_url(), tools.source_capture.image_requests()
    """
    result = None
    if isinstance(file_path, str):
        parts = file_path.split('/')
        if len(parts) == 4 and parts[0] == '' and parts[1] == 'file':
            identifier, filename = parts[2], parts[3].replace('+', '^20')
            if (
                len(identifier) in {3, 4, 5, 6, 7, 8, 9, 33}
                and re.fullmatch(r'n[A-Za-z0-9]{2,32}', identifier)
                and re.fullmatch(r'[A-Za-z0-9._^-]+', filename)
            ):
                chunks = [identifier[index : index + 3] for index in range(1, len(identifier), 3)]
                result = '/profile-images/' + '/'.join(chunks) + '/' + filename
    return result


def image_key(path: str) -> RequestKey:
    """
    Restricts an image request to the profile-image path derived from Solr.

    Called by: views.source_image(), tools.source_capture.image_requests()
    """
    if re.fullmatch(r'/profile-images/(?:[A-Za-z0-9]{1,3}/)+[A-Za-z0-9._^-]+', path) is None:
        raise PageDataError('The requested source image path is unsupported.')
    return RequestKey('images', path)


def document_key(path: str, query: tuple[tuple[str, str], ...] = ()) -> RequestKey:
    """
    Restricts a CV request to a public PDF path and its optional version value.

    Called by: document_key_from_url(), views.source_document(), tests
    """
    if re.fullmatch(r'/docs/[A-Za-z0-9_-]{1,3}/[A-Za-z0-9._-]+\.pdf', path) is None:
        raise PageDataError('The requested source document path is unsupported.')
    if len(query) > 1 or any(key != 'dt' or re.fullmatch(r'[A-Za-z0-9_-]{1,40}', value) is None for key, value in query):
        raise PageDataError('The requested source document version is unsupported.')
    return RequestKey('documents', path, query)


def document_key_from_url(url: str) -> RequestKey:
    """
    Accepts a PDF URL only from the configured document source.

    Called by: local_document_url(), views.source_document(), tools.source_capture.capture_document_chain()
    """
    origin = urlsplit(source_origin('documents'))
    parsed = urlsplit(url)
    if parsed.netloc != origin.netloc or parsed.scheme not in {'http', origin.scheme} or parsed.fragment:
        raise PageDataError('The document URL does not match the configured source.')
    return document_key(parsed.path, tuple(parse_qsl(parsed.query, keep_blank_values=True)))


def local_document_url(url: str) -> str:
    """
    Rewrites a supported CV link to the local recorded or live PDF route.

    Called by: source_pages.profile_data()
    """
    result = url
    if settings.DOCUMENTS_URL:
        try:
            key = document_key_from_url(url)
            result = reverse('source_document', kwargs={'filename': key.path.lstrip('/')})
            if key.query:
                result += '?' + urlencode(key.query)
        except PageDataError:
            pass
    return result


def source_origin(service: str) -> str:
    """
    Reads a configured source origin without allowing paths outside its root.

    Called by: read_source(), document_key_from_url()
    """
    raw = {
        'solr': settings.SOLR_URL,
        'images': settings.IMAGES_URL,
        'documents': settings.DOCUMENTS_URL,
        'viz': settings.VIZ_SERVICE_URL,
        'vitro': settings.VIVO_BACKEND_URL,
    }.get(service, '')
    parsed = urlsplit(raw)
    if (
        parsed.scheme not in {'http', 'https'}
        or not parsed.netloc
        or parsed.query
        or parsed.fragment
        or (service == 'documents' and parsed.path not in {'', '/'})
    ):
        raise PageDataError(f'{service} source URL is not configured.')
    result = raw.rstrip('/')
    return result


def read_source(key: RequestKey, mode: str) -> RecordedResponse:
    """
    Reads one response from the configured live source or exact saved input, with no fallback.

    Called by: source_pages.response_object(), views.source_image(), views.source_document(), tools.source_capture.CapturingReader.__call__()
    """
    if mode == 'replay':
        manifest = settings.UPSTREAM_RECORDING_MANIFEST
        if not manifest:
            raise PageDataError('Replay requires an upstream recording manifest.')
        try:
            recordings = load_recordings(Path(manifest))
            if recordings.data_kind != 'recorded':
                raise RecordingError('Replay requires authentic recorded responses.')
            result = recordings.get(settings.UPSTREAM_RECORDING_CASE, key)
        except RecordingError as exc:
            raise PageDataError(str(exc)) from exc
    elif mode == 'live':
        if key.service == 'book_db':
            from vivo_app.lib.source_books import BOOKS_KEY, book_rows_response

            if key != BOOKS_KEY:
                raise PageDataError('The requested homepage book query is unsupported.')
            result = book_rows_response()
        else:
            origin = source_origin(key.service)
            limit = MAX_DOCUMENT_BYTES if key.service == 'documents' else MAX_RESPONSE_BYTES
            try:
                with (
                    httpx2.Client(timeout=10.0, follow_redirects=False, trust_env=False) as client,
                    client.stream('GET', origin + key.path, params=list(key.query), headers=dict(key.headers)) as response,
                ):
                    chunks: list[bytes] = []
                    size = 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > limit:
                            raise PageDataError('The upstream response exceeds the configured size limit.')
                        chunks.append(chunk)
                    headers = [('content-type', response.headers.get('content-type', ''))]
                    if key.service == 'documents' and 'location' in response.headers:
                        headers.append(('location', response.headers['location']))
                    result = RecordedResponse(response.status_code, tuple(headers), b''.join(chunks))
            except httpx2.HTTPError as exc:
                raise PageDataError(f'{key.service} source request failed.') from exc
    else:
        raise PageDataError('Source requests require replay or live mode.')
    limit = MAX_DOCUMENT_BYTES if key.service == 'documents' else MAX_RESPONSE_BYTES
    allowed_status = {200, 301, 302} if key.service == 'documents' else ({200, 404} if key.service == 'vitro' else {200})
    if result.status not in allowed_status or len(result.body) > limit:
        raise PageDataError(f'{key.service} source returned an unusable response.')
    return result
