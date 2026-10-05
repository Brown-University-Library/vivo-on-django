"""
Changes stylesheet and script addresses when their local contents change.
"""

from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.contrib.staticfiles import finders
from django.templatetags.static import static


@lru_cache(maxsize=128)
def asset_digest(path: str, modified_ns: int, size: int) -> str:
    """
    Caches the content digest until a file's modification time or size changes.

    Called by: versioned_asset_url()
    """
    return sha256(Path(path).read_bytes()).hexdigest()[:16]


def versioned_asset_url(name: str) -> str:
    """
    Adds a content version while preserving the configured static URL.

    Missing assets keep their original URL so delivery failures remain visible.
    Called by: asset_urls.versioned_static()
    """
    result = static(name)
    path = finders.find(name)
    if isinstance(path, str):
        file_stat = Path(path).stat()
        digest = asset_digest(path, file_stat.st_mtime_ns, file_stat.st_size)
        parts = urlsplit(result)
        query = parse_qsl(parts.query, keep_blank_values=True)
        query.append(('v', digest))
        result = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
    return result


def collected_asset_differences(source_root: Path, collected_root: Path) -> list[str]:
    """
    Lists application stylesheets and scripts with missing, unreadable, or changed copies.

    Called by: checks.check_static_collection()
    """
    sources = sorted(path for path in source_root.rglob('*') if path.is_file() and path.suffix in {'.css', '.js'})
    if not sources:
        raise ValueError('Application stylesheets and scripts are unavailable.')
    differences: list[str] = []
    for source in sources:
        name = source.relative_to(source_root).as_posix()
        found = finders.find(name)
        selected_source = Path(found) if isinstance(found, str) else source
        try:
            if selected_source.read_bytes() != (collected_root / name).read_bytes():
                differences.append(name)
        except OSError:
            differences.append(name)
    return differences
