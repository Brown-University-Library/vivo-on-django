"""
Keeps prepared and replay browser loads local.
"""

from collections.abc import Callable
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import reverse

from vivo_app.lib.bot_detect import challenge_passed
from vivo_app.lib.page_data import selected_mode
from vivo_app.lib.page_rendering import data_unavailable
from vivo_app.lib.prepared_data import PageDataError


class LocalPageDataMiddleware:
    """Prevents automatic remote browser loads and sample fallbacks in source modes."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """
        Keeps the next Django request handler.

        Called by: Django middleware setup
        """
        self.get_response = get_response

    def process_view(
        self, request: HttpRequest, view_func: object, view_args: object, view_kwargs: object
    ) -> HttpResponse | None:
        """
        Rejects unconverted public handlers when prepared or source data is selected.

        Called by: Django request handler
        """
        response = None
        supported = {
            'home_index',
            'home_about',
            'home_help',
            'home_status',
            'search',
            'display_show',
            'organization_publications_tsv',
            'visualization_graph_json',
            'visualization_graph_csv',
            'visualization_coauthor',
            'visualization_coauthor_treemap',
            'visualization_collab',
            'visualization_publications',
            'visualization_research',
            'search_facets',
            'people',
            'organizations',
            'individual_redirect',
            'individual_export',
            'old_image',
            'prepared_asset',
            'prepared_document',
            'source_image',
            'source_document',
            'error_check',
            'version',
            'bot_detect_challenge',
        }
        if settings.PAGE_DATA_MODE in {'live', 'replay'}:
            supported.update({'advanced_search', 'display_index'})
        if (
            settings.PAGE_DATA_MODE in {'prepared', 'replay', 'live'}
            and getattr(view_func, '__module__', '') == 'vivo_app.views'
            and getattr(view_func, '__name__', '') not in supported
        ):
            label = 'prepared data' if settings.PAGE_DATA_MODE == 'prepared' else 'source data'
            response = HttpResponse(
                f'This endpoint is not connected to {label} yet.'.encode(), status=503, content_type='text/plain'
            )
        return response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Limits resource loads to this origin when local data is selected.

        Called by: Django request handler
        """
        try:
            mode = selected_mode()
        except PageDataError as exc:
            response = data_unavailable(exc)
            mode = ''
        else:
            response = self.get_response(request)
        if mode in {'prepared', 'replay'}:
            if response.status_code == 200 and response.get('Content-Type', '').startswith('text/html'):
                response['Cache-Control'] = 'max-age=0, private, must-revalidate'
            response['Content-Security-Policy'] = (
                "default-src 'self'; img-src 'self' data:; font-src 'self'; "
                "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
                "connect-src 'self'; frame-src 'none'; object-src 'none'; base-uri 'self'"
            )
        return response


class TurnstileSearchMiddleware:
    """Requires a valid challenge pass before an enabled search request."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """
        Keeps the next Django request handler.

        Called by: Django middleware setup
        """
        self.get_response = get_response

    def process_view(
        self, request: HttpRequest, view_func: object, view_args: object, view_kwargs: object
    ) -> HttpResponse | None:
        """
        Redirects unverified search GETs to the local challenge page.

        Called by: Django request handler
        """
        response = None
        if (
            settings.TURNSTILE_ENABLED
            and request.method == 'GET'
            and getattr(view_func, '__module__', '') == 'vivo_app.views'
            and getattr(view_func, '__name__', '') == 'search'
            and not challenge_passed(request)
        ):
            location = reverse('bot_detect_challenge') + '?' + urlencode({'dest': request.get_full_path()})
            response = HttpResponse(status=307)
            response['Location'] = location
        return response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Passes the request through to Django's next handler.

        Called by: Django middleware setup
        """
        return self.get_response(request)
