"""
Checks deployed page data and selected live sources without printing records or URLs.
"""

import hashlib
import json
from pathlib import Path
from typing import ClassVar

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser

from vivo_app.lib.page_data import selected_mode
from vivo_app.lib.prepared_data import PageDataError, load_bundle
from vivo_app.lib.source_books import homepage_books
from vivo_app.lib.source_graph import visualization_list
from vivo_app.lib.source_requests import read_source, vitro_key
from vivo_app.lib.source_status import status_data

SOURCES = ('solr', 'viz', 'vivo', 'books')


def prepared_check() -> dict[str, object]:
    """
    Validates the configured prepared bundle from the checkout directory.

    Called by: Command.handle()
    """
    directory = Path(settings.PREPARED_FIXTURE_DIR)
    if not directory.is_absolute():
        directory = Path(settings.BASE_DIR) / directory
    try:
        bundle = load_bundle(directory)
        result: dict[str, object] = {'status': 'ok', 'version': bundle.version, 'cases': len(bundle.cases)}
    except PageDataError as exc:
        result = {'status': 'error', 'reason': str(exc)}
    return result


def source_check(name: str, vivo_id: str) -> dict[str, object]:
    """
    Makes one small read for a named service and keeps returned content private.

    Called by: Command.handle()
    """
    try:
        if name == 'solr':
            status_data('live')
            result: dict[str, object] = {'status': 'ok', 'check': 'searchable record count'}
        elif name == 'viz':
            visualization_list('coauthors', 'live')
            result = {'status': 'ok', 'check': 'graph availability list'}
        elif name == 'vivo':
            if not vivo_id:
                raise PageDataError('Supply --vivo-id to check one existing record export.')
            response = read_source(vitro_key(vivo_id, 'jsonld'), 'live')
            result = {'status': 'ok' if response.status == 200 else 'missing_record', 'http_status': response.status}
            if response.status == 200:
                result['sha256'] = hashlib.sha256(response.body).hexdigest()
        elif name == 'books':
            homepage_books('live')
            result = {'status': 'ok', 'check': 'active homepage books and image prefix'}
        else:
            raise PageDataError('Unknown source name.')
    except PageDataError as exc:
        result = {'status': 'error', 'reason': str(exc)}
    return result


class Command(BaseCommand):
    """Checks the active data mode and optional live sources from the server."""

    help = 'Check page data and selected live sources with read-only requests and safe output.'
    requires_system_checks: ClassVar[list[str]] = []

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Accepts repeated source names and one optional existing VIVO record ID.

        Called by: Django management command runner
        """
        parser.add_argument('--source', action='append', choices=SOURCES, default=[])
        parser.add_argument('--vivo-id', default='')

    def handle(self, *args: object, **options: object) -> None:
        """
        Prints a compact report and exits nonzero when a selected check fails.

        Called by: Django management command runner
        """
        try:
            mode = selected_mode()
            mode_result: dict[str, object] = {'status': 'ok', 'value': mode}
        except PageDataError as exc:
            mode_result = {'status': 'error', 'reason': str(exc)}
            mode = settings.PAGE_DATA_MODE
        report: dict[str, object] = {'page_data_mode': mode_result}
        if mode == 'prepared':
            report['prepared_bundle'] = prepared_check()
        selected = options.get('source')
        vivo_id = options.get('vivo_id')
        if isinstance(selected, list) and isinstance(vivo_id, str):
            report['sources'] = {name: source_check(name, vivo_id) for name in dict.fromkeys(selected)}
        self.stdout.write(json.dumps(report, indent=2))
        failed = mode_result['status'] != 'ok'
        prepared = report.get('prepared_bundle')
        if isinstance(prepared, dict):
            failed = failed or prepared.get('status') != 'ok'
        sources = report.get('sources')
        if isinstance(sources, dict):
            failed = failed or any(isinstance(value, dict) and value.get('status') != 'ok' for value in sources.values())
        if failed:
            raise SystemExit(1)
