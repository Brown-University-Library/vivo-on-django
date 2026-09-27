"""
Converts validated page data and explicit failures to HTTP responses.
"""

import logging

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse, QueryDict
from django.shortcuts import render
from django.template.loader import get_template

from vivo_app.lib.prepared_data import PageDataError, PreparedEntry

logger = logging.getLogger(__name__)


def render_or_stub(
    request: HttpRequest, template_name: str, context: dict[str, object] | None = None, status: int = 200
) -> HttpResponse:
    """
    Renders sample pages or returns a placeholder after logging a template failure.

    Called by: vivo_app.views sample page and error handlers
    """
    context = context or {}
    if request.GET.get('format') == 'json':
        response = JsonResponse(context, status=status)
    else:
        try:
            get_template(template_name)
            response = render(request, template_name, context, status=status)
        except Exception:
            logger.exception('Sample page rendering failed.')
            response = HttpResponse(f'Stub for {template_name}'.encode(), status=status, content_type='text/plain')
    return response


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
    location = next((value for key, value in entry.headers if key.lower() == 'location'), '')
    if 300 <= entry.status < 400 and location:
        response = HttpResponseRedirect(location, content_type=entry.content_type)
        response.status_code = entry.status
        response.content = entry.body
    else:
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
