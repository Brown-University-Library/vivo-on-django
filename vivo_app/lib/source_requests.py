"""
Builds and reads the upstream requests for a search-to-profile journey.
"""

import re
from pathlib import Path
from urllib.parse import urlsplit

import httpx2
from django.conf import settings

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RecordingError, RequestKey, load_recordings

SEARCH_FIELDS = (
    'short_id_s^2500 email_s^2500 nameText^2000 title_t^1600 department_t^1500 '
    'research_areas_en^400 affiliations_en^450 nameUnstemmed^4 nameStemmed^4 '
    'nameLowercase ALLTEXT^2 ALLTEXTUNSTEMMED^2'
)
FACETS = ('record_type', 'affiliations', 'research_areas', 'published_in')
FACET_TITLES = ('Type', 'Brown Affiliations', 'Research Areas', 'Published In')
MAX_RESPONSE_BYTES = 3_000_000


def quoted(value: str) -> str:
    """
    Quotes a value for a Solr field query after rejecting control characters.

    Called by: search_key(), profile_key()
    """
    if any(ord(character) < 32 for character in value):
        raise PageDataError('Search and filter values cannot contain control characters.')
    result = '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return result


def search_key(query: str, page: int, filters: list[tuple[str, str]]) -> RequestKey:
    """
    Builds one bounded Solr search with the same main fields and ranking as Rails.

    Called by: source_pages.search_data(), capture_solr_journey.Command.handle()
    """
    if page < 1 or page > 1000 or len(query) > 300 or len(filters) > 12:
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
        ('facet.limit', '10'),
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
    Looks up a single canonical person record by its public identifier.

    Called by: source_pages.profile_data(), capture_solr_journey.Command.handle()
    """
    if re.fullmatch(r'[A-Za-z0-9_-]{1,80}', identifier) is None:
        raise PageDataError('The requested profile identifier is unsupported.')
    query = f'id:{quoted("http://vivo.brown.edu/individual/" + identifier)}'
    return RequestKey(
        'solr',
        '/select',
        (
            ('q', query),
            ('fl', 'id,record_type,thumbnail_file_path_s,json_txt,display_name_s'),
            ('rows', '1'),
            ('wt', 'json'),
        ),
    )


def image_path(file_path: object) -> str | None:
    """
    Converts a VIVO thumbnail path to its public image-service path.

    Called by: source_pages.thumbnail_url(), capture_solr_journey.Command.handle()
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

    Called by: views.source_image(), capture_solr_journey.Command.handle()
    """
    if re.fullmatch(r'/profile-images/(?:[A-Za-z0-9]{1,3}/)+[A-Za-z0-9._^-]+', path) is None:
        raise PageDataError('The requested source image path is unsupported.')
    return RequestKey('images', path)


def source_origin(service: str) -> str:
    """
    Reads a configured source origin without allowing paths outside its root.

    Called by: read_source()
    """
    raw = settings.SOLR_URL if service == 'solr' else settings.IMAGES_URL if service == 'images' else ''
    parsed = urlsplit(raw)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc or parsed.query or parsed.fragment:
        raise PageDataError(f'{service} source URL is not configured.')
    result = raw.rstrip('/')
    return result


def read_source(key: RequestKey, mode: str) -> RecordedResponse:
    """
    Reads one response from the tunnel or exact saved input, with no fallback.

    Called by: source_pages.read_json(), views.source_image(), capture_solr_journey.Command.handle()
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
        origin = source_origin(key.service)
        try:
            with (
                httpx2.Client(timeout=10.0, follow_redirects=False, trust_env=False) as client,
                client.stream('GET', origin + key.path, params=list(key.query), headers=dict(key.headers)) as response,
            ):
                chunks: list[bytes] = []
                size = 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > MAX_RESPONSE_BYTES:
                        raise PageDataError('The upstream response exceeds the configured size limit.')
                    chunks.append(chunk)
                result = RecordedResponse(
                    response.status_code,
                    (('content-type', response.headers.get('content-type', '')),),
                    b''.join(chunks),
                )
        except httpx2.HTTPError as exc:
            raise PageDataError(f'{key.service} source request failed.') from exc
    else:
        raise PageDataError('Source requests require replay or live mode.')
    if result.status != 200 or len(result.body) > MAX_RESPONSE_BYTES:
        raise PageDataError(f'{key.service} source returned an unusable response.')
    return result
