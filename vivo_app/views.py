"""Views for the VIVO Django application."""

import datetime
import json
import logging
import random
import re
import sys
from urllib.parse import quote_plus, urlencode

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .lib import version_helper
from .lib.assets import get_random_background_relpath
from .lib.bot_detect import SESSION_KEY, verify_token
from .lib.display import build_display_context, build_publications_context, get_type_for_id
from .lib.error_check import IntentionalErrorCheckError
from .lib.home import BookCover, get_book_cover_pages
from .lib.page_data import (
    get_bundle,
    get_home_data,
    get_organization_data,
    get_profile_data,
    get_response_data,
    get_search_data,
)
from .lib.page_rendering import data_unavailable, prepared_response, query_pairs, render_or_stub
from .lib.prepared_data import PageDataError
from .lib.source_formats import profile_json_data
from .lib.source_graph import graph_csv, graph_page_data, graph_subject_data, visualization_graph
from .lib.source_org_charts import publication_history_csv, publication_history_data, research_areas_data
from .lib.source_pages import facet_values_data, organization_publications_data, search_json_data
from .lib.source_requests import (
    document_key,
    document_key_from_url,
    image_key,
    image_path,
    read_source,
    source_origin,
    vitro_key,
)
from .lib.source_status import status_data
from .lib.source_teams import custom_organization_members
from .lib.version_helper import GatherCommitAndBranchData

logger = logging.getLogger(__name__)


def source_image(request: HttpRequest, filename: str) -> HttpResponse:
    """
    Returns an image from the selected live or recorded source.

    Called by: config.urls
    """
    try:
        if settings.PAGE_DATA_MODE not in {'live', 'replay'}:
            raise PageDataError('Source images require live or replay mode.')
        result = read_source(image_key('/' + filename), settings.PAGE_DATA_MODE)
        content_type = next((value for key, value in result.headers if key.lower() == 'content-type'), '')
        if content_type not in {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}:
            raise PageDataError('The image source returned an unsupported content type.')
        response = HttpResponse(result.body, content_type=content_type)
        response['X-Content-Type-Options'] = 'nosniff'
        return response
    except PageDataError as exc:
        return data_unavailable(exc)


def source_document(request: HttpRequest, filename: str) -> HttpResponse:
    """
    Serves one recorded or live PDF while keeping a source version redirect local.

    Called by: config.urls
    """
    try:
        if settings.PAGE_DATA_MODE not in {'live', 'replay'}:
            raise PageDataError('Source documents require live or replay mode.')
        key = document_key('/' + filename, tuple(query_pairs(request.GET)))
        result = read_source(key, settings.PAGE_DATA_MODE)
        headers = dict(result.headers)
        if result.status in {301, 302}:
            location = headers.get('location', '')
            target = document_key_from_url(location)
            redirect_url = '/source-documents' + target.path
            if target.query:
                redirect_url += '?' + urlencode(target.query)
            return HttpResponse(status=result.status, headers={'Location': redirect_url})
        if headers.get('content-type', '').split(';', 1)[0] != 'application/pdf' or not result.body.startswith(b'%PDF-'):
            raise PageDataError('The document source returned an unsupported PDF response.')
        return HttpResponse(result.body, content_type='application/pdf')
    except PageDataError as exc:
        return data_unavailable(exc)


# Standard application support endpoints
def error_check(request: HttpRequest) -> HttpResponse:
    """
    Raises an intentional exception in development to check administrator error reporting.

    Called by: config.urls
    """
    logger.debug('starting error_check(); request.method, ``%s``', request.method)
    logger.debug('settings.DEBUG, ``%s``', settings.DEBUG)
    if settings.DEBUG is True:
        logger.debug('triggering intentional exception')
        raise IntentionalErrorCheckError('Raising intentional exception to check email-admins-on-error functionality.')
    response: HttpResponse = HttpResponseNotFound(b'<div>404 / Not Found</div>')
    return response


