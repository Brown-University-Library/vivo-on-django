"""Views for the VIVO Django application."""
from urllib.parse import quote_plus

from django.conf import settings
from django.shortcuts import redirect, render
from django.http import JsonResponse, HttpResponse, HttpRequest, Http404
from django.template.loader import get_template
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.http import require_http_methods
import logging
from .lib.display import get_type_for_id, build_display_context, build_publications_context
from .lib.assets import get_random_background_relpath
from .lib.home import BookCover, get_book_cover_pages
from .lib.page_data import get_bundle, get_profile_data, get_response_data, get_search_data
from .lib.prepared_data import PageDataError
from .lib.page_rendering import data_unavailable, prepared_response, query_pairs

logger = logging.getLogger(__name__)


def render_or_stub(request, template_name, context=None, status=200):
    """Render template if available; otherwise return a simple stub.

    If `?format=json` is present, return JSON of the context regardless of template presence.
    """
    context = context or {}
    if request.GET.get('format') == 'json':
        return JsonResponse(context, status=status)
    try:
        # Check if template exists; if so render it
        get_template(template_name)
        return render(request, template_name, context, status=status)
    except Exception:
        # Fallback stub response to keep endpoints working during scaffolding
        return HttpResponse(f"Stub for {template_name}".encode(), status=status, content_type="text/plain")

# Home and static pages
def home_index(request):
    """Render the home page."""
    alias_value: str | None = request.GET.get('alias')
    if alias_value:
        query: str = alias_value.replace('_', ' ')
        redirect_url: str = f"{reverse('search')}?q={quote_plus(query)}"
        return redirect(redirect_url)

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
                image_url = f"{image_base_path.rstrip('/')}/{cover.image_filename}"
            rendered_page.append({
                'author_url': reverse('display_show', args=[cover.author_id]),
                'title': cover.title,
                'author_name': cover.author_name,
                'image_url': image_url,
            })
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


def home_status(request):
    # Optionally include minimal status context later
    return render_or_stub(request, 'home/status.html', context={})


def home_brown_classic(request, name=None):
    query_fragment: str = ''
    if name:
        query_fragment = name
    elif request.GET.get('name'):
        query_fragment = request.GET.get('name')
    redirect_target: str = reverse('search')
    if query_fragment:
        formatted_query: str = query_fragment.replace('_', ' ')
        redirect_target = f"{redirect_target}?q={quote_plus(formatted_query)}"
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
        if request.GET.get('format') == 'json':
            saved_response = get_response_data(request.path, query_pairs(request.GET))
            if saved_response is not None:
                return prepared_response(saved_response)
        else:
            profile_data = get_profile_data(request.path, query_pairs(request.GET))
            if profile_data is not None:
                return render(request, 'display/show.html', {
                    'profile': profile_data,
                    'back_to_search': request.session.get('prepared_search_url', '/search'),
                })
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

# Visualizations
def visualization_home(request, id):
    """Home for visualizations."""
    context = {'id': id}
    return render_or_stub(request, 'visualization/home.html', context)

def visualization_coauthor(request, id):
    """Coauthor visualization."""
    context = {'id': id}
    return render_or_stub(request, 'visualization/coauthor.html', context)

def visualization_coauthor_treemap(request, id):
    """Coauthor treemap visualization."""
    context = {'id': id}
    return render_or_stub(request, 'visualization/coauthor_treemap.html', context)

def visualization_collab(request, id):
    """Collaboration visualization."""
    context = {'id': id}
    return render_or_stub(request, 'visualization/collab.html', context)

def visualization_publications(request, id):
    """Publications visualization."""
    context = {'id': id}
    return render_or_stub(request, 'visualization/publications.html', context)

def visualization_research(request, id):
    """Research visualization."""
    context = {'id': id}
    return render_or_stub(request, 'visualization/research.html', context)

# Edit functionality
@require_http_methods(["GET"])
def edit_profile(request, id):
    """Edit profile page."""
    context = {'id': id}
    return render_or_stub(request, 'edit/profile.html', context)

