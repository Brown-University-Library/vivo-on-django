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