def version(request: HttpRequest) -> HttpResponse:
    """
    Returns the Git branch and commit.

    Called by: config.urls
    """
    logger.debug('starting version()')
    request_started: datetime.datetime = datetime.datetime.now().astimezone()
    gatherer = GatherCommitAndBranchData()
    gatherer.gather()
    version_text: str = f'{gatherer.branch} {gatherer.commit}'
    context: dict[str, dict[str, str]] = version_helper.make_context(
        request,
        request_started,
        version_text,
    )
    output: str = json.dumps(context, sort_keys=True, indent=2)
    logger.debug('version output, ``%s``', output)
    response = HttpResponse(output.encode('utf-8'), content_type='application/json; charset=utf-8')
    return response


# Home and static pages
def home_index(request):
    """Render the home page."""
    alias_value: str | None = request.GET.get('alias')
    if alias_value:
        query: str = alias_value.replace('_', ' ')
        redirect_url: str = f'{reverse("search")}?q={quote_plus(query)}'
        return redirect(redirect_url)

    try:
        home_data = get_home_data(request.path_info, query_pairs(request.GET))
        if home_data is not None:
            backgrounds = home_data['backgrounds']
            if isinstance(backgrounds, list):
                home_data['hero_background_url'] = random.choice(backgrounds)
            return render(request, 'home/index.html', home_data)
    except PageDataError as exc:
        return data_unavailable(exc)

    hero_background_relpath: str = get_random_background_relpath()
    carousel_pages_raw: list[list[BookCover]] = get_book_cover_pages(page_size=4)
    placeholder_image: str = static('images/vivo_blank_profile.jpg')
    image_base_path: str = getattr(settings, 'BOOK_COVER_BASE_PATH', '') or ''

    book_covers_paginated: list[list[dict[str, str]]] = []
    for page in carousel_pages_raw:
        rendered_page: list[dict[str, str]] = []
        for cover in page:
            image_url: str = placeholder_image
            if image_base_path:
                image_url = f'{image_base_path.rstrip("/")}/{cover.image_filename}'
            rendered_page.append(
                {
                    'author_url': reverse('display_show', args=[cover.author_id]),
                    'title': cover.title,
                    'author_name': cover.author_name,
                    'image_url': image_url,
                }
            )
        book_covers_paginated.append(rendered_page)

    context: dict[str, object] = {
        'hero_background_relpath': hero_background_relpath,
        'book_covers_paginated': book_covers_paginated,
    }
    return render_or_stub(request, 'home/index.html', context)


def home_about(request):
    """Render the about page."""
    return render_or_stub(request, 'home/about.html')


def home_faq(request):
    """Render the FAQ page."""
    return render_or_stub(request, 'home/faq.html')


def home_help(request):
    """Render the help page."""
    return render_or_stub(request, 'home/help.html')


def home_history(request):
    """Render the history page."""
    return render_or_stub(request, 'home/history.html')


def home_publications(request):
    """Render the publications page."""
    return render_or_stub(request, 'home/publications.html')


def home_roadmap(request):
    """Render the roadmap page."""
    return render_or_stub(request, 'home/roadmap.html')


def home_terms(request):
    """Render the terms of use page."""
    return render_or_stub(request, 'home/terms.html')


# Additional home/legacy static pages
def home_brown(request):
    return render_or_stub(request, 'home/brown.html')


def home_help_viz(request):
    return render_or_stub(request, 'home/help_viz.html')


def home_status(request: HttpRequest) -> HttpResponse:
    """
    Reports whether the configured Solr index has searchable records.

    Called by: config.urls
    """
    mode = settings.PAGE_DATA_MODE
    if mode == 'prototype':
        return render_or_stub(request, 'home/status.html', context={})
    try:
        if mode == 'prepared':
            saved_response = get_response_data(request.path_info, query_pairs(request.GET))
            if saved_response is None:
                raise PageDataError('The status response is unavailable in prepared data.')
            return prepared_response(saved_response)
        return JsonResponse(status_data(mode))
    except PageDataError:
        return JsonResponse({'status': 'ERROR', 'message': 'The search status could not be checked.'}, status=500)


def home_brown_classic(request, name=None):
    query_fragment: str = ''
    if name:
        query_fragment = name
    elif request.GET.get('name'):
        query_fragment = request.GET.get('name')
    redirect_target: str = reverse('search')
    if query_fragment:
        formatted_query: str = query_fragment.replace('_', ' ')
        redirect_target = f'{redirect_target}?q={quote_plus(formatted_query)}'
    return redirect(redirect_target)