@require_http_methods(["POST"])
def overview_update(request, faculty_id):
    """Update overview information."""
    # TODO: Implement update logic
    return JsonResponse({'status': 'success'})

@require_http_methods(["POST"])
def research_area_add(request, faculty_id):
    """Add research area."""
    # TODO: Implement add logic
    return JsonResponse({'status': 'success'})

@require_http_methods(["POST"])
def research_area_delete(request, faculty_id):
    """Delete research area."""
    # TODO: Implement delete logic
    return JsonResponse({'status': 'success'})

@require_http_methods(["POST"])
def web_link_save(request, faculty_id):
    """Save web link."""
    # TODO: Implement save logic
    return JsonResponse({'status': 'success'})

@require_http_methods(["POST"])
def web_link_delete(request, faculty_id):
    """Delete web link."""
    # TODO: Implement delete logic
    return JsonResponse({'status': 'success'})

# Search
def search(request):
    """Handle search requests."""
    try:
        if request.GET.get('format') == 'json':
            saved_response = get_response_data(request.path, query_pairs(request.GET))
            if saved_response is not None:
                return prepared_response(saved_response)
        else:
            search_data = get_search_data(request.path, query_pairs(request.GET))
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
        saved_response = get_response_data(request.path, query_pairs(request.GET))
        if saved_response is not None:
            return prepared_response(saved_response)
    except PageDataError as exc:
        return data_unavailable(exc)
    # TODO: Implement facet logic for authentic sources.
    return JsonResponse({'facets': {}})


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
def bot_detect_challenge(request):
    """Handle bot detection challenge."""
    if request.method == 'POST':
        # TODO: Implement challenge verification
        return JsonResponse({'status': 'success'})
    return render_or_stub(request, 'bot_detect/challenge.html')

# Legacy VIVO URLs
def people(request):
    """Legacy people listing."""
    return render_or_stub(request, 'legacy/people.html')

def organizations(request):
    """Legacy organizations listing."""
    return render_or_stub(request, 'legacy/organizations.html')

def old_image(request, id, file_name):
    """Serve old image files."""
    # TODO: Implement file serving logic
    return page_not_found(request)


# Legacy VIVO individual handlers
def individual_redirect(request, id):
    """Handle legacy /individual/<id>/ redirect semantics.

    For now, return a simple stub or JSON with the id, keeping behavior predictable.
    """
    context = {'id': id}
    return render_or_stub(request, 'vivo/individual_redirect.html', context)


def individual_export(request, id, fmt, id2=None):
    """Export legacy individual data in various formats (e.g., .json).

    Supports both /individual/<id>.<fmt>/ and /individual/<id>/<id2>.<fmt>/ patterns.
    """
    payload = {'id': id, 'format': fmt}
    if id2 is not None:
        payload['id2'] = id2
    if fmt.lower() == 'json' or request.GET.get('format') == 'json':
        return JsonResponse(payload)
    return HttpResponse(f"Export for {id} as {fmt}".encode(), content_type='text/plain')


# Editor fast search (de-prioritized functionality; stub only)
@require_http_methods(["GET"])
def edit_fast_search(request):
    query = request.GET.get('q', '')
    return JsonResponse({'query': query, 'results': []})

def page_not_found(request, exception=None, template_name='404.html'):
    """Custom 404 page handler."""
    logger.warning(
        "404 Not Found: %s",
        request.path,
        extra={
            'status_code': 404,
            'request': request
        },
        exc_info=True
    )
    return render_or_stub(request, template_name, status=404)


def server_error(request, template_name='500.html'):
    """Custom 500 page handler."""
    logger.error(
        "500 Internal Server Error: %s",
        request.path,
        extra={
            'status_code': 500,
            'request': request
        },
        exc_info=True
    )
    return render_or_stub(request, template_name, status=500)


# Set up default error handlers
handler404 = page_not_found
handler500 = server_error
