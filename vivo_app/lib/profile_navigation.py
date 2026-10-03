"""
Chooses the search-return link for a person profile's actual entry request.
"""

from urllib.parse import urlsplit

from django.http import HttpRequest
from django.urls import reverse


def profile_search_return(request: HttpRequest) -> str:
    """
    Returns to the referring local search or the default search on a direct visit.

    Called by: views.display_show()
    """
    search_path = reverse('search').rstrip('/')
    result = search_path
    referer = request.META.get('HTTP_REFERER', '')
    if isinstance(referer, str) and not any(ord(char) < 32 for char in referer):
        try:
            parsed = urlsplit(referer)
            current = urlsplit(request.build_absolute_uri())
            if (
                parsed.scheme == current.scheme
                and parsed.netloc == current.netloc
                and parsed.path.rstrip('/') == search_path
            ):
                result = search_path + ('?' + parsed.query if parsed.query else '')
        except ValueError:
            pass
    return result