# Display functionality
def display_index(request):
    """Display index page."""
    return render_or_stub(request, 'display/index.html')


def display_show(request, id):
    """Display a single item.

    Behavior parity considerations:
    - If `?format=json` is given and the ID type is unknown, return just {"id": id}
      to preserve existing test expectations and scaffolding behavior.
    - For known types, build a minimal presenter-like context for progressive parity.
    """
    try:
        if request.GET.get('format') == 'json' or id.endswith('.json'):
            if settings.PAGE_DATA_MODE in {'live', 'replay'}:
                if any(key != 'format' or value != 'json' for key, value in query_pairs(request.GET)):
                    raise PageDataError('Profile JSON query options are unsupported.')
                return JsonResponse(profile_json_data(id.removesuffix('.json'), settings.PAGE_DATA_MODE))
            saved_response = get_response_data(request.path_info, query_pairs(request.GET))
            if saved_response is not None:
                return prepared_response(saved_response)
        else:
            if id.startswith(('org-', 'team-')):
                organization_data = get_organization_data(request.path_info, query_pairs(request.GET))
                if organization_data is not None:
                    return render(request, 'display/organization_data.html', {'organization': organization_data})
            profile_data = get_profile_data(request.path_info, query_pairs(request.GET))
            if profile_data is not None:
                return render(
                    request,
                    'display/show.html',
                    {
                        'profile': profile_data,
                        'back_to_search': request.session.get('prepared_search_url', '/search'),
                    },
                )
    except PageDataError as exc:
        return data_unavailable(exc)
    entity_type = get_type_for_id(id)

    # JSON response handling
    if request.GET.get('format') == 'json':
        if entity_type is None:
            return JsonResponse({'id': id})
        context = build_display_context(id, entity_type, request)
        return JsonResponse(context)

    # HTML response handling
    context = {'id': id} if entity_type is None else build_display_context(id, entity_type, request)
    return render_or_stub(request, 'display/show.html', context)


def display_publications(request, id):
    """Display publications for an item.

    Behavior: If `?format=json` is provided, return a JSON structure including
    a publications list. Otherwise render minimal HTML with the list.
    Unknown types return an empty list but still include the id.
    """
    entity_type = get_type_for_id(id)

    if request.GET.get('format') == 'json':
        context = build_publications_context(id, entity_type, request)
        return JsonResponse(context)

    context = build_publications_context(id, entity_type, request)
    return render_or_stub(request, 'display/publications.html', context)


def organization_publications_tsv(request: HttpRequest, id: str) -> HttpResponse:
    """
    Serves a source-backed organization publication download.

    Called by: config.urls
    """
    try:
        if settings.PAGE_DATA_MODE not in {'live', 'replay'}:
            saved = get_response_data(request.path_info, query_pairs(request.GET))
            if saved is not None:
                return prepared_response(saved)
            raise PageDataError('The organization publication download is unavailable.')
        if request.GET:
            raise PageDataError('Organization publication query options are unsupported.')
        body = organization_publications_data(
            id, settings.PAGE_DATA_MODE, extra_member_ids=custom_organization_members(id, settings.PAGE_DATA_MODE)
        )
        return HttpResponse(
            body.encode(),
            content_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{id}.tsv"'},
        )
    except PageDataError as exc:
        return data_unavailable(exc)


# Visualizations
def visualization_home(request, id):
    """Home for visualizations."""
    context = {'id': id}
    return render_or_stub(request, 'visualization/home.html', context)


def visualization_graph_json(request: HttpRequest, id: str, kind: str) -> HttpResponse:
    """
    Returns one unchanged graph object from a recorded or live visualization response.

    Called by: config.urls
    """
    try:
        if settings.PAGE_DATA_MODE not in {'live', 'replay'}:
            saved = get_response_data(request.path_info, query_pairs(request.GET))
            if saved is not None:
                return prepared_response(saved)
            raise PageDataError('This visualization is unavailable.')
        if request.GET:
            raise PageDataError('Visualization query options are unsupported.')
        return JsonResponse(visualization_graph(kind, id, settings.PAGE_DATA_MODE))
    except PageDataError as exc:
        return data_unavailable(exc)


