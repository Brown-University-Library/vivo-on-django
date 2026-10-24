"""Views for the VIVO Django application."""

import datetime
import json
import logging
import random
import sys
from urllib.parse import quote, quote_plus, urlencode

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.core.exceptions import BadRequest, SuspiciousOperation
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    HttpResponseNotFound,
    JsonResponse,
    StreamingHttpResponse,
)
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.cache import add_never_cache_headers
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .lib import version_helper
from .lib.advanced_search import advanced_search_query
from .lib.assets import get_random_background_relpath
from .lib.bot_detect import SESSION_KEY, verify_token
from .lib.display_cache import cached_display
from .lib.display_exports import export_request
from .lib.display_jsonld_cache import cached_display_data
from .lib.error_check import IntentionalErrorCheckError
from .lib.organization_chart_cache import cached_chart
from .lib.page_data import (
    get_home_data,
    get_search_data,
)
from .lib.page_errors import InvalidDocumentError, MissingRecordError, PageDataError, SourceTimeoutError
from .lib.page_rendering import data_unavailable, query_pairs, render_or_stub, valid_format_query
from .lib.profile_navigation import profile_search_return
from .lib.report_cache import cached_report
from .lib.reports import ReportError, load_reports, rails_integer, report_access
from .lib.search_errors import ReferenceSearchError
from .lib.source_documents import document_response
from .lib.source_formats import organization_json_data, profile_json_data, profile_json_text, raw_record_json_data
from .lib.source_graph import graph_csv, graph_page_data, graph_subject_data, visualization_graph
from .lib.source_media import cached_media
from .lib.source_org_charts import publication_history_csv, publication_history_data, research_areas_data
from .lib.source_pages import facet_values_data, organization_publications_data, search_json_data
from .lib.source_representations import cached_representation
from .lib.source_requests import (
    document_key,
    document_key_from_url,
    image_key,
    image_path,
    read_source,
    source_origin,
    valid_profile_identifier,
)
from .lib.source_status import status_data, status_error_data
from .lib.source_teams import custom_organization_members
from .lib.source_types import SourceResponse
from .lib.version_helper import GatherCommitAndBranchData

logger = logging.getLogger(__name__)


@never_cache
@require_http_methods(['GET', 'HEAD'])
def source_image(request: HttpRequest, filename: str) -> HttpResponse:
    """
    Returns an image from the configured source.

    Called by: config.urls
    """
    try:
        key = image_key('/' + filename)
    except PageDataError:
        return HttpResponseNotFound(b'Image not found.', content_type='text/plain')
    try:
        result = cached_media(key, read_source)
        if result.status == 404:
            return HttpResponseNotFound(b'Image not found.', content_type='text/plain')
        content_type = dict(result.headers)['content-type']
        response = HttpResponse(result.body, content_type=content_type)
        response['Content-Length'] = str(len(result.body))
        if request.method == 'HEAD':
            response.content = b''
        response['X-Content-Type-Options'] = 'nosniff'
        return response
    except PageDataError as exc:
        return data_unavailable(exc)


@never_cache
@require_http_methods(['GET', 'HEAD'])
def source_document(request: HttpRequest, filename: str) -> HttpResponse | StreamingHttpResponse:
    """
    Serves one configured CV while keeping a source version redirect local.

    Called by: config.urls, original_document()
    """
    try:
        document_key('/' + filename)
    except PageDataError:
        return HttpResponseNotFound(b'Document not found.', content_type='text/plain')
    try:
        key = document_key('/' + filename, tuple(query_pairs(request.GET, {'dt'})))
    except PageDataError:
        return HttpResponseBadRequest(b'Invalid document version.', content_type='text/plain; charset=utf-8')
    try:
        result = cached_media(key, read_source)
        if result.status == 404:
            return HttpResponseNotFound(b'Document not found.', content_type='text/plain')
        headers = dict(result.headers)
        if result.status in {301, 302}:
            location = headers.get('location', '')
            target = document_key_from_url(location)
            redirect_url = reverse('source_document', kwargs={'filename': target.path.lstrip('/')})
            if target.query:
                redirect_url += '?' + urlencode(target.query)
            return HttpResponse(status=result.status, headers={'Location': redirect_url})
        return document_response(request, result.body)
    except InvalidDocumentError:
        logger.warning('cv_pdf_validation_failed: filename, ``%s``', filename)
        return render(request, 'documents/unavailable.html', status=404)
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
    context: dict[str, dict[str, str]] = version_helper.make_context(request, request_started, version_text)
    context['response']['loaded_version'] = version_helper.LOADED_VERSION
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
        home_data = get_home_data(request.path_info, [])
        backgrounds = home_data['backgrounds']
        if isinstance(backgrounds, list):
            home_data['hero_background_url'] = random.choice(backgrounds)
        return render(request, 'home/index.html', home_data)
    except PageDataError as exc:
        return data_unavailable(exc)


