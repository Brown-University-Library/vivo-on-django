"""
Supplies application page data from configured sources.
"""

import logging
import time
from dataclasses import dataclass

from django.conf import settings

from vivo_app.lib.page_errors import MissingRecordError, PageDataError, SourceTimeoutError
from vivo_app.lib.source_books import homepage_books
from vivo_app.lib.source_pages import display_document, first_text, organization_data, profile_data, search_data
from vivo_app.lib.source_requests import read_source, vitro_key
from vivo_app.lib.source_teams import custom_organization_members, team_data
from vivo_app.lib.source_types import SourceResponse

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DisplayPage:
    """Supplies the template and context for a person, organization, or team page."""

    template_name: str
    context: dict[str, object]


def check_source_configuration() -> None:
    """
    Checks required source configuration without contacting services.

    Called by: checks.check_page_data(), middleware.SourceDataMiddleware.__call__(), check_dev_sources.Command.handle()
    """
    if not settings.SOLR_URL:
        raise PageDataError('Search and profiles require SOLR_URL.')


def get_search_data(path: str, query: list[tuple[str, str]]) -> dict[str, object]:
    """
    Supplies search results and navigation from Solr.

    Called by: views.search()
    """
    return search_data(query)


def get_display_data(path: str, query: list[tuple[str, str]]) -> DisplayPage | SourceResponse:
    """
    Selects an HTML page by record type or reads the original VIVO JSON-LD response.

    Called by: display_jsonld_cache.cached_display_data()
    """
    if query:
        raise PageDataError('Display query options are not connected to source data yet.')
    identifier = path.rstrip('/').rsplit('/', 1)[-1]
    result: DisplayPage | SourceResponse
    if identifier.startswith('team-'):
        result = DisplayPage('display/organization_data.html', {'organization': team_data(identifier)})
    else:
        doc = display_document(identifier)
        record_type = first_text(doc.get('record_type'))
        if record_type == 'PEOPLE':
            result = DisplayPage('display/show.html', {'profile': profile_data(identifier, doc=doc)})
        elif record_type == 'ORGANIZATION':
            organization = organization_data(identifier, extra_member_ids=custom_organization_members(identifier), doc=doc)
            result = DisplayPage('display/organization_data.html', {'organization': organization})
        elif not record_type:
            raise MissingRecordError('The requested display record has no record type.')
        else:
            result = display_jsonld_response(identifier)
    return result


def display_jsonld_response(identifier: str) -> SourceResponse:
    """
    Retries a timed-out VIVO display read once, preserving source validation and response bytes.

    Called by: get_display_data()
    """
    key = vitro_key(identifier, 'jsonld')
    try:
        result = read_source(key)
    except SourceTimeoutError:
        logger.warning('Retrying timed-out VIVO display read; id, ``%s``', identifier)
        time.sleep(0.25)
        result = read_source(key)
    return result


def get_home_data(path: str, query: list[tuple[str, str]]) -> dict[str, object]:
    """
    Supplies homepage books and background choices.

    Called by: views.home_index()
    """
    if path != '/' or query:
        raise PageDataError('The requested homepage variation is unsupported.')
    return homepage_books()
