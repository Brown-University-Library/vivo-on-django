"""
Converts validated page data and explicit failures to HTTP responses.
"""

import logging

from django.http import HttpResponse, QueryDict

from vivo_app.lib.prepared_data import PageDataError, PreparedEntry

logger = logging.getLogger(__name__)


def query_pairs(query: QueryDict) -> list[tuple[str, str]]:
    """
    Preserves every value of repeated query parameters.

    Called by: views.search(), views.display_show(), views.search_facets()
    """
    return [(key, value) for key, values in query.lists() for value in values]


def prepared_response(entry: PreparedEntry) -> HttpResponse:
    """
    Returns the recorded status, relevant headers, and original response bytes.

    Called by: views.search(), views.display_show(), views.search_facets()
    """
    response = HttpResponse(entry.body, status=entry.status, content_type=entry.content_type)
    for key, value in entry.headers:
        response[key] = value
    return response


def data_unavailable(error: PageDataError) -> HttpResponse:
    """
    Reports unavailable data without exposing any record or filesystem values.

    Called by: views.search(), views.display_show(), views.search_facets(), views.prepared_asset()
    """
    logger.error(f'page_data_error, ``{error}``')
    return HttpResponse(f'Page data unavailable: {error}'.encode(), status=503, content_type='text/plain; charset=utf-8')
