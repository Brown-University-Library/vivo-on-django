"""
Caches completed organization charts briefly using the shared file cache and generation locks.
"""

import datetime
import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache

from vivo_app.lib.page_errors import PageDataError
from vivo_app.lib.report_cache import generation_lock
from vivo_app.lib.reports import ReportError
from vivo_app.lib.source_pages import CUSTOM_ORGANIZATION_IDS
from vivo_app.lib.source_requests import profile_key, source_origin
from vivo_app.lib.source_teams import source_definitions

CHART_VERSION = 2


@dataclass(frozen=True)
class ChartResult:
    """Keeps one successful chart's name and data together across its public formats."""

    name: str
    data: dict[str, object]


def chart_cache_key(identifier: str, kind: str) -> str:
    """
    Separates organizations, chart kinds, source settings, membership definitions, and calendar years.

    Called by: cached_chart(), tests
    """
    profile_key(identifier)
    if kind not in {'publications', 'research'}:
        raise PageDataError('The requested chart kind is unsupported.')
    definitions = source_definitions() if identifier.startswith('team-') or identifier in CUSTOM_ORGANIZATION_IDS else None
    values = [
        identifier,
        kind,
        source_origin('solr'),
        definitions,
        settings.CHART_CACHE_TIMEOUT_SECONDS,
        datetime.datetime.now().astimezone().year,
        CHART_VERSION,
    ]
    digest = hashlib.sha256(json.dumps(values, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest()
    return f'organization-chart:{digest}'


def cached_chart(
    identifier: str, kind: str, builder: Callable[[str], tuple[str, dict[str, object]]]
) -> tuple[str, dict[str, object]]:
    """
    Reuses a complete chart for a fixed short lifetime and leaves failed requests uncached.

    Called by: views.visualization_publications(), views.visualization_research()
    """
    timeout = settings.CHART_CACHE_TIMEOUT_SECONDS
    try:
        if timeout == 0:
            result = ChartResult(*builder(identifier))
        else:
            key = chart_cache_key(identifier, kind)
            result = cache.get(key)
            if not isinstance(result, ChartResult):
                with generation_lock(key):
                    result = cache.get(key)
                    if not isinstance(result, ChartResult):
                        result = ChartResult(*builder(identifier))
                        cache.set(key, result, timeout=timeout)
    except (OSError, ReportError) as exc:
        raise PageDataError('Chart cache storage or generation lock is unavailable.') from exc
    return result.name, result.data