def home_about(request: HttpRequest) -> HttpResponse:
    """
    Renders the About page with the public site's shared presentation.

    Called by: config.urls urlpatterns
    """
    return render_or_stub(request, 'home/about.html', {'source_page_styles': True})


def home_faq(request: HttpRequest) -> HttpResponse:
    """
    Renders the FAQ page with the public site's shared presentation.

    Called by: config.urls urlpatterns
    """
    return render_or_stub(request, 'home/faq.html', {'source_page_styles': True})


def home_help(request: HttpRequest) -> HttpResponse:
    """
    Renders the Help page with the public site's shared presentation.

    Called by: config.urls urlpatterns
    """
    return render_or_stub(request, 'home/help.html', {'source_page_styles': True})


def home_history(request: HttpRequest) -> HttpResponse:
    """
    Renders the history page with the public site's shared presentation.

    Called by: config.urls urlpatterns
    """
    return render_or_stub(request, 'home/history.html', {'source_page_styles': True})


def home_publications(request: HttpRequest) -> HttpResponse:
    """
    Renders the publication help page with the public site's shared presentation.

    Called by: config.urls urlpatterns
    """
    return render_or_stub(request, 'home/publications.html', {'source_page_styles': True})


def home_roadmap(request: HttpRequest) -> HttpResponse:
    """
    Renders the roadmap page with the public site's shared presentation.

    Called by: config.urls urlpatterns
    """
    return render_or_stub(request, 'home/roadmap.html', {'source_page_styles': True})


def home_terms(request: HttpRequest) -> HttpResponse:
    """
    Renders the terms of use page with the public site's shared presentation.

    Called by: config.urls urlpatterns
    """
    return render_or_stub(request, 'home/terms.html', {'source_page_styles': True})


# Additional home/legacy static pages
def home_brown(request: HttpRequest) -> HttpResponse:
    """
    Renders the institution information page with the public site's shared presentation.

    Called by: config.urls urlpatterns
    """
    return render_or_stub(request, 'home/brown.html', {'source_page_styles': True})


def home_help_viz(request: HttpRequest) -> HttpResponse:
    """
    Renders the visualization help page with the public site's shared presentation.

    Called by: config.urls urlpatterns
    """
    return render_or_stub(request, 'home/help_viz.html', {'source_page_styles': True})


def home_status(request: HttpRequest) -> HttpResponse:
    """
    Reports whether the configured Solr index has searchable records.

    Called by: config.urls
    """
    try:
        return JsonResponse(status_data())
    except Exception as exc:
        error_data = status_error_data(exc)
        logger.exception(
            'status_check_failed: message, ``%s``; error_type, ``%s``',
            error_data['message'],
            type(exc).__name__,
            exc_info=False,
        )
        return JsonResponse(error_data, status=500)


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
    return redirect(reverse('search').rstrip('/'))


