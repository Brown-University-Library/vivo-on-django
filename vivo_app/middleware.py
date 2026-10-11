"""
Checks source configuration and protects configured search access.
"""

from collections.abc import Callable
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import reverse

from vivo_app.lib.bot_detect import challenge_passed
from vivo_app.lib.page_data import check_source_configuration
from vivo_app.lib.page_errors import PageDataError
from vivo_app.lib.page_rendering import data_unavailable


class SourceDataMiddleware:
    """Checks source configuration and rejects unsupported application handlers."""

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
        Preserves unavailable responses for unsupported application handlers.

        Called by: Django request handler
        """
        supported = {
            'advanced_search',
            'bot_detect_challenge',
            'display_index',
            'display_show',
            'error_check',
            'faculty_service_redirect',
            'home_about',
            'home_brown',
            'home_faq',
            'home_help',
            'home_help_viz',
            'home_history',
            'home_index',
            'home_publications',
            'home_roadmap',
            'home_status',
            'home_terms',
            'individual_export',
            'individual_redirect',
            'old_image',
            'organization_publications_tsv',
            'organizations',
            'original_document',
            'people',
            'search',
            'search_facets',
            'source_document',
            'source_image',
            'subject_lib_list',
            'version',
            'visualization_coauthor',
            'visualization_coauthor_treemap',
            'visualization_collab',
            'visualization_graph_csv',
            'visualization_graph_json',
            'visualization_publications',
            'visualization_research',
        }
        response = None
        if getattr(view_func, '__module__', '') == 'vivo_app.views' and getattr(view_func, '__name__', '') not in supported:
            response = HttpResponse(
                b'This endpoint is not connected to source data yet.', status=503, content_type='text/plain'
            )
        return response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Checks required source configuration before dispatching a request.

        Called by: Django request handler
        """
        try:
            check_source_configuration()
        except PageDataError as exc:
            response = data_unavailable(exc)
        else:
            response = self.get_response(request)
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
