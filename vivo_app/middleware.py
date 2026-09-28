"""
Keeps prepared and replay browser loads local.
"""

from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse

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
            'search',
            'display_show',
            'search_facets',
            'people',
            'organizations',
            'individual_redirect',
            'prepared_asset',
            'prepared_document',
            'source_image',
            'source_document',
            'error_check',
            'version',
        }
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
