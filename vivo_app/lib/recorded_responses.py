"""
Reads saved GET responses without opening a network connection.

Real recordings and manifests belong outside every Git checkout. This loader
does not yet replace the prototype page helpers or establish data authenticity.
"""

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


class RecordingError(ValueError):
    """Identifies a missing, invalid, or mismatched recording."""


@dataclass(frozen=True)
class RequestKey:
    """Identifies a GET request using decoded, ordered query pairs."""

    service: str
    path: str
    query: tuple[tuple[str, str], ...] = ()
    headers: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class RecordedResponse:
    """Retains the status, headers, and unchanged bytes of a saved response."""

    status: int
    headers: tuple[tuple[str, str], ...]
    body: bytes

    def json(self) -> object:
        """
        Parses a JSON body without changing the retained response bytes.

        Called by: response consumers and tests
        """
        try:
            result: object = json.loads(self.body)
        except (ValueError, UnicodeError) as exc:
            raise RecordingError('Recorded response does not contain valid JSON.') from exc
        return result


def json_object(value: object) -> dict[str, object]:
    """
    Checks that a JSON value contains an object with string keys.

    Called by: load_recordings(), parse_entry()
    """
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise RecordingError('Expected a JSON object with string keys.')
    result: dict[str, object] = dict(value)
    return result


def string_pairs(value: object) -> tuple[tuple[str, str], ...]:
    """
    Preserves repeated keys, blank values, and pair order.

    Called by: parse_entry()
    """
    if not isinstance(value, list):
        raise RecordingError('Expected an array of string pairs.')
    result: list[tuple[str, str]] = []
    for pair in value:
        if not isinstance(pair, list) or len(pair) != 2:
            raise RecordingError('Expected an array of string pairs.')
        key, text = pair
        if not isinstance(key, str) or not isinstance(text, str):
            raise RecordingError('Expected an array of string pairs.')
        result.append((key, text))
    return tuple(result)


def external_path(path: Path) -> Path:
    """
    Rejects files and directories inside a Git checkout.

    Called by: load_recordings(), parse_entry()
    """
    resolved: Path = path.resolve()
    if any((parent / '.git').exists() for parent in (resolved, *resolved.parents)):
        raise RecordingError('Keep recording files outside Git checkouts.')
    return resolved


def parse_entry(value: object, root: Path) -> tuple[str, RequestKey, RecordedResponse]:
    """
    Validates one request and reads its response after checking the checksum.

    Called by: load_recordings()
    """
    entry: dict[str, object] = json_object(value)
    name = entry.get('id')
    request: dict[str, object] = json_object(entry.get('request'))
    response: dict[str, object] = json_object(entry.get('response'))
    service, path = request.get('service'), request.get('path')
    if not isinstance(name, str) or not name or not isinstance(service, str) or not service:
        raise RecordingError('Each recording needs an id and a service name.')
    if request.get('method') != 'GET':
        raise RecordingError('Only recorded GET requests are supported.')
    if not isinstance(path, str) or not path.startswith('/') or path.startswith('//') or '?' in path or '#' in path:
        raise RecordingError('Use a service-relative path and separate query pairs.')
    request_headers = string_pairs(request.get('headers'))
    if any(key.lower() in {'authorization', 'cookie', 'proxy-authorization'} for key, _ in request_headers):
        raise RecordingError('Do not include authentication or cookie request headers.')
    key = RequestKey(service, path, string_pairs(request.get('query')), request_headers)
    status, filename, digest = response.get('status'), response.get('body_file'), response.get('sha256')
    if type(status) is not int or not 100 <= status <= 599:
        raise RecordingError('Response status must be an HTTP status integer.')
    if not isinstance(filename, str) or not filename or Path(filename).is_absolute():
        raise RecordingError('Response body_file must be a relative filename.')
    body_path = external_path(root / filename)
    if not body_path.is_relative_to(root):
        raise RecordingError('Response body_file must stay inside the recording directory.')
    try:
        body = body_path.read_bytes()
    except OSError as exc:
        raise RecordingError('A recorded response body is missing or unreadable.') from exc
    if not isinstance(digest, str) or hashlib.sha256(body).hexdigest() != digest:
        raise RecordingError('Recorded response checksum does not match.')
    result = RecordedResponse(status, string_pairs(response.get('headers')), body)
    return name, key, result


