"""
Defines failures shared by source processing and page rendering.
"""


class PageDataError(ValueError):
    """Identifies unavailable or invalid page data without a fallback."""


class MissingRecordError(PageDataError):
    """Identifies an exact source lookup with no matching public record."""


class SourceTimeoutError(PageDataError):
    """Identifies a source request that exceeded its connection or response wait limit."""


class ChartRetryError(PageDataError):
    """
    Identifies a brief wait before attempting a failed chart again.
    """

    def __init__(self, retry_after: int, cached: bool) -> None:
        """
        Keeps the remaining wait and whether the original failure has already been reported.

        Called by: organization_chart_cache.cached_chart(), organization_chart_cache.read_cached_chart()
        """
        super().__init__('Chart data is temporarily unavailable; please try again shortly.')
        self.retry_after = retry_after
        self.cached = cached


class InvalidDocumentError(PageDataError):
    """Identifies a successful document response that fails the PDF checks."""