def visualization_graph_csv(request: HttpRequest, id: str, kind: str) -> HttpResponse:
    """
    Serves the public graph CSV path from the same source graph as JSON and HTML.

    Called by: config.urls
    """
    try:
        if settings.PAGE_DATA_MODE not in {'live', 'replay'}:
            saved = get_response_data(request.path_info, query_pairs(request.GET))
            if saved is not None:
                return prepared_response(saved)
            raise PageDataError('This visualization download is unavailable.')
        if request.GET:
            raise PageDataError('Visualization query options are unsupported.')
        data = visualization_graph(kind, id, settings.PAGE_DATA_MODE)
        return HttpResponse(graph_csv(data, kind).encode(), content_type='text/plain; charset=utf-8')
    except PageDataError as exc:
        return data_unavailable(exc)


def visualization_coauthor(request, id):
    """Shows or downloads a source-backed coauthor network."""
    return visualization_network(request, id, 'coauthors')


def visualization_coauthor_treemap(request: HttpRequest, id: str) -> HttpResponse:
    """
    Renders a coauthor treemap from the same graph used by the network page.

    Called by: config.urls
    """
    try:
        if settings.PAGE_DATA_MODE == 'prototype':
            return render_or_stub(request, 'visualization/coauthor_treemap.html', {'id': id})
        if settings.PAGE_DATA_MODE not in {'live', 'replay'}:
            raise PageDataError('This visualization is unavailable.')
        pairs = query_pairs(request.GET)
        if len(pairs) > 1 or any(key != 'format' or value not in {'json', 'csv'} for key, value in pairs):
            raise PageDataError('Visualization query options are unsupported.')
        data = visualization_graph('coauthors', id, settings.PAGE_DATA_MODE)
        response_format = request.GET.get('format')
        if response_format == 'json':
            return JsonResponse(data)
        if response_format == 'csv':
            return HttpResponse(graph_csv(data, 'coauthors').encode(), content_type='text/plain; charset=utf-8')
        subject = graph_subject_data('coauthors', id, settings.PAGE_DATA_MODE)
        return render(
            request,
            'visualization/treemap_data.html',
            {'graph': graph_page_data(data, 'coauthors', id, subject)},
        )
    except PageDataError as exc:
        return data_unavailable(exc)


def visualization_collab(request, id):
    """Shows or downloads a source-backed collaborator network."""
    return visualization_network(request, id, 'collaborators')


def visualization_network(request: HttpRequest, identifier: str, kind: str) -> HttpResponse:
    """
    Serves the graph page and its JSON or CSV representation.

    Called by: visualization_coauthor(), visualization_collab()
    """
    try:
        if settings.PAGE_DATA_MODE == 'prototype':
            return render_or_stub(
                request,
                'visualization/coauthor.html' if kind == 'coauthors' else 'visualization/collab.html',
                {'id': identifier},
            )
        if settings.PAGE_DATA_MODE not in {'live', 'replay'}:
            raise PageDataError('This visualization is unavailable.')
        pairs = query_pairs(request.GET)
        if len(pairs) > 1 or any(
            (key == 'format' and value not in {'json', 'csv'})
            or (key == 'fit' and value != '1')
            or key not in {'format', 'fit'}
            for key, value in pairs
        ):
            raise PageDataError('Visualization query options are unsupported.')
        data = visualization_graph(kind, identifier, settings.PAGE_DATA_MODE)
        response_format = request.GET.get('format')
        if response_format == 'json':
            return JsonResponse(data)
        if response_format == 'csv':
            return HttpResponse(graph_csv(data, kind).encode(), content_type='text/plain; charset=utf-8')
        subject = graph_subject_data(kind, identifier, settings.PAGE_DATA_MODE)
        return render(
            request,
            'visualization/network_data.html',
            {'graph': graph_page_data(data, kind, identifier, subject), 'force_to_fit': request.GET.get('fit') == '1'},
        )
    except PageDataError as exc:
        return data_unavailable(exc)


