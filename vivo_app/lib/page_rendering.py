"""
Converts validated page data and explicit failures to HTTP responses.
"""

import logging

from django.http import HttpRequest, HttpResponse, JsonResponse, QueryDict
from django.shortcuts import render
from django.template.loader import get_template
from django.utils.log import log_response

from vivo_app.lib.page_errors import PageDataError
from vivo_app.lib.reports import ReportError

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


def query_pairs(query: QueryDict, allowed_names: set[str] | None = None) -> list[tuple[str, str]]:
    """
    Preserves repeated query values, optionally keeping only names used by the requested page.

    Called by: views.search(), views.display_show(), views.source_document(), valid_format_query(), visualization views
    """
    return [
        (key, value) for key, values in query.lists() if allowed_names is None or key in allowed_names for value in values
    ]


def valid_format_query(query: QueryDict, fmt: str) -> bool:
    """
    Accepts an absent format parameter or one value matching the URL's explicit format.

    Called by: views.individual_export(), views.visualization_publications(), and the other visualization views
    """
    pairs = query_pairs(query, {'format'})
    return not pairs or (bool(fmt) and pairs == [('format', fmt)])


def log_error_response(request: HttpRequest, response: HttpResponse, error: Exception | None) -> HttpResponse:
    """
    Logs handled responses as warnings and unexpected exceptions once with their traceback for administrator email.

    Called by: data_unavailable(), middleware.SourceDataMiddleware, and views returning error responses
    """
    log_response(
        '%s: %s',
        response.reason_phrase,
        request.path,
        response=response,
        request=request,
        level='warning' if error is None or isinstance(error, (PageDataError, ReportError)) else 'error',
        exception=error,
    )
    return response


def data_unavailable(request: HttpRequest, error: PageDataError) -> HttpResponse:
    """
    Reports unavailable data while keeping the handled exception in warning logs without administrator email.

    Called by: views.search(), views.display_show(), views.search_facets()
    """
    logger.warning('page_data_error, ``%s``', error, exc_info=error)
    response = HttpResponse(f'Page data unavailable: {error}'.encode(), status=503, content_type='text/plain; charset=utf-8')
    return log_error_response(request, response, error)
