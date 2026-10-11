"""
Converts validated page data and explicit failures to HTTP responses.
"""

import logging

from django.http import HttpRequest, HttpResponse, JsonResponse, QueryDict
from django.shortcuts import render
from django.template.loader import get_template

from vivo_app.lib.page_errors import PageDataError

logger = logging.getLogger(__name__)


def render_or_stub(
    request: HttpRequest, template_name: str, context: dict[str, object] | None = None, status: int = 200
) -> HttpResponse:
    """
    Renders informational pages or returns a placeholder after logging a template failure.

    Called by: vivo_app.views informational page and error handlers
    """
    context = context or {}
    if request.GET.get('format') == 'json':
        response = JsonResponse(context, status=status)
    else:
        try:
            get_template(template_name)
            response = render(request, template_name, context, status=status)
        except Exception:
            logger.exception('Page rendering failed.')
            response = HttpResponse(f'Stub for {template_name}'.encode(), status=status, content_type='text/plain')
    return response


def query_pairs(query: QueryDict) -> list[tuple[str, str]]:
    """
    Preserves every value of repeated query parameters.

    Called by: views.search(), views.display_show(), views.search_facets()
    """
    return [(key, value) for key, values in query.lists() for value in values]


def data_unavailable(error: PageDataError) -> HttpResponse:
    """
    Reports unavailable data without exposing any record or filesystem values.

    Called by: views.search(), views.display_show(), views.search_facets()
    """
    logger.error(f'page_data_error, ``{error}``')
    return HttpResponse(f'Page data unavailable: {error}'.encode(), status=503, content_type='text/plain; charset=utf-8')
