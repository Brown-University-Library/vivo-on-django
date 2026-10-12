"""
Loads private report definitions and checks server-supplied report access.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class ReportError(ValueError):
    """Identifies a report failure using a message safe for application logs."""


@dataclass(frozen=True)
class Report:
    """Keeps the original row alongside its parsed selection rules."""

    id: int
    name: str | None
    description: str | None
    definition: dict[str, list[str]]
    source: dict[str, object]


def cache_timeout(value: str) -> int:
    """
    Converts seconds, including Python's underscore spelling, to a nonnegative integer.

    Called by: config.settings, tests
    """
    try:
        result = int(value)
        if result < 0:
            raise ValueError
    except ValueError as exc:
        raise ImproperlyConfigured('REPORT_CACHE_TIMEOUT_SECONDS must be a nonnegative integer.') from exc
    return result


def report_access(meta: dict[str, object]) -> bool:
    """
    Requires a trusted server attribute or the explicitly enabled loopback runserver.

    Called by: views.subject_lib_list(), views.subject_lib()
    """
    key = settings.REPORTS_SHIB_ATTRIBUTE
    if not isinstance(key, str) or not key or key.upper().startswith('HTTP_'):
        raise ReportError('REPORTS_SHIB_ATTRIBUTE must name a server environment attribute.')
    value = meta.get(key)
    trusted = isinstance(value, str) and bool(value.strip())
    local = (
        settings.REPORTS_ALLOW_LOCAL_DEVELOPMENT
        and settings.DEBUG
        and getattr(settings, 'REPORTS_LOCAL_RUNSERVER', False)
        and meta.get('REMOTE_ADDR') in {'127.0.0.1', '::1'}
    )
    return bool(trusted or local)


def parse_report(row: object) -> Report:
    """
    Validates the seven transferred fields without changing their stored values.

    Called by: load_reports(), tests
    """
    fields = {'id', 'user_id', 'name', 'description', 'definition', 'created_at', 'updated_at'}
    if not isinstance(row, dict) or set(row) != fields:
        raise ReportError('A report must contain exactly the seven report fields.')
    identifier = row['id']
    if type(identifier) is not int or identifier < 1:
        raise ReportError('Report IDs must be positive integers.')
    if row['user_id'] is not None and type(row['user_id']) is not int:
        raise ReportError('A report user_id must be an integer or null.')
    for field in ('name', 'description', 'created_at', 'updated_at'):
        if row[field] is not None and not isinstance(row[field], str):
            raise ReportError('Report text and timestamp fields must be strings or null.')
    raw = row['definition']
    if not isinstance(raw, str):
        raise ReportError('A report definition must be a JSON string.')
    try:
        parsed = json.loads(raw)
    except ValueError as exc:
        raise ReportError('A report definition contains invalid JSON.') from exc
    if not isinstance(parsed, dict) or set(parsed) - {'faculty_ids', 'department_names'}:
        raise ReportError('A report definition contains unsupported selection fields.')
    definition: dict[str, list[str]] = {}
    for key, values in parsed.items():
        if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
            raise ReportError('Report selectors must be lists of nonempty strings.')
        definition[key] = values
    return Report(identifier, row['name'], row['description'], definition, dict(row))


def load_reports() -> list[Report]:
    """
    Reads the small private definition file afresh for each permitted request.

    Called by: views.subject_lib_list(), views.subject_lib()
    """
    configured = settings.REPORT_DEFINITIONS_PATH
    if not configured:
        raise ReportError('REPORT_DEFINITIONS_PATH is not configured.')
    path = Path(configured)
    if not path.is_absolute():
        path = settings.BASE_DIR / path
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError, UnicodeError) as exc:
        raise ReportError('The report definitions file cannot be read as JSON.') from exc
    if not isinstance(data, dict) or type(data.get('schema_version')) is not int or data['schema_version'] != 1:
        raise ReportError('The report definitions file requires schema_version 1.')
    rows = data.get('reports')
    if not isinstance(rows, list):
        raise ReportError('The report definitions file requires a reports list.')
    reports = [parse_report(row) for row in rows]
    if len({report.id for report in reports}) != len(reports):
        raise ReportError('The report definitions file contains duplicate IDs.')
    return reports


def rails_integer(value: str) -> int:
    """
    Reads a leading signed decimal number as Ruby String.to_i does.

    Called by: views.subject_lib(), report_exports.publication_year(), tests
    """
    match = re.match(r'\s*([+-]?[0-9]+(?:_[0-9]+)*)', value, flags=re.ASCII)
    result = int(match.group(1)) if match else 0
    return result


def download_name(name: str | None, extension: str) -> str:
    """
    Matches Rails attachment filename cleanup and its empty-name fallback.

    Called by: report_cache.generate_report(), tests
    """
    stripped = (name or '').strip(' \t\r\n\v\f\0')
    if stripped:
        safe = re.sub(r'[^0-9a-z]', '_', stripped.lower())
        if not ('a' <= safe[0] <= 'z'):
            safe = '_' + safe
    else:
        safe = 'untitled'
    return f'{safe}.{extension}'
