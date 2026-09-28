"""
Captures one bounded search-to-profile journey outside Git for local replay.
"""

import hashlib
import json
from argparse import ArgumentParser
from datetime import UTC, datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RecordingError, RequestKey, external_path
from vivo_app.lib.source_pages import profile_data, search_data
from vivo_app.lib.source_requests import image_key, image_path, read_source

MAX_REQUESTS = 24
MAX_TOTAL_BYTES = 25_000_000


class CapturingReader:
    """Keeps each source response while the ordinary page parser reads it."""

    def __init__(self) -> None:
        """
        Starts an empty bounded capture.

        Called by: Command.handle()
        """
        self.responses: dict[RequestKey, RecordedResponse] = {}

    def __call__(self, key: RequestKey, mode: str) -> RecordedResponse:
        """
        Reads a live response once and retains its original bytes.

        Called by: source_pages.search_data(), source_pages.profile_data(), Command.handle()
        """
        if mode != 'live':
            raise PageDataError('Captures require live source access.')
        if key not in self.responses:
            if len(self.responses) >= MAX_REQUESTS:
                raise PageDataError('The capture reached its request limit.')
            response = read_source(key, 'live')
            if sum(len(item.body) for item in self.responses.values()) + len(response.body) > MAX_TOTAL_BYTES:
                raise PageDataError('The capture reached its total byte limit.')
            self.responses[key] = response
        return self.responses[key]


def image_requests(responses: dict[RequestKey, RecordedResponse]) -> list[RequestKey]:
    """
    Finds the image paths named by captured Solr documents.

    Called by: Command.handle()
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


def write_capture(directory: Path, responses: dict[RequestKey, RecordedResponse]) -> None:
    """
    Writes original response bytes and a checksum manifest outside Git.

    Called by: Command.handle()
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
        'cases': {'search-profile': names},
    }
    (root / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


class Command(BaseCommand):
    """Captures one bounded live journey for exact local replay."""

    help = 'Capture a search and person profile, including required images, outside Git.'

    def add_arguments(self, parser: ArgumentParser) -> None:
        """
        Adds one query, one profile identifier, and a new external directory.

        Called by: Django management command runner
        """
        parser.add_argument('--query', required=True)
        parser.add_argument('--id', required=True)
        parser.add_argument('--output', required=True, type=Path)

    def handle(self, *args: object, **options: object) -> None:
        """
        Captures the exact requests used to render one journey.

        Called by: Django management command runner
        """
        query, identifier, output = options['query'], options['id'], options['output']
        if not isinstance(query, str) or not isinstance(identifier, str) or not isinstance(output, Path):
            raise CommandError('Query, profile identifier, and output directory are required.')
        reader = CapturingReader()
        try:
            search_page = search_data([('q', query)], 'live', reader)
            results = search_page.get('results')
            if not isinstance(results, list) or not any(
                isinstance(row, dict) and row.get('id') == identifier for row in results
            ):
                raise PageDataError('The selected profile is not in the captured search results.')
            search_data([('q', query), ('fq', 'record_type|PEOPLE')], 'live', reader)
            profile_data(identifier, 'live', reader)
            for key in image_requests(reader.responses):
                reader(key, 'live')
            write_capture(output, reader.responses)
        except PageDataError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(f'Captured {len(reader.responses)} responses for one replay case.')