def visualization_publications(request: HttpRequest, id: str, fmt: str = '') -> HttpResponse:
    """
    Serves an organization's publication timeline and its source-backed formats.

    Called by: config.urls
    """
    try:
        if settings.PAGE_DATA_MODE == 'prototype':
            return render_or_stub(request, 'visualization/publications.html', {'id': id})
        if settings.PAGE_DATA_MODE not in {'live', 'replay'}:
            saved = get_response_data(request.path_info, query_pairs(request.GET))
            if saved is not None:
                return prepared_response(saved)
            raise PageDataError('The publication chart is unavailable.')
        if id.startswith('team-') or fmt not in {'', 'json', 'csv'} or request.GET:
            raise PageDataError('The publication chart request is unsupported.')
        name, data = publication_history_data(id, settings.PAGE_DATA_MODE)
        if fmt == 'json':
            return JsonResponse(data)
        if fmt == 'csv':
            return HttpResponse(
                publication_history_csv(data).encode(),
                content_type='text/csv',
                headers={'Content-Disposition': f'attachment; filename="{id}.csv"'},
            )
        return render(request, 'visualization/publications_data.html', {'id': id, 'name': name, 'chart': data})
    except PageDataError as exc:
        return data_unavailable(exc)


def visualization_research(request: HttpRequest, id: str, fmt: str = '') -> HttpResponse:
    """
    Serves an organization's shared research areas and the underlying data.

    Called by: config.urls
    """
    try:
        if settings.PAGE_DATA_MODE == 'prototype':
            return render_or_stub(request, 'visualization/research.html', {'id': id})
        if settings.PAGE_DATA_MODE not in {'live', 'replay'}:
            saved = get_response_data(request.path_info, query_pairs(request.GET))
            if saved is not None:
                return prepared_response(saved)
            raise PageDataError('The research chart is unavailable.')
        if fmt not in {'', 'json'} or request.GET:
            raise PageDataError('The research chart request is unsupported.')
        name, data = research_areas_data(id, settings.PAGE_DATA_MODE)
        if fmt == 'json':
            return JsonResponse(data)
        return render(
            request,
            'visualization/research_data.html',
            {'id': id, 'name': name, 'chart': data, 'is_team': id.startswith('team-')},
        )
    except PageDataError as exc:
        return data_unavailable(exc)


# Edit functionality
@require_http_methods(['GET'])
def edit_profile(request, id):
    """Edit profile page."""
    context = {'id': id}
    return render_or_stub(request, 'edit/profile.html', context)


@require_http_methods(['POST'])
def overview_update(request, faculty_id):
    """Update overview information."""
    # TODO: Implement update logic
    return JsonResponse({'status': 'success'})


@require_http_methods(['POST'])
def research_area_add(request, faculty_id):
    """Add research area."""
    # TODO: Implement add logic
    return JsonResponse({'status': 'success'})


@require_http_methods(['POST'])
def research_area_delete(request, faculty_id):
    """Delete research area."""
    # TODO: Implement delete logic
    return JsonResponse({'status': 'success'})


@require_http_methods(['POST'])
def web_link_save(request, faculty_id):
    """Save web link."""
    # TODO: Implement save logic
    return JsonResponse({'status': 'success'})


@require_http_methods(['POST'])
def web_link_delete(request, faculty_id):
    """Delete web link."""
    # TODO: Implement delete logic
    return JsonResponse({'status': 'success'})


# Search
def search(request):
    """Handle search requests."""
    try:
        if request.GET.get('format') == 'json':
            if settings.PAGE_DATA_MODE in {'live', 'replay'}:
                pairs = [(key, value) for key, value in query_pairs(request.GET) if key != 'format']
                return JsonResponse(
                    search_json_data(pairs, settings.PAGE_DATA_MODE, request.build_absolute_uri('/')), safe=False
                )
            saved_response = get_response_data(request.path_info, query_pairs(request.GET))
            if saved_response is not None:
                return prepared_response(saved_response)
        else:
            search_data = get_search_data(request.path_info, query_pairs(request.GET))
            if search_data is not None:
                request.session['prepared_search_url'] = request.get_full_path()
                return render(request, 'search/results.html', search_data)
    except PageDataError as exc:
        return data_unavailable(exc)
    query = request.GET.get('q', '')
    context = {'query': query}
    return render_or_stub(request, 'search/results.html', context)


