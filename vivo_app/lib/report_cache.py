"""
Caches complete report downloads and coordinates generation across server workers.
"""

import fcntl
import hashlib
import json
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.cache import cache

from vivo_app.lib.report_exports import csv_bytes, report_tables, xml_bytes
from vivo_app.lib.report_sources import report_faculty
from vivo_app.lib.reports import Report, ReportError, download_name

EXPORT_VERSION = 1
LOCK_WAIT_SECONDS = 30.0


@dataclass(frozen=True)
class ReportDownload:
    """Keeps one attachment's bytes and response metadata."""

    body: bytes
    filename: str
    content_type: str


@dataclass(frozen=True)
class ReportBundle:
    """Keeps both formats from the same faculty reads and generation time."""

    csv: ReportDownload
    xml: ReportDownload
    generated_at: float


def report_cache_key(report: Report) -> str:
    """
    Hashes definition, source, timeout, and code version without exposing private values.

    Called by: cached_report(), tests
    """
    inputs = [report.source, settings.SOLR_URL, settings.REPORT_CACHE_TIMEOUT_SECONDS, EXPORT_VERSION]
    digest = hashlib.sha256(json.dumps(inputs, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest()
    return f'report:{report.id}:{digest}'


@contextmanager
def generation_lock(key: str) -> Iterator[None]:
    """
    Holds a Unix file lock shared by workers, releasing it even after failure or process exit.

    Called by: cached_report(), display_cache.cached_display(), display_jsonld_cache.cached_display_data(), tests
    """
    directory = Path(settings.REPORT_CACHE_LOCK_DIR)
    if not directory.is_absolute():
        directory = settings.BASE_DIR / directory
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    filename = hashlib.sha256(key.encode('ascii')).hexdigest() + '.lock'
    ## Keep lock files in place: unlinking a locked file can create two independent locks.
    with (directory / filename).open('a', encoding='ascii') as handle:
        deadline = time.monotonic() + LOCK_WAIT_SECONDS
        acquired = False
        try:
            while not acquired:
                try:
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise ReportError('This report is still being generated; try the download again.') from None
                    time.sleep(0.1)
            yield
        finally:
            if acquired:
                fcntl.flock(handle, fcntl.LOCK_UN)


def generate_report(report: Report) -> ReportBundle:
    """
    Fetches faculty once and renders both formats before recording successful completion.

    Called by: cached_report(), tests
    """
    tables = report_tables(report_faculty(report))
    csv = ReportDownload(csv_bytes(tables), download_name(report.name, 'csv'), 'text/plain; charset=utf-8')
    xml = ReportDownload(xml_bytes(tables), download_name(report.name, 'xml'), 'application/xml; charset=utf-8')
    return ReportBundle(csv, xml, time.time())


def cached_report(report: Report) -> ReportBundle:
    """
    Reuses complete reports for a fixed lifetime or generates fresh output when disabled.

    Called by: views.subject_lib(), tests
    """
    timeout = settings.REPORT_CACHE_TIMEOUT_SECONDS
    try:
        if timeout == 0:
            result = generate_report(report)
        else:
            key = report_cache_key(report)
            result = cache.get(key)
            if not isinstance(result, ReportBundle):
                with generation_lock(key):
                    result = cache.get(key)
                    if not isinstance(result, ReportBundle):
                        result = generate_report(report)
                        cache.set(key, result, timeout=timeout)
    except OSError as exc:
        raise ReportError('Report cache storage is unavailable.') from exc
    return result
