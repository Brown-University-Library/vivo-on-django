"""
Defines source request/response values and validates external input files.
"""

from dataclasses import dataclass
from pathlib import Path


class SourceDataError(ValueError):
    """Identifies invalid source data or external input files."""


@dataclass(frozen=True)
class RequestKey:
    """Identifies a GET request using decoded, ordered query pairs."""

    service: str
    path: str
    query: tuple[tuple[str, str], ...] = ()
    headers: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class SourceResponse:
    """Retains the status, headers, and unchanged bytes of a source response."""

    status: int
    headers: tuple[tuple[str, str], ...]
    body: bytes


def json_object(value: object) -> dict[str, object]:
    """
    Checks that a JSON value contains an object with string keys.

    Called by: source consumers and developer tools
    """
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise SourceDataError('Expected a JSON object with string keys.')
    result: dict[str, object] = dict(value)
    return result


def external_path(path: Path) -> Path:
    """
    Rejects files and directories inside a Git checkout.

    Called by: source consumers and developer tools
    """
    resolved: Path = path.resolve()
    if any((parent / '.git').exists() for parent in (resolved, *resolved.parents)):
        raise SourceDataError('Keep input files outside Git checkouts.')
    return resolved
