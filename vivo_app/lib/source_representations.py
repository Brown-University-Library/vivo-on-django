"""
Retries timed-out VIVO reads and briefly caches successful public downloads.
"""

import hashlib
import json
import logging
import time
from collections.abc import Callable

from django.conf import settings
from django.core.cache import cache

from vivo_app.lib.page_errors import PageDataError, SourceTimeoutError
from vivo_app.lib.report_cache import generation_lock
from vivo_app.lib.reports import ReportError
from vivo_app.lib.source_requests import vitro_key
from vivo_app.lib.source_types import RequestKey, SourceResponse

REPRESENTATION_VERSION = 1
logger = logging.getLogger(__name__)


def read_representation(key: RequestKey, reader: Callable[[RequestKey], SourceResponse]) -> SourceResponse:
    """
    Retries a timed-out VIVO read once without changing source limits or response bytes.

    Called by: cached_representation(), page_data.get_display_data()
    """
    try:
        result = reader(key)
    except SourceTimeoutError:
        logger.warning('Retrying timed-out VIVO read; path, ``%s``', key.path)
        time.sleep(0.25)
        result = reader(key)
    return result


def representation_cache_key(identifier: str, fmt: str) -> str:
    """
    Separates validated record IDs, formats, sources, cache lifetimes, and code versions.

    Called by: cached_representation(), tests
    """
    vitro_key(identifier, fmt)
    inputs = [settings.VIVO_BACKEND_URL, settings.VIVO_EXPORT_CACHE_TIMEOUT_SECONDS, REPRESENTATION_VERSION]
    digest = hashlib.sha256(json.dumps(inputs, ensure_ascii=True).encode('utf-8')).hexdigest()
    return f'vivo-export:{identifier}:{fmt}:{digest}'


def cached_representation(
    identifier: str, fmt: str, reader: Callable[[RequestKey], SourceResponse], method: str | None = 'GET'
) -> SourceResponse:
    """
    Reuses successful downloads for a fixed short lifetime, sharing source reads across workers.

    Called by: views.individual_export(), tests
    """
    key = vitro_key(identifier, fmt)
    timeout = settings.VIVO_EXPORT_CACHE_TIMEOUT_SECONDS
    try:
        if timeout == 0 or method not in {'GET', 'HEAD'}:
            result = read_representation(key, reader)
        else:
            cache_key = representation_cache_key(identifier, fmt)
            saved = cache.get(cache_key)
            if isinstance(saved, SourceResponse) and saved.status == 200:
                result = saved
            else:
                with generation_lock(cache_key):
                    saved = cache.get(cache_key)
                    if isinstance(saved, SourceResponse) and saved.status == 200:
                        result = saved
                    else:
                        result = read_representation(key, reader)
                        if result.status == 200:
                            cache.set(cache_key, result, timeout=timeout)
    except (OSError, ReportError) as exc:
        raise PageDataError('VIVO download cache storage or generation lock is unavailable.') from exc
    return result
