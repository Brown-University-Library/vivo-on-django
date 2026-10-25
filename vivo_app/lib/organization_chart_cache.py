"""
Caches completed charts and briefly delays repeated failed reads using shared storage and locks.
"""

import datetime
import hashlib
import json
import math
import time
from collections.abc import Callable
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache

from vivo_app.lib.page_errors import ChartRetryError, MissingRecordError, PageDataError
from vivo_app.lib.report_cache import generation_lock
from vivo_app.lib.reports import ReportError
from vivo_app.lib.source_pages import CUSTOM_ORGANIZATION_IDS
from vivo_app.lib.source_requests import profile_key, source_origin
from vivo_app.lib.source_teams import source_definitions

CHART_VERSION = 4
CHART_FAILURE_RETRY_SECONDS = 10


@dataclass(frozen=True)
class ChartResult:
    """Keeps one successful chart's name and data together across its public formats."""

    name: str
    data: dict[str, object]


@dataclass(frozen=True)
class ChartFailure:
    """
    Keeps only a retry deadline, without saving exceptions or incomplete chart data.
    """

    retry_at: float


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


def read_cached_chart(key: str) -> ChartResult | None:
    """
    Reuses a complete result or reports the remaining failure delay without extending it.

    Called by: cached_chart()
    """
    value = cache.get(key)
    if isinstance(value, ChartFailure):
        retry_after = math.ceil(value.retry_at - time.time())
        if retry_after > 0:
            raise ChartRetryError(retry_after, cached=True)
    return value if isinstance(value, ChartResult) else None


def cached_chart(
    identifier: str, kind: str, builder: Callable[[str], tuple[str, dict[str, object]]]
) -> tuple[str, dict[str, object]]:
    """
    Reuses complete charts and shares a fixed brief delay after handled failures across workers.

    Called by: views.visualization_publications(), views.visualization_research()
    """
    timeout = settings.CHART_CACHE_TIMEOUT_SECONDS
    try:
        if timeout == 0:
            result = ChartResult(*builder(identifier))
        else:
            key = chart_cache_key(identifier, kind)
            result = read_cached_chart(key)
            if result is None:
                with generation_lock(key):
                    result = read_cached_chart(key)
                    if result is None:
                        try:
                            result = ChartResult(*builder(identifier))
                        except MissingRecordError:
                            raise
                        except PageDataError as exc:
                            failure = ChartFailure(time.time() + CHART_FAILURE_RETRY_SECONDS)
                            cache.set(key, failure, timeout=CHART_FAILURE_RETRY_SECONDS)
                            raise ChartRetryError(CHART_FAILURE_RETRY_SECONDS, cached=False) from exc
                        cache.set(key, result, timeout=timeout)
    except (OSError, ReportError) as exc:
        raise PageDataError('Chart cache storage or generation lock is unavailable.') from exc
    return result.name, result.data