class RecordedResponses:
    """Selects exact recorded requests and fails when a request was not saved."""

    def __init__(
        self,
        data_kind: str,
        captured_at: str,
        entries: dict[str, tuple[RequestKey, RecordedResponse]],
        cases: dict[str, tuple[str, ...]],
    ) -> None:
        """
        Keeps validated entries in memory for repeatable local reads.

        Called by: load_recordings()
        """
        self.data_kind: str = data_kind
        self.captured_at: str = captured_at
        self._entries = entries
        self._cases = cases

    def for_case(self, case_id: str) -> dict[RequestKey, RecordedResponse]:
        """
        Returns only the responses listed for the selected case.

        Called by: get(), main(), tests
        """
        if case_id not in self._cases:
            raise RecordingError('The selected case has no recordings.')
        result = {self._entries[name][0]: self._entries[name][1] for name in self._cases[case_id]}
        return result

    def get(self, case_id: str, request: RequestKey) -> RecordedResponse:
        """
        Returns a saved response without any fallback to samples or a service.

        Called by: response consumers and tests
        """
        responses = self.for_case(case_id)
        if request not in responses:
            raise RecordingError('The selected case has no recording for this exact request.')
        return responses[request]


def load_recordings(manifest_path: Path) -> RecordedResponses:
    """
    Reads and validates a complete manifest and all referenced response files.

    Called by: main(), response consumers, tests
    """
    path: Path = external_path(manifest_path)
    try:
        value: object = json.loads(path.read_bytes())
    except (OSError, ValueError, UnicodeError) as exc:
        raise RecordingError('The recording manifest is missing, unreadable, or invalid JSON.') from exc
    manifest = json_object(value)
    if type(manifest.get('schema_version')) is not int or manifest.get('schema_version') != 1:
        raise RecordingError('Unsupported recording schema version.')
    data_kind, captured_at = manifest.get('data_kind'), manifest.get('captured_at')
    if not isinstance(data_kind, str) or data_kind not in {'synthetic', 'recorded'}:
        raise RecordingError('Declare data_kind as synthetic or recorded.')
    if not isinstance(captured_at, str):
        raise RecordingError('A capture timestamp with a timezone is required.')
    try:
        timestamp = datetime.fromisoformat(captured_at)
    except ValueError as exc:
        raise RecordingError('A capture timestamp with a timezone is required.') from exc
    if timestamp.tzinfo is None:
        raise RecordingError('A capture timestamp with a timezone is required.')
    recordings = manifest.get('recordings')
    if not isinstance(recordings, list) or not recordings:
        raise RecordingError('The manifest must contain recordings.')
    entries: dict[str, tuple[RequestKey, RecordedResponse]] = {}
    keys: set[RequestKey] = set()
    for entry in recordings:
        name, request, response = parse_entry(entry, path.parent)
        if name in entries or request in keys:
            raise RecordingError('Recording ids and request keys must be unique.')
        entries[name] = (request, response)
        keys.add(request)
    case_values = json_object(manifest.get('cases'))
    if not case_values:
        raise RecordingError('The manifest must link recordings to cases.')
    cases: dict[str, tuple[str, ...]] = {}
    for case_id, names in case_values.items():
        if not case_id or not isinstance(names, list) or not names:
            raise RecordingError('Each case must list at least one recording id.')
        checked_names: list[str] = []
        for name in names:
            if not isinstance(name, str) or name not in entries or name in checked_names:
                raise RecordingError('A case names an absent or repeated recording id.')
            checked_names.append(name)
        cases[case_id] = tuple(checked_names)
    return RecordedResponses(data_kind, captured_at, entries, cases)


def main() -> None:
    """
    Checks selected cases locally and reports whether their data is synthetic.

    Called by: __main__
    """
    parser = argparse.ArgumentParser(description='Validate saved GET responses; never contacts a service.')
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--case', action='append', required=True, dest='cases')
    parser.add_argument('--require-recorded', action='store_true', help='Reject a manifest marked synthetic.')
    args = parser.parse_args()
    try:
        recordings = load_recordings(args.manifest)
        if args.require_recorded and recordings.data_kind != 'recorded':
            raise RecordingError('Authentic upstream recordings are still required; this manifest is synthetic.')
        counts = [len(recordings.for_case(case_id)) for case_id in args.cases]
    except RecordingError as exc:
        parser.exit(1, f'Recording check failed: {exc}\n')
    else:
        print(f'Validated {len(counts)} selected cases ({recordings.data_kind}); response counts: {counts}.')
        print('This checks saved files, not completeness of page inputs or agreement with the public site.')


if __name__ == '__main__':
    main()
