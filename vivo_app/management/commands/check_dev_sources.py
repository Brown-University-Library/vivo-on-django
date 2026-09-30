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
from vivo_app.lib.source_pages import (
    documents,
    entries,
    facet_values_data,
    first_text,
    record_data,
    record_id,
    response_object,
    search_data,
)
from vivo_app.lib.source_requests import profile_key, read_source, vitro_key
from vivo_app.lib.source_status import status_data

SOURCES = ('solr', 'search', 'search-facets', 'profile', 'viz', 'vivo', 'books')


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


def source_check(name: str, vivo_id: str, search_query: str = 'biology') -> dict[str, object]:
    """
    Checks a named source with read-only requests and keeps returned content private.

    Called by: Command.handle()
    """
    try:
        if name == 'solr':
            status_data('live')
            result: dict[str, object] = {'status': 'ok', 'check': 'searchable record count'}
        elif name == 'search':
            search = search_data([('q', search_query)], 'live')
            results = search.get('results')
            if not isinstance(results, list):
                raise PageDataError('Search processing returned no result list.')
            result = {'status': 'ok', 'check': 'search results and facets', 'results_on_page': len(results)}
        elif name == 'search-facets':
            search = search_data([('q', search_query)], 'live')
            facets = search.get('facets')
            if not isinstance(facets, list):
                raise PageDataError('Search processing returned no facet list.')
            affiliation = next(
                (facet for facet in facets if isinstance(facet, dict) and facet.get('name') == 'affiliations'), None
            )
            shown = affiliation.get('values') if isinstance(affiliation, dict) else []
            if not isinstance(shown, list):
                raise PageDataError('Search processing returned an invalid affiliation facet.')
            full = facet_values_data([('q', search_query), ('f_name', 'affiliations')], 'live')
            result = {
                'status': 'ok' if len(full) >= len(shown) else 'error',
                'check': 'affiliation values shown and returned by the full facet request',
                'shown_values': len(shown),
                'full_values': len(full),
            }
        elif name == 'profile':
            if not vivo_id:
                raise PageDataError('Supply --vivo-id to check one person profile.')
            response = response_object(profile_key(vivo_id), 'live', read_source)
            docs, _ = documents(response)
            if not docs or record_id(docs[0]) != vivo_id or first_text(docs[0].get('record_type')) != 'PEOPLE':
                raise PageDataError('The requested source record is not a person profile.')
            collaborators = entries(record_data(docs[0]), 'collaborators')
            enabled = first_text(docs[0].get('show_visualizations_s')) == 'true'
            graph_available = False
            if collaborators and enabled:
                graphs = visualization_list('collaborators', 'live')
                graph_available = first_text(docs[0].get('id')) in graphs
            result = {
                'status': 'ok',
                'check': 'person profile collaborator source',
                'collaborators': len(collaborators),
                'profile_visualizations_enabled': enabled,
                'django_visualizations_enabled': settings.VIZ_ENABLED,
                'collaborator_graph_available': graph_available,
            }
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
        Accepts repeated source names, one optional VIVO record ID, and a search term.

        Called by: Django management command runner
        """
        parser.add_argument('--source', action='append', choices=SOURCES, default=[])
        parser.add_argument('--vivo-id', default='')
        parser.add_argument('--search-query', default='biology', help='Term for the search source check (not printed)')

    def handle(self, *args: object, **options: object) -> None:
        """
        Checks selected live sources independently, or checks the selected page-data mode.

        Called by: Django management command runner
        """
        requested = options.get('source')
        source_names = [name for name in requested if isinstance(name, str)] if isinstance(requested, list) else []
        requested_id = options.get('vivo_id')
        vivo_id = requested_id if isinstance(requested_id, str) else ''
        requested_query = options.get('search_query')
        search_query = requested_query if isinstance(requested_query, str) else ''
        report: dict[str, object]
        if source_names:
            sources = {name: source_check(name, vivo_id, search_query) for name in dict.fromkeys(source_names)}
            report = {'sources': sources}
            failed = any(value['status'] != 'ok' for value in sources.values())
        else:
            try:
                mode = selected_mode()
                mode_result: dict[str, object] = {'status': 'ok', 'value': mode}
            except PageDataError as exc:
                mode_result = {'status': 'error', 'reason': str(exc)}
                mode = settings.PAGE_DATA_MODE
            report = {'page_data_mode': mode_result, 'sources': {}}
            if mode == 'prepared':
                report['prepared_bundle'] = prepared_check()
            failed = mode_result['status'] != 'ok'
            prepared = report.get('prepared_bundle')
            if isinstance(prepared, dict):
                failed = failed or prepared.get('status') != 'ok'
        self.stdout.write(json.dumps(report, indent=2))
        if failed:
            raise SystemExit(1)
