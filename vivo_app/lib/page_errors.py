"""
Defines failures shared by source processing and page rendering.
"""


class PageDataError(ValueError):
    """Identifies unavailable or invalid page data without a fallback."""


class MissingRecordError(PageDataError):
    """Identifies an exact source lookup with no matching public record."""


class SourceTimeoutError(PageDataError):
    """Identifies a source request that exceeded its connection or response wait limit."""


class InvalidDocumentError(PageDataError):
    """Identifies a successful document response that fails the PDF checks."""
