"""
Caches public display attachments separately using the report timeout and shared file locks.
"""

import hashlib
import json
import time

from django.conf import settings
from django.core.cache import cache

from vivo_app.lib.display_exports import display_files
from vivo_app.lib.page_errors import PageDataError
from vivo_app.lib.report_cache import ReportBundle, ReportDownload, generation_lock
from vivo_app.lib.source_pages import CUSTOM_ORGANIZATION_IDS
from vivo_app.lib.source_requests import profile_export_key
from vivo_app.lib.source_teams import source_definitions

EXPORT_VERSION = 1


def display_cache_key(identifier: str) -> str:
    """
    Validates the ID and hashes source, definitions, lifetime, and export version into a public-only key.

    Called by: cached_display(), tests
    """
    profile_export_key(identifier)
    team = identifier.startswith('team-')
    definitions = source_definitions() if team or identifier in CUSTOM_ORGANIZATION_IDS else None
    inputs = [settings.SOLR_URL, definitions, settings.REPORT_CACHE_TIMEOUT_SECONDS, EXPORT_VERSION]
    digest = hashlib.sha256(json.dumps(inputs, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest()
    kind = 'team' if team else 'record'
    return f'display-export:{kind}:{identifier}:{digest}'


def generate_display(identifier: str) -> ReportBundle:
    """
    Finishes both public attachments before starting their shared cache lifetime.

    Called by: cached_display()
    """
    csv, xml = display_files(identifier)
    return ReportBundle(
        ReportDownload(csv, f'{identifier}.csv', 'application/xml'),
        ReportDownload(xml, f'{identifier}.xml', 'application/xml'),
        time.time(),
    )


def cached_display(identifier: str) -> ReportBundle:
    """
    Reuses completed public exports for a fixed lifetime without reading staff report definitions.

    Called by: views.display_show(), tests
    """
    timeout = settings.REPORT_CACHE_TIMEOUT_SECONDS
    try:
        if timeout == 0:
            result = generate_display(identifier)
        else:
            key = display_cache_key(identifier)
            result = cache.get(key)
            if not isinstance(result, ReportBundle):
                with generation_lock(key):
                    result = cache.get(key)
                    if not isinstance(result, ReportBundle):
                        result = generate_display(identifier)
                        if key != display_cache_key(identifier):
                            raise PageDataError(
                                'Export membership definitions changed during generation; retry the download.'
                            )
                        cache.set(key, result, timeout=timeout)
    except OSError as exc:
        raise PageDataError('Export cache storage is unavailable.') from exc
    return result
