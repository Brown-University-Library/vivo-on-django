"""
Defines failures shared by source processing and page rendering.
"""


class PageDataError(ValueError):
    """Identifies unavailable or invalid page data without a fallback."""


class MissingRecordError(PageDataError):
    """Identifies an exact source lookup with no matching public record."""