def display_show(request: HttpRequest, id: str) -> HttpResponse:
    """
    Displays a record or returns the shared error page after a source failure.

    Called by: config.urls
    """
    try:
        base, _, suffix = id.rpartition('.')
        identifier = base if suffix in {'csv', 'xml', 'json', 'json_txt'} else id
        if not valid_profile_identifier(identifier):
            return page_not_found(request)
        ## Only format selects a display representation; other query parameters are ignored.
        pairs = [(key, value) for key, value in query_pairs(request.GET) if key == 'format']
        query_format = request.GET.get('format')
        export = export_request(id, query_format if isinstance(query_format, str) else None)
        if export is not None:
            if request.method not in {'GET', 'HEAD'}:
                return HttpResponseNotAllowed(['GET', 'HEAD'])
            identifier, fmt = export
            bundle = cached_display(identifier)
            download = bundle.csv if fmt == 'csv' else bundle.xml
            response = HttpResponse(download.body, content_type=download.content_type)
            response['Content-Disposition'] = (
                f'attachment; filename="{download.filename}"; filename*=UTF-8\'\'{download.filename}'
            )
            response['X-Content-Type-Options'] = 'nosniff'
            return response
        suffix_format = 'json_txt' if id.endswith('.json_txt') else 'json' if id.endswith('.json') else None
        if suffix_format is not None and any(value != suffix_format for _, value in pairs):
            return HttpResponseBadRequest(b'Unsupported display format.', content_type='text/plain; charset=utf-8')
        if request.GET.get('format') == 'json_txt' or id.endswith('.json_txt'):
            if pairs and pairs != [('format', 'json_txt')]:
                return HttpResponseBadRequest(b'Unsupported display format.', content_type='text/plain; charset=utf-8')
            return JsonResponse(raw_record_json_data(id.removesuffix('.json_txt')))
        elif request.GET.get('format') == 'json' or id.endswith('.json'):
            if any(value != 'json' for _, value in pairs):
                return HttpResponseBadRequest(b'Unsupported display format.', content_type='text/plain; charset=utf-8')
            identifier = id.removesuffix('.json')
            if identifier.startswith('org-'):
                return JsonResponse(
                    organization_json_data(identifier, extra_member_ids=custom_organization_members(identifier))
                )
            return HttpResponse(
                profile_json_text(profile_json_data(identifier)).encode('utf-8'),
                content_type='application/json; charset=utf-8',
            )
        else:
            if pairs:
                return HttpResponseBadRequest(b'Unsupported display format.', content_type='text/plain; charset=utf-8')
            display_data = cached_display_data(request.path_info, [], request.method)
            if isinstance(display_data, SourceResponse):
                response = HttpResponse(
                    display_data.body, status=display_data.status, content_type='application/json; charset=utf-8'
                )
                response['X-Content-Type-Options'] = 'nosniff'
                add_never_cache_headers(response)
                return response
            context = dict(display_data.context)
            if 'profile' in context:
                context['back_to_search'] = profile_search_return(request)
            return render(request, display_data.template_name, context)
    except MissingRecordError:
        return render(request, '404.html', {'hero_background_relpath': get_random_background_relpath()}, status=404)
    except SourceTimeoutError as exc:
        logger.warning('Display source request timed out; id, ``%s``; reason, ``%s``', id, exc)
        response = render(
            request,
            'search/error.html',
            {'hero_background_relpath': get_random_background_relpath(), 'temporarily_unavailable': True},
            status=503,
        )
        response['Retry-After'] = '60'
        add_never_cache_headers(response)
        request.META['vivo.source_timeout'] = True
        return response
    except (BadRequest, SuspiciousOperation):
        raise
    except Exception:
        logger.exception('Could not render display record; id, ``%s``', id)
        return render(request, 'search/error.html', {'hero_background_relpath': get_random_background_relpath()}, status=500)


def display_publications(request: HttpRequest, id: str) -> HttpResponse:
    """
    Preserves the unavailable response for this unsupported public route.

    Called by: config.urls
    """
    return HttpResponse(b'This endpoint is not connected to source data yet.', status=503, content_type='text/plain')


def organization_publications_tsv(request: HttpRequest, id: str) -> HttpResponse:
    """
    Serves a source-backed organization publication download.

    Called by: config.urls
    """
    try:
        if request.GET:
            raise PageDataError('Organization publication query options are unsupported.')
        body = organization_publications_data(id, extra_member_ids=custom_organization_members(id))
        return HttpResponse(
            body.encode(),
            content_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{id}.tsv"; filename*=UTF-8\'\'{id}.tsv'},
        )
    except PageDataError as exc:
        return data_unavailable(exc)


# Visualizations
def visualization_home(request: HttpRequest, id: str) -> HttpResponse:
    """
    Preserves the unavailable response for this unsupported public route.

    Called by: config.urls
    """
    return HttpResponse(b'This endpoint is not connected to source data yet.', status=503, content_type='text/plain')


