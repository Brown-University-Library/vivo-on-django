"""
Validates portable prepared page data kept outside Git checkouts.
"""

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from vivo_app.lib.recorded_responses import RecordingError, external_path, json_object, string_pairs

PAGE_DATA_VERSION = 1


class PageDataError(ValueError):
    """Identifies unavailable or invalid page data without a fallback."""


def object_value(value: object) -> dict[str, object]:
    """
    Requires a JSON object.

    Called by: load_bundle(), read_entry(), validate_page()
    """
    try:
        result = json_object(value)
    except RecordingError as exc:
        raise PageDataError(str(exc)) from exc
    return result


def request_key(path: str, query: list[tuple[str, str]]) -> tuple[str, tuple[tuple[str, str], ...]]:
    """
    Normalizes parameter names while retaining repeated values and blank inputs.

    Called by: load_bundle(), PreparedBundle.page()
    """
    if not path.startswith('/') or path.startswith('//') or '?' in path or '#' in path or '\\' in path:
        raise PageDataError('Use a site-relative request path and separate query pairs.')
    page_values = [value for key, value in query if key == 'page']
    pairs = [(key, value) for key, value in query if not (key == 'page' and page_values == ['1'])]
    result = (path.rstrip('/') or '/', tuple(sorted(pairs, key=lambda pair: pair[0])))
    return result


def read_file(root: Path, value: object) -> tuple[str, bytes]:
    """
    Checks a relative file path and checksum before reading bundle content.

    Called by: load_bundle(), read_entry()
    """
    entry = object_value(value)
    filename, checksum = entry.get('file'), entry.get('sha256')
    if not isinstance(filename, str) or not filename or Path(filename).is_absolute() or '\\' in filename:
        raise PageDataError('Bundle files need relative paths.')
    path = (root / filename).resolve()
    if not path.is_relative_to(root):
        raise PageDataError('A bundle file leaves the bundle directory.')
    try:
        external_path(path)
        body = path.read_bytes()
    except (OSError, RecordingError) as exc:
        raise PageDataError('A bundle file is missing, unreadable, or inside a Git checkout.') from exc
    if not isinstance(checksum, str) or hashlib.sha256(body).hexdigest() != checksum:
        raise PageDataError('A bundle file checksum does not match.')
    return filename, body


@dataclass(frozen=True)
class PreparedAsset:
    """Keeps validated local asset bytes and their content type."""

    body: bytes
    content_type: str


@dataclass(frozen=True)
class PreparedEntry:
    """Keeps one exact saved page state or supporting response."""

    family: str
    data: dict[str, object]
    status: int = 200
    content_type: str = 'text/html; charset=utf-8'
    body: bytes = b''
    headers: tuple[tuple[str, str], ...] = ()


@dataclass
class PreparedBundle:
    """Supplies validated states without opening network connections."""

    version: str
    origin: str
    prepared_at: str
    application_revision: str
    entries: dict[str, PreparedEntry]
    requests: dict[tuple[str, tuple[tuple[str, str], ...]], str]
    cases: dict[str, list[str]]
    assets: dict[str, PreparedAsset]

    def page(self, family: str, path: str, query: list[tuple[str, str]]) -> PreparedEntry:
        """
        Selects an exact prepared request and checks its expected page family.

        Called by: page_data.get_search_data(), page_data.get_profile_data(), page_data.get_response_data()
        """
        name = self.requests.get(request_key(path, query))
        if name is None:
            raise PageDataError('No prepared state matches this request. Add it to the external bundle and validate again.')
        entry = self.entries[name]
        if entry.family != family:
            raise PageDataError('The prepared state has a different page family.')
        return entry


def read_entry(root: Path, value: object, assets: dict[str, PreparedAsset]) -> PreparedEntry:
    """
    Checks page fields or retains an original supporting response unchanged.

    Called by: load_bundle()
    """
    from vivo_app.lib.page_fields import validate_page

    row = object_value(value)
    family = row.get('family')
    if family not in {'search', 'profile', 'organization', 'home', 'response'}:
        raise PageDataError('Unsupported prepared page family.')
    _, body = read_file(root, row)
    result: PreparedEntry
    if family == 'response':
        status, content_type = row.get('status'), row.get('content_type')
        if type(status) is not int or not 200 <= status <= 599:
            raise PageDataError('Supporting responses need an HTTP status.')
        if not isinstance(content_type, str) or '\n' in content_type or '\r' in content_type:
            raise PageDataError('Supporting responses need a content type.')
        try:
            headers = string_pairs(row.get('headers', []))
        except RecordingError as exc:
            raise PageDataError(str(exc)) from exc
        allowed = {'content-disposition', 'location', 'cache-control'}
        if any(key.lower() not in allowed or '\r' in val or '\n' in val for key, val in headers):
            raise PageDataError('Unsupported supporting response header.')
        if 300 <= status < 400:
            locations = [value for key, value in headers if key.lower() == 'location']
            if len(locations) != 1 or not locations[0].startswith('/') or locations[0].startswith('//'):
                raise PageDataError('Prepared redirects need one local destination.')
        result = PreparedEntry('response', {}, status, content_type, body, headers)
    else:
        try:
            data = object_value(json.loads(body))
        except (ValueError, UnicodeError) as exc:
            raise PageDataError('A prepared page contains invalid JSON.') from exc
        validate_page(str(family), data, set(assets))
        result = PreparedEntry(str(family), data)
    return result


