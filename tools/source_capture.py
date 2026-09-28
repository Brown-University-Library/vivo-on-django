"""
Captures one bounded search-to-profile journey outside Git for local replay.
"""

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RecordingError, RequestKey, external_path
from vivo_app.lib.source_books import BOOKS_KEY
from vivo_app.lib.source_graph import visualization_graph
from vivo_app.lib.source_pages import (
    facet_values_data,
    organization_data,
    organization_publications_data,
    profile_data,
    search_data,
)
from vivo_app.lib.source_requests import document_key, document_key_from_url, image_key, image_path, read_source, vitro_key
from vivo_app.lib.source_teams import CUSTOM_ORGANIZATION_IDS, custom_organization_members, team_data

MAX_REQUESTS = 120
MAX_TOTAL_BYTES = 60_000_000
MIN_SOLR_INTERVAL_SECONDS = 1.0


class CapturingReader:
    """Keeps each source response while the ordinary page parser reads it."""

    def __init__(self) -> None:
        """
        Starts an empty bounded capture.

        Called by: capture_journey()
        """
        self.responses: dict[RequestKey, RecordedResponse] = {}
        self.last_solr_request_at: float | None = None

    def __call__(self, key: RequestKey, mode: str) -> RecordedResponse:
        """
        Reads a live response once and retains its original bytes.

        Called by: source_pages.search_data(), source_pages.profile_data(), source_pages.organization_data(), capture_journey()
        """
        if mode != 'live':
            raise PageDataError('Captures require live source access.')
        if key not in self.responses:
            if len(self.responses) >= MAX_REQUESTS:
                raise PageDataError('The capture reached its request limit.')
            if key.service == 'solr':
                if self.last_solr_request_at is not None:
                    elapsed = time.monotonic() - self.last_solr_request_at
                    if elapsed < MIN_SOLR_INTERVAL_SECONDS:
                        time.sleep(MIN_SOLR_INTERVAL_SECONDS - elapsed)
                self.last_solr_request_at = time.monotonic()
            response = read_source(key, 'live')
            if sum(len(item.body) for item in self.responses.values()) + len(response.body) > MAX_TOTAL_BYTES:
                raise PageDataError('The capture reached its total byte limit.')
            self.responses[key] = response
        return self.responses[key]


def image_requests(responses: dict[RequestKey, RecordedResponse]) -> list[RequestKey]:
    """
    Finds the image paths named by captured Solr documents.

    Called by: capture_journey()
    """
    paths: set[str] = set()
    for key, response in responses.items():
        if key.service != 'solr':
            continue
        value: object = json.loads(response.body)
        if not isinstance(value, dict) or not isinstance(value.get('response'), dict):
            raise PageDataError('A captured Solr response has no document list.')
        docs = value['response'].get('docs')
        if not isinstance(docs, list):
            raise PageDataError('A captured Solr response has no document list.')
        for doc in docs:
            if isinstance(doc, dict):
                path = image_path(doc.get('thumbnail_file_path_s'))
                if path:
                    paths.add(path)
    if len(paths) + len(responses) > MAX_REQUESTS:
        raise PageDataError('The journey has more images than the capture limit permits.')
    return [image_key(path) for path in sorted(paths)]


def capture_document_chain(url: object, reader: CapturingReader) -> None:
    """
    Captures a local CV link and at most two version redirects as exact responses.

    Called by: capture_journey()
    """
    if not isinstance(url, str):
        raise PageDataError('The profile CV link is invalid.')
    parsed = urlsplit(url)
    if parsed.path.startswith('/source-documents/'):
        key = document_key(parsed.path.removeprefix('/source-documents'), tuple(parse_qsl(parsed.query)))
        for _ in range(3):
            response = reader(key, 'live')
            if response.status == 200:
                return
            location = dict(response.headers).get('location', '')
            key = document_key_from_url(location)
        raise PageDataError('The document source redirected too many times.')