@require_http_methods(['GET', 'HEAD'])
def visualization_graph_json(request: HttpRequest, id: str, kind: str) -> HttpResponse:
    """
    Returns one unchanged graph object from a configured visualization response.

    Called by: config.urls
    """
    if not valid_profile_identifier(id):
        return page_not_found(request)
    if not valid_format_query(request.GET, 'json'):
        return HttpResponseBadRequest(b'Unsupported visualization format.', content_type='text/plain; charset=utf-8')
    try:
        return HttpResponse(
            profile_json_text(visualization_graph(kind, id)).encode('utf-8'), content_type='application/json; charset=utf-8'
        )
    except PageDataError as exc:
        return data_unavailable(exc)


@require_http_methods(['GET', 'HEAD'])
def visualization_graph_csv(request: HttpRequest, id: str, kind: str) -> HttpResponse:
    """
    Serves the public graph CSV path from the same source graph as JSON and HTML.

    Called by: config.urls
    """
    if not valid_profile_identifier(id):
        return page_not_found(request)
    if not valid_format_query(request.GET, 'csv'):
        return HttpResponseBadRequest(b'Unsupported visualization format.', content_type='text/plain; charset=utf-8')
    try:
        data = visualization_graph(kind, id)
        return HttpResponse(graph_csv(data, kind).encode(), content_type='text/plain; charset=utf-8')
    except PageDataError as exc:
        return data_unavailable(exc)


def visualization_coauthor(request, id):
    """Shows or downloads a source-backed coauthor network."""
    return visualization_network(request, id, 'coauthors')


@require_http_methods(['GET', 'HEAD'])
def visualization_coauthor_treemap(request: HttpRequest, id: str) -> HttpResponse:
    """
    Renders a coauthor treemap from the same graph used by the network page.

    Called by: config.urls
    """
    if not valid_profile_identifier(id):
        return page_not_found(request)
    pairs = query_pairs(request.GET, {'format'})
    if len(pairs) > 1 or any(value not in {'json', 'csv'} for _, value in pairs):
        return HttpResponseBadRequest(b'Unsupported visualization format.', content_type='text/plain; charset=utf-8')
    try:
        response_format = request.GET.get('format')
        subject = graph_subject_data('coauthors', id) if response_format is None else None
        data = visualization_graph('coauthors', id)
        if response_format == 'json':
            return HttpResponse(profile_json_text(data).encode('utf-8'), content_type='application/json; charset=utf-8')
        if response_format == 'csv':
            return HttpResponse(graph_csv(data, 'coauthors').encode(), content_type='text/plain; charset=utf-8')
        return render(request, 'visualization/treemap_data.html', {'graph': graph_page_data(data, 'coauthors', id, subject)})
    except MissingRecordError:
        return page_not_found(request)
    except PageDataError as exc:
        return data_unavailable(exc)


def visualization_collab(request, id):
    """Shows or downloads a source-backed collaborator network."""
    return visualization_network(request, id, 'collaborators')


@require_http_methods(['GET', 'HEAD'])
def visualization_network(request: HttpRequest, identifier: str, kind: str) -> HttpResponse:
    """
    Serves the graph page and its JSON or CSV representation.

    Called by: visualization_coauthor(), visualization_collab()
    """
    if not valid_profile_identifier(identifier):
        return page_not_found(request)
    pairs = query_pairs(request.GET, {'format', 'fit'})
    if len(pairs) > 1 or any(
        (key == 'format' and value not in {'json', 'csv'}) or (key == 'fit' and value != '1') for key, value in pairs
    ):
        return HttpResponseBadRequest(b'Unsupported visualization options.', content_type='text/plain; charset=utf-8')
    try:
        response_format = request.GET.get('format')
        subject = graph_subject_data(kind, identifier) if response_format is None else None
        data = visualization_graph(kind, identifier)
        if response_format == 'json':
            return HttpResponse(profile_json_text(data).encode('utf-8'), content_type='application/json; charset=utf-8')
        if response_format == 'csv':
            return HttpResponse(graph_csv(data, kind).encode(), content_type='text/plain; charset=utf-8')
        return render(
            request,
            'visualization/network_data.html',
            {'graph': graph_page_data(data, kind, identifier, subject), 'force_to_fit': request.GET.get('fit') == '1'},
        )
    except MissingRecordError:
        return page_not_found(request)
    except PageDataError as exc:
        return data_unavailable(exc)


