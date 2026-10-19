"""
Caches successful legacy display JSON-LD using the shared cache and generation locks.
"""

import hashlib
import json

from django.conf import settings
from django.core.cache import cache

from vivo_app.lib.page_data import DisplayPage, get_display_data
from vivo_app.lib.page_errors import PageDataError
from vivo_app.lib.report_cache import generation_lock
from vivo_app.lib.source_requests import profile_key
from vivo_app.lib.source_types import SourceResponse

JSONLD_VERSION = 1


def jsonld_cache_key(identifier: str) -> str:
    """
    Validates the identifier and separates JSON-LD entries by sources, lifetime, and code version.

    Called by: cached_display_data(), tests
    """
    profile_key(identifier)
    inputs = [settings.SOLR_URL, settings.VIVO_BACKEND_URL, settings.REPORT_CACHE_TIMEOUT_SECONDS, JSONLD_VERSION]
    digest = hashlib.sha256(json.dumps(inputs, ensure_ascii=True).encode('utf-8')).hexdigest()
    return f'display-jsonld:{identifier}:{digest}'


def cached_display_data(path: str, query: list[tuple[str, str]], method: str | None = 'GET') -> DisplayPage | SourceResponse:
    """
    Reuses successful JSON-LD before source reads, leaving HTML and failed responses uncached.

    Called by: views.display_show(), tests
    """
    identifier = path.rstrip('/').rsplit('/', 1)[-1]
    timeout = settings.REPORT_CACHE_TIMEOUT_SECONDS
    result: DisplayPage | SourceResponse
    try:
        if timeout == 0 or query or method not in {'GET', 'HEAD'} or identifier.startswith('team-'):
            result = get_display_data(path, query)
        else:
            key = jsonld_cache_key(identifier)
            cached = cache.get(key)
            if isinstance(cached, SourceResponse) and cached.status == 200:
                result = cached
            else:
                with generation_lock(key):
                    cached = cache.get(key)
                    if isinstance(cached, SourceResponse) and cached.status == 200:
                        result = cached
                    else:
                        result = get_display_data(path, query)
                        if isinstance(result, SourceResponse) and result.status == 200:
                            cache.set(key, result, timeout=timeout)
    except OSError as exc:
        raise PageDataError('Display JSON-LD cache storage is unavailable.') from exc
    return result