def advanced_search(request):
    """Handle advanced search requests."""
    return render_or_stub(request, 'search/advanced.html')


def search_facets(request):
    """Return search facets."""
    try:
        if settings.PAGE_DATA_MODE in {'live', 'replay'}:
            if 'f_name' not in request.GET:
                return JsonResponse(None, safe=False)
            return JsonResponse(facet_values_data(query_pairs(request.GET), settings.PAGE_DATA_MODE), safe=False)
        saved_response = get_response_data(request.path_info, query_pairs(request.GET))
        if saved_response is not None:
            return prepared_response(saved_response)
    except PageDataError as exc:
        return data_unavailable(exc)
    # TODO: Implement facet logic for authentic sources.
    return JsonResponse({'facets': {}})


def prepared_document(request: HttpRequest, filename: str) -> HttpResponse:
    """
    Serves a document only when its exact request exists in the selected bundle.

    Called by: config.urls
    """
    try:
        entry = get_response_data(request.path_info, query_pairs(request.GET))
        if entry is None:
            raise Http404('Prepared document is unavailable.')
        response = prepared_response(entry)
        response['X-Content-Type-Options'] = 'nosniff'
    except PageDataError as exc:
        response = data_unavailable(exc)
    return response


def prepared_asset(request: HttpRequest, name: str) -> HttpResponse:
    """
    Serves only assets explicitly included in the selected external bundle.

    Called by: config.urls
    """
    try:
        bundle = get_bundle()
        if bundle is None or name not in bundle.assets:
            raise Http404('Prepared asset is unavailable.')
        asset = bundle.assets[name]
        response = HttpResponse(asset.body, content_type=asset.content_type)
        response['X-Content-Type-Options'] = 'nosniff'
    except PageDataError as exc:
        response = data_unavailable(exc)
    return response


# Reports
def subject_lib_list(request):
    """List subject librarian reports."""
    return render_or_stub(request, 'reports/subject_lib_list.html')


def subject_lib(request, list_id):
    """View a specific subject librarian report."""
    context = {'list_id': list_id}
    return render_or_stub(request, 'reports/subject_lib.html', context)


# Bot detection
@require_http_methods(['GET', 'POST'])
def bot_detect_challenge(request: HttpRequest) -> HttpResponse:
    """
    Shows or verifies a Turnstile challenge when search protection is enabled.

    Called by: config.urls
    """
    if not settings.TURNSTILE_ENABLED:
        return HttpResponseNotFound()
    if not settings.CF_TURNSTILE_SITEKEY or not settings.CF_TURNSTILE_SECRET_KEY:
        return data_unavailable(PageDataError('The browser challenge is not configured.'))
    if request.method == 'POST':
        session = getattr(request, 'session', None)
        if not isinstance(session, SessionBase):
            return data_unavailable(PageDataError('The browser challenge cannot save a session.'))
        try:
            payload: object = json.loads(request.body) if len(request.body) <= 4096 else None
        except (ValueError, UnicodeError):
            payload = None
        token = payload.get('cf_turnstile_response') if isinstance(payload, dict) else None
        success = isinstance(token, str) and verify_token(token, request.META.get('REMOTE_ADDR', ''))
        if success:
            session[SESSION_KEY] = {
                'time': datetime.datetime.now(tz=datetime.UTC).isoformat(),
                'ip': request.META.get('REMOTE_ADDR', ''),
            }
        return JsonResponse({'success': success, 'redirect_for_challenge': bool(success)})
    return render(request, 'bot_detect/challenge.html', {'turnstile_sitekey': settings.CF_TURNSTILE_SITEKEY})


# Legacy VIVO URLs
def people(request):
    """Legacy people listing."""
    try:
        saved_response = get_response_data(request.path_info, query_pairs(request.GET))
        if saved_response is not None:
            return prepared_response(saved_response)
    except PageDataError as exc:
        return data_unavailable(exc)
    return render_or_stub(request, 'legacy/people.html')


def organizations(request):
    """Legacy organizations listing."""
    try:
        saved_response = get_response_data(request.path_info, query_pairs(request.GET))
        if saved_response is not None:
            return prepared_response(saved_response)
    except PageDataError as exc:
        return data_unavailable(exc)
    return render_or_stub(request, 'legacy/organizations.html')