@never_cache
@require_http_methods(['GET', 'HEAD'])
def visualization_publications(request: HttpRequest, id: str, fmt: str = '') -> HttpResponse:
    """
    Serves an organization's publication timeline and its source-backed formats.

    Called by: config.urls
    """
    if not valid_profile_identifier(id) or id.startswith('team-') or fmt not in {'', 'json', 'csv'}:
        return page_not_found(request)
    if not valid_format_query(request.GET, fmt):
        return HttpResponseBadRequest(b'Unsupported publication chart format.', content_type='text/plain; charset=utf-8')
    try:
        name, data = cached_chart(id, 'publications', publication_history_data)
        if fmt == 'json':
            return HttpResponse(profile_json_text(data).encode('utf-8'), content_type='application/json; charset=utf-8')
        if fmt == 'csv':
            return HttpResponse(
                publication_history_csv(data).encode(),
                content_type='text/csv',
                headers={'Content-Disposition': f'attachment; filename="{id}.csv"; filename*=UTF-8\'\'{id}.csv'},
            )
        return render(request, 'visualization/publications_data.html', {'id': id, 'name': name, 'chart': data})
    except MissingRecordError:
        return page_not_found(request)
    except PageDataError as exc:
        return data_unavailable(exc)


@never_cache
@require_http_methods(['GET', 'HEAD'])
def visualization_research(request: HttpRequest, id: str, fmt: str = '') -> HttpResponse:
    """
    Serves an organization's shared research areas and the underlying data.

    Called by: config.urls
    """
    if not valid_profile_identifier(id) or fmt not in {'', 'json'}:
        return page_not_found(request)
    if not valid_format_query(request.GET, fmt):
        return HttpResponseBadRequest(b'Unsupported research chart format.', content_type='text/plain; charset=utf-8')
    try:
        name, data = cached_chart(id, 'research', research_areas_data)
        if fmt == 'json':
            return HttpResponse(profile_json_text(data).encode('utf-8'), content_type='application/json; charset=utf-8')
        return render(
            request,
            'visualization/research_data.html',
            {'id': id, 'name': name, 'chart': data, 'is_team': id.startswith('team-')},
        )
    except MissingRecordError:
        return page_not_found(request)
    except PageDataError as exc:
        return data_unavailable(exc)


# Search
def search(request: HttpRequest) -> HttpResponse:
    """
    Shows search results or the reference response for a known filter failure.

    Called by: config.urls
    """
    if 'querytext' in request.GET:
        destination = reverse('search').rstrip('/') + '?' + urlencode({'q': request.GET['querytext']}, quote_via=quote)
        return redirect(destination)
    try:
        if request.GET.get('format') == 'json':
            pairs = [(key, value) for key, value in query_pairs(request.GET) if key != 'format']
            site_origin = request.build_absolute_uri(reverse('home')) or ''
            data = search_json_data(pairs, site_origin)
            return HttpResponse(profile_json_text(data).encode('utf-8'), content_type='application/json; charset=utf-8')
        else:
            search_data = get_search_data(request.path_info, query_pairs(request.GET))
            session = getattr(request, 'session', None)
            if isinstance(session, SessionBase):
                session['search_url'] = request.get_full_path()
            return render(request, 'search/results.html', search_data)
    except ReferenceSearchError:
        logger.error('reference_search_filter_error')
        if request.GET.get('format') == 'json':
            return JsonResponse(
                {'status': 500, 'error': 'Internal Server Error'},
                status=500,
                content_type='application/json; charset=UTF-8',
                json_dumps_params={'separators': (',', ':')},
            )
        return render(request, 'search/error.html', {'hero_background_relpath': get_random_background_relpath()}, status=500)
    except PageDataError as exc:
        return data_unavailable(exc)