def load_bundle(directory: Path) -> PreparedBundle:
    """
    Validates the entire bundle, including every case, page, response, and asset.

    Called by: page_data.get_bundle(), check_page_data(), validate_prepared_data.Command.handle()
    """
    try:
        root = external_path(directory)
    except RecordingError as exc:
        raise PageDataError('The prepared bundle must be outside a Git checkout.') from exc
    except OSError as exc:
        raise PageDataError('The prepared bundle directory is unreadable.') from exc
    try:
        manifest_bytes = (root / 'manifest.json').read_bytes()
    except OSError as exc:
        raise PageDataError('The prepared manifest is missing or unreadable.') from exc
    try:
        manifest = object_value(json.loads(manifest_bytes))
    except (PageDataError, ValueError, UnicodeError) as exc:
        raise PageDataError('The prepared manifest contains invalid JSON.') from exc
    if type(manifest.get('format_version')) is not int or manifest.get('format_version') != PAGE_DATA_VERSION:
        raise PageDataError('Unsupported prepared data format version.')
    revision = manifest.get('application_revision')
    version, origin, prepared_at = manifest.get('bundle_version'), manifest.get('data_origin'), manifest.get('prepared_at')
    if not isinstance(version, str) or not re.fullmatch(r'[A-Za-z0-9._-]+', version):
        raise PageDataError('The bundle needs a version containing letters, numbers, dots, underscores, or hyphens.')
    if origin not in {'invented', 'prepared_from_reference'}:
        raise PageDataError('Declare data_origin as invented or prepared_from_reference.')
    if not isinstance(revision, str) or not revision.strip():
        raise PageDataError('Record the compatible application revision or working revision description.')
    try:
        timestamp = datetime.fromisoformat(str(prepared_at))
    except ValueError as exc:
        raise PageDataError('A preparation timestamp with a timezone is required.') from exc
    if timestamp.tzinfo is None:
        raise PageDataError('A preparation timestamp with a timezone is required.')
    read_file(root, manifest.get('readme'))
    assets: dict[str, PreparedAsset] = {}
    for name, item in object_value(manifest.get('assets')).items():
        row = object_value(item)
        content_type = row.get('content_type')
        if not re.fullmatch(r'[A-Za-z0-9._-]+', name):
            raise PageDataError('Asset names must be simple filenames.')
        if content_type not in {'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'font/woff2', 'font/woff', 'font/ttf'}:
            raise PageDataError('Unsupported prepared asset content type.')
        _, body = read_file(root, row)
        assets[name] = PreparedAsset(body, str(content_type))
    entries: dict[str, PreparedEntry] = {}
    requests: dict[tuple[str, tuple[tuple[str, str], ...]], str] = {}
    for name, item in object_value(manifest.get('entries')).items():
        row = object_value(item)
        path = row.get('path')
        if not isinstance(path, str) or not name:
            raise PageDataError('Each entry needs a name and request path.')
        try:
            query = list(string_pairs(row.get('query')))
        except RecordingError as exc:
            raise PageDataError(str(exc)) from exc
        key = request_key(path, query)
        if key in requests:
            raise PageDataError('Prepared request states must be unique.')
        entries[name] = read_entry(root, row, assets)
        entry = entries[name]
        if entry.family == 'search':
            inputs = dict(query)
            expected_query = inputs.get('q', '')
            if expected_query == '*':
                expected_query = ''
            if entry.data['query'] != expected_query or str(entry.data['page']) != inputs.get('page', '1'):
                raise PageDataError('Search fields disagree with the saved request query or page.')
        elif entry.family == 'profile' and entry.data['id'] != path.rstrip('/').rsplit('/', 1)[-1]:
            raise PageDataError('Profile identity disagrees with the saved request path.')
        elif entry.family == 'organization' and entry.data['id'] != path.rstrip('/').rsplit('/', 1)[-1]:
            raise PageDataError('Organization identity disagrees with the saved request path.')
        requests[key] = name
    cases: dict[str, list[str]] = {}
    for name, items in object_value(manifest.get('cases')).items():
        if not name or not isinstance(items, list) or not items:
            raise PageDataError('Each case must list at least one entry.')
        checked: list[str] = []
        for item in items:
            if not isinstance(item, str) or item not in entries or item in checked:
                raise PageDataError('A case names an absent or repeated entry.')
            checked.append(item)
        cases[name] = checked
    if not entries or not cases or set(entries) != {item for items in cases.values() for item in items}:
        raise PageDataError('Every prepared entry must belong to a case.')
    validate_documents(entries, requests)
    return PreparedBundle(version, str(origin), str(prepared_at), revision, entries, requests, cases, assets)


def validate_documents(
    entries: dict[str, PreparedEntry], requests: dict[tuple[str, tuple[tuple[str, str], ...]], str]
) -> None:
    """
    Requires every profile CV link to resolve to a saved PDF response.

    Called by: load_bundle()
    """
    from urllib.parse import parse_qsl, urlsplit

    for entry in entries.values():
        cv_url = entry.data.get('cv_url') if entry.family == 'profile' else None
        if isinstance(cv_url, str) and cv_url:
            parsed = urlsplit(cv_url)
            name = requests.get(request_key(parsed.path, parse_qsl(parsed.query, keep_blank_values=True)))
            document = entries.get(name) if name else None
            if (
                document is None
                or document.family != 'response'
                or document.status != 200
                or document.content_type != 'application/pdf'
                or not document.body.startswith(b'%PDF-')
            ):
                raise PageDataError('A profile CV link needs a saved PDF response.')