def write_capture(directory: Path, responses: dict[RequestKey, RecordedResponse], case_id: str = 'search-profile') -> None:
    """
    Writes original response bytes and a checksum manifest outside Git.

    Called by: capture_journey()
    """
    try:
        root = external_path(directory)
        root.mkdir(parents=True, exist_ok=False)
    except (OSError, RecordingError) as exc:
        raise PageDataError('Use a new capture directory outside Git.') from exc
    recordings: list[dict[str, object]] = []
    names: list[str] = []
    for number, (key, response) in enumerate(responses.items(), 1):
        name = f'upstream-{number:02d}'
        filename = f'response-{number:02d}.bin'
        (root / filename).write_bytes(response.body)
        names.append(name)
        recordings.append(
            {
                'id': name,
                'request': {
                    'service': key.service,
                    'method': 'GET',
                    'path': key.path,
                    'query': [list(pair) for pair in key.query],
                    'headers': [list(pair) for pair in key.headers],
                },
                'response': {
                    'status': response.status,
                    'headers': [list(pair) for pair in response.headers],
                    'body_file': filename,
                    'sha256': hashlib.sha256(response.body).hexdigest(),
                },
            }
        )
    manifest = {
        'schema_version': 1,
        'data_kind': 'recorded',
        'captured_at': datetime.now(UTC).isoformat(),
        'recordings': recordings,
        'cases': {case_id: names},
    }
    (root / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


def capture_vivo_exports(identifier: str, output: Path) -> int:
    """
    Captures three original VIVO formats with a pause between requests.

    Called by: capture_vivo_exports.Command.handle()
    """
    reader = CapturingReader()
    for number, fmt in enumerate(('jsonld', 'ttl', 'rdf')):
        if number:
            time.sleep(0.3)
        response = reader(vitro_key(identifier, fmt), 'live')
        if response.status != 200:
            raise PageDataError('A VIVO representation is unavailable.')
    write_capture(output, reader.responses, 'vivo-exports')
    return len(reader.responses)


def capture_homepage_books(output: Path) -> int:
    """
    Captures the active homepage book rows outside Git for exact replay.

    Called by: capture_homepage_books.Command.handle()
    """
    reader = CapturingReader()
    reader(BOOKS_KEY, 'live')
    write_capture(output, reader.responses, 'homepage-books')
    return len(reader.responses)


def capture_custom_graph(identifier: str, output: Path) -> int:
    """
    Captures paced Solr inputs for a team or specialized-organization graph.

    Called by: capture_custom_graph.Command.handle()
    """
    if not (identifier.startswith('team-') or identifier in CUSTOM_ORGANIZATION_IDS):
        raise PageDataError('The selected record does not use a calculated Solr graph.')
    reader = CapturingReader()
    visualization_graph('collaborators', identifier, 'live', reader)
    if not reader.responses or any(key.service != 'solr' for key in reader.responses):
        raise PageDataError('The selected record does not use a calculated Solr graph.')
    write_capture(output, reader.responses, 'custom-graph')
    return len(reader.responses)


def capture_journey(
    query: str, identifier: str, output: Path, organization_id: str | None, extra_searches: list[str]
) -> int:
    """
    Captures the exact source responses used to render one selected journey.

    Called by: capture_solr_journey.Command.handle()
    """
    reader = CapturingReader()
    search_page = search_data([('q', query)], 'live', reader)
    results = search_page.get('results')
    if not isinstance(results, list) or not any(isinstance(row, dict) and row.get('id') == identifier for row in results):
        raise PageDataError('The selected profile is not in the captured search results.')
    search_data([('q', query), ('fq', 'record_type|PEOPLE')], 'live', reader)
    facet_values_data([('q', query), ('f_name', 'record_type')], 'live', reader)
    facet_values_data([('q', query), ('fq', 'record_type|PEOPLE'), ('f_name', 'record_type')], 'live', reader)
    for raw in extra_searches:
        pairs = parse_qsl(raw.removeprefix('?'), keep_blank_values=True)
        search_data(pairs, 'live', reader)
        facet_values_data([*pairs, ('f_name', 'record_type')], 'live', reader)
    profile = profile_data(identifier, 'live', reader)
    capture_document_chain(profile.get('cv_url'), reader)
    if organization_id:
        if organization_id.startswith('team-'):
            team_data(organization_id, 'live', reader)
        else:
            extras = custom_organization_members(organization_id, 'live', reader)
            organization_data(organization_id, 'live', reader, extras)
            organization_publications_data(organization_id, 'live', reader, extras)
    for key in image_requests(reader.responses):
        reader(key, 'live')
    write_capture(output, reader.responses)
    return len(reader.responses)