def advanced_search(request: HttpRequest) -> HttpResponse:
    """
    Shows the public advanced search form or redirects its fielded query.

    Called by: config.urls
    """
    name_value = request.GET.get('name_t', '')
    title_value = request.GET.get('title_t', '')
    department_value = request.GET.get('department_t', '')
    name = name_value if isinstance(name_value, str) else ''
    title = title_value if isinstance(title_value, str) else ''
    department = department_value if isinstance(department_value, str) else ''
    if request.GET.get('search') == 'true':
        try:
            query = advanced_search_query(title, name, department, url_encoded=True)
        except PageDataError as exc:
            return data_unavailable(exc)
        if query:
            return redirect(reverse('search').rstrip('/') + '?q=' + query)
    return render(request, 'search/advanced.html', {'name': name, 'title': title})


def search_facets(request: HttpRequest) -> HttpResponse:
    """
    Returns search facets or the reference null response for a known filter failure.

    Called by: config.urls
    """
    try:
        if 'f_name' not in request.GET:
            return JsonResponse(None, safe=False)
        values = facet_values_data(query_pairs(request.GET))
        return HttpResponse(profile_json_text(values).encode('utf-8'), content_type='application/json; charset=utf-8')
    except ReferenceSearchError:
        logger.error('reference_search_filter_error')
        return JsonResponse(None, safe=False, status=500, content_type='application/json; charset=utf-8')
    except PageDataError as exc:
        return data_unavailable(exc)


def original_document(request: HttpRequest, filename: str) -> HttpResponse | StreamingHttpResponse:
    """
    Serves the original public document path through the configured document source.

    Called by: config.urls
    """
    return source_document(request, 'docs/' + filename)


# Reports
@never_cache
@require_http_methods(['GET', 'HEAD'])
def subject_lib_list(request: HttpRequest) -> HttpResponse:
    """
    Shows the report definitions after checking trusted server access.

    Called by: config.urls report-list routes
    """
    try:
        if not report_access(request.META):
            response = HttpResponse(b'Report access requires Shibboleth.', status=403, content_type='text/plain')
        else:
            response = render(request, 'reports/subject_lib_list.html', {'reports': load_reports()})
    except ReportError as exc:
        logger.error('report_error, ``%s``', exc)
        response = render(
            request, 'reports/error.html', {'hero_background_relpath': get_random_background_relpath()}, status=500
        )
    return response


@never_cache
@require_http_methods(['GET', 'HEAD'])
def subject_lib(request: HttpRequest, list_id: str, fmt: str | None = None) -> HttpResponse:
    """
    Returns a protected report attachment using the shared completed-report cache.

    Called by: config.urls
    """
    try:
        if not report_access(request.META):
            response = HttpResponse(b'Report access requires Shibboleth.', status=403, content_type='text/plain')
        else:
            identifier = rails_integer(list_id)
            report = next((report for report in load_reports() if report.id == identifier), None)
            if report is None:
                response = render(
                    request, '404.html', {'hero_background_relpath': get_random_background_relpath()}, status=404
                )
            else:
                bundle = cached_report(report)
                download = bundle.xml if (fmt or request.GET.get('format')) == 'xml' else bundle.csv
                response = HttpResponse(download.body, content_type=download.content_type)
                response['Content-Disposition'] = f'attachment; filename="{download.filename}"'
                response['X-Content-Type-Options'] = 'nosniff'
    except ReportError as exc:
        logger.error('report_error, ``%s``', exc)
        response = render(
            request, 'reports/error.html', {'hero_background_relpath': get_random_background_relpath()}, status=500
        )
    return response


# Bot detection
@require_http_methods(['GET', 'POST'])
def bot_detect_challenge(request: HttpRequest) -> HttpResponse:
    """
    Shows or verifies a Turnstile challenge when configured.

    Called by: config.urls
    """
    configured: bool = bool(settings.CF_TURNSTILE_SITEKEY and settings.CF_TURNSTILE_SECRET_KEY)
    if not settings.TURNSTILE_ENABLED and not configured:
        return HttpResponseNotFound()
    if not configured:
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
    return render(
        request,
        'bot_detect/challenge.html',
        {'turnstile_sitekey': settings.CF_TURNSTILE_SITEKEY, 'source_page_styles': True},
    )


# Legacy VIVO URLs
def people(request: HttpRequest) -> HttpResponse:
    """
    Redirects the legacy people entry to its fixed search filter.

    Called by: config.urls
    """
    search_url = request.build_absolute_uri(reverse('search').rstrip('/'))
    if search_url is None:
        return data_unavailable(PageDataError('The search destination is unavailable.'))
    destination = search_url + '?fq=record_type|PEOPLE'
    return HttpResponse(status=302, headers={'Location': destination})