def old_image(request: HttpRequest, id: str, file_name: str) -> HttpResponse:
    """
    Redirects a legacy image path to its current image location.

    Called by: config.urls
    """
    path = image_path(f'/file/{id}/{file_name}')
    if path is None:
        return page_not_found(request)
    try:
        if settings.PAGE_DATA_MODE == 'replay':
            location = '/source-images' + path
        else:
            location = source_origin('images') + path
    except PageDataError as exc:
        return data_unavailable(exc)
    return HttpResponse(status=301, headers={'Location': location})


# Legacy VIVO individual handlers
def individual_redirect(request: HttpRequest, id: str) -> HttpResponse:
    """
    Redirects a VIVO record to the selected HTML or original-data representation.

    Called by: config.urls
    """
    try:
        if settings.PAGE_DATA_MODE == 'prototype':
            return render_or_stub(request, 'vivo/individual_redirect.html', {'id': id})
        if settings.PAGE_DATA_MODE == 'prepared':
            saved_response = get_response_data(request.path_info, query_pairs(request.GET))
            if saved_response is not None:
                return prepared_response(saved_response)
        if re.fullmatch(r'[A-Za-z0-9_-]{1,80}', id) is None:
            raise PageDataError('The requested VIVO identifier is unsupported.')
        formats = {'application/json': 'jsonld', 'text/turtle': 'ttl', 'application/rdf+xml': 'rdf'}
        fmt = formats.get(request.META.get('HTTP_ACCEPT', ''))
        path = (
            reverse('individual_export_public', kwargs={'id': id, 'id2': id, 'fmt': fmt})
            if fmt
            else reverse('display_show_public', args=[id])
        )
        return HttpResponse(status=303, headers={'Location': request.build_absolute_uri(path)})
    except PageDataError as exc:
        return data_unavailable(exc)


def individual_export(request: HttpRequest, id: str, fmt: str, id2: str | None = None) -> HttpResponse:
    """
    Returns unchanged bytes from an original VIVO representation.

    Called by: config.urls
    """
    try:
        if settings.PAGE_DATA_MODE == 'prototype':
            payload = {'id': id, 'format': fmt}
            if id2 is not None:
                payload['id2'] = id2
            if fmt.lower() == 'json' or request.GET.get('format') == 'json':
                return JsonResponse(payload)
            return HttpResponse(f'Export for {id} as {fmt}'.encode(), content_type='text/plain')
        if settings.PAGE_DATA_MODE == 'prepared':
            saved_response = get_response_data(request.path_info, query_pairs(request.GET))
            if saved_response is not None:
                return prepared_response(saved_response)
            raise PageDataError('The VIVO representation is unavailable.')
        if settings.PAGE_DATA_MODE not in {'live', 'replay'} or id2 != id or request.GET:
            raise PageDataError('The requested VIVO representation is unsupported.')
        key = vitro_key(id, fmt)
        response = read_source(key, settings.PAGE_DATA_MODE)
        content_type = {'jsonld': 'application/json', 'ttl': 'text/turtle', 'rdf': 'application/rdf+xml'}[fmt]
        result = HttpResponse(response.body, status=response.status, content_type=content_type + '; charset=utf-8')
        result['X-Content-Type-Options'] = 'nosniff'
        return result
    except PageDataError as exc:
        return data_unavailable(exc)


# Editor fast search (de-prioritized functionality; stub only)
@require_http_methods(['GET'])
def edit_fast_search(request):
    query = request.GET.get('q', '')
    return JsonResponse({'query': query, 'results': []})


def page_not_found(request, exception=None, template_name='404.html'):
    """Custom 404 page handler."""
    logger.warning('404 Not Found: %s', request.path, extra={'status_code': 404, 'request': request}, exc_info=exception)
    return render_or_stub(request, template_name, status=404)


def server_error(request, template_name='500.html'):
    """Custom 500 page handler."""
    logger.error(
        '500 Internal Server Error: %s',
        request.path,
        extra={'status_code': 500, 'request': request},
        exc_info=sys.exception(),
    )
    return render_or_stub(request, template_name, status=500)


# Set up default error handlers
handler404 = page_not_found
handler500 = server_error
