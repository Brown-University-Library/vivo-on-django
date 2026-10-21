"""
Caches validated public images and CV files briefly using the shared file cache and locks.
"""

import hashlib
import json
from collections.abc import Callable

from django.conf import settings
from django.core.cache import cache

from vivo_app.lib.page_errors import InvalidDocumentError, PageDataError
from vivo_app.lib.report_cache import generation_lock
from vivo_app.lib.reports import ReportError
from vivo_app.lib.source_requests import document_key, image_key, source_origin
from vivo_app.lib.source_types import RequestKey, SourceResponse

MEDIA_VERSION = 2


def media_cache_key(key: RequestKey) -> str:
    """
    Separates validated file paths, document versions, sources, and cache lifetimes.

    Called by: cached_media(), tests
    """
    expected = image_key(key.path) if key.service == 'images' else document_key(key.path, key.query)
    if key != expected:
        raise PageDataError('The requested media source is unsupported.')
    values = [
        key.service,
        source_origin(key.service),
        key.path,
        key.query,
        settings.MEDIA_CACHE_TIMEOUT_SECONDS,
        MEDIA_VERSION,
    ]
    digest = hashlib.sha256(json.dumps(values, ensure_ascii=True).encode('utf-8')).hexdigest()
    return f'source-media:{digest}'


def validated_media(key: RequestKey, reader: Callable[[RequestKey], SourceResponse]) -> SourceResponse:
    """
    Checks successful file types and leaves missing files and version redirects uncached.

    Called by: cached_media()
    """
    result = reader(key)
    if result.status == 200:
        content_type = dict(result.headers).get('content-type', '').split(';', 1)[0].strip().lower()
        if key.service == 'images':
            if content_type not in {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}:
                raise PageDataError('The image source returned an unsupported content type.')
        else:
            if content_type != 'application/pdf' or not result.body.startswith(b'%PDF-'):
                raise InvalidDocumentError('The document source did not provide a PDF.')
        result = SourceResponse(200, (('content-type', content_type),), result.body)
    elif result.status != 404 and not (key.service == 'documents' and result.status in {301, 302}):
        raise PageDataError(f'{key.service} source returned an unusable response.')
    return result


def cached_media(key: RequestKey, reader: Callable[[RequestKey], SourceResponse]) -> SourceResponse:
    """
    Reuses successful files for a fixed short lifetime and retries failures on the next request.

    Called by: views.source_image(), views.source_document()
    """
    cache_key = media_cache_key(key)
    timeout = settings.MEDIA_CACHE_TIMEOUT_SECONDS
    try:
        if timeout == 0:
            result = validated_media(key, reader)
        else:
            saved = cache.get(cache_key)
            if isinstance(saved, SourceResponse) and saved.status == 200:
                result = saved
            else:
                with generation_lock(cache_key):
                    saved = cache.get(cache_key)
                    if isinstance(saved, SourceResponse) and saved.status == 200:
                        result = saved
                    else:
                        result = validated_media(key, reader)
                        if result.status == 200:
                            cache.set(cache_key, result, timeout=timeout)
    except (OSError, ReportError) as exc:
        raise PageDataError('Media cache storage or generation lock is unavailable.') from exc
    return result