def organizations(request: HttpRequest) -> HttpResponse:
    """
    Redirects the legacy organization entry to its fixed search filter.

    Called by: config.urls
    """
    search_url = request.build_absolute_uri(reverse('search').rstrip('/'))
    if search_url is None:
        return data_unavailable(PageDataError('The search destination is unavailable.'))
    destination = search_url + '?fq=record_type|ORGANIZATION'
    return HttpResponse(status=302, headers={'Location': destination})


def old_image(request: HttpRequest, id: str, file_name: str) -> HttpResponse:
    """
    Redirects a legacy image path to its current image location.

    Called by: config.urls
    """
    path = image_path(f'/file/{id}/{file_name}')
    if path is None:
        return page_not_found(request)
    try:
        location = source_origin('images') + path
    except PageDataError as exc:
        return data_unavailable(exc)
    return HttpResponse(status=301, headers={'Location': location})


# Existing public data service
@require_http_methods(['GET', 'HEAD'])
def faculty_service_redirect(request: HttpRequest, id: str) -> HttpResponse:
    """
    Redirects faculty data requests to the existing service at the site root.

    Called by: config.urls
    """
    destination = f'/services/data/v1/faculty/{quote(id, safe="")}/'
    query = request.META.get('QUERY_STRING', '')
    if query:
        destination += '?' + query
    response = HttpResponse(status=301, headers={'Location': request.build_absolute_uri(destination)})
    response['Access-Control-Allow-Origin'] = '*'
    return response


# Legacy VIVO individual handlers
@require_http_methods(['GET', 'HEAD'])
def individual_redirect(request: HttpRequest, id: str) -> HttpResponse:
    """
    Redirects a VIVO record to the selected HTML or original-data representation.

    Called by: config.urls
    """
    if not valid_profile_identifier(id):
        return page_not_found(request)
    formats = {'application/json': 'jsonld', 'text/turtle': 'ttl', 'application/rdf+xml': 'rdf'}
    fmt = formats.get(request.META.get('HTTP_ACCEPT', ''))
    path = (
        reverse('individual_export_public', kwargs={'id': id, 'id2': id, 'fmt': fmt})
        if fmt
        else reverse('display_show_public', args=[id])
    )
    return HttpResponse(status=303, headers={'Location': request.build_absolute_uri(path)})


@never_cache
@require_http_methods(['GET', 'HEAD'])
def individual_export(request: HttpRequest, id: str, fmt: str, id2: str | None = None) -> HttpResponse:
    """
    Returns unchanged bytes from an original VIVO representation.

    Called by: config.urls
    """
    if not valid_profile_identifier(id) or id2 != id or fmt not in {'jsonld', 'ttl', 'rdf'}:
        return page_not_found(request)
    if not valid_format_query(request.GET, fmt):
        return HttpResponseBadRequest(b'Unsupported download format.', content_type='text/plain; charset=utf-8')
    try:
        response = cached_representation(id, fmt, read_source, request.method)
        content_type = {'jsonld': 'application/json', 'ttl': 'text/turtle', 'rdf': 'application/rdf+xml'}[fmt]
        result = HttpResponse(response.body, status=response.status, content_type=content_type + '; charset=utf-8')
        result['X-Content-Type-Options'] = 'nosniff'
    except SourceTimeoutError as exc:
        logger.warning('VIVO download timed out; id, ``%s``; fmt, ``%s``; reason, ``%s``', id, fmt, exc)
        result = HttpResponse(
            b'Download temporarily unavailable. Please try again in a minute.',
            status=503,
            content_type='text/plain; charset=utf-8',
        )
        result['Retry-After'] = '60'
        request.META['vivo.source_timeout'] = True
    except PageDataError as exc:
        result = data_unavailable(exc)
    return result


def page_not_found(request, exception=None, template_name='404.html'):
    """Custom 404 page handler."""
    logger.warning('404 Not Found: %s', request.path, extra={'status_code': 404, 'request': request}, exc_info=exception)
    return render_or_stub(
        request, template_name, context={'hero_background_relpath': get_random_background_relpath()}, status=404
    )


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
