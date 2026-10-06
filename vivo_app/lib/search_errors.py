"""
Preserves demonstrated search failures without sending malformed source queries.
"""

import re

from vivo_app.lib.prepared_data import PageDataError


class ReferenceSearchError(PageDataError):
    """
    Identifies a filter for which the reference search returns its error page.
    """


def check_reference_filter_markup(filters: list[tuple[str, str]]) -> None:
    """
    Preserves the reference failure for publication entity tags with quoted attributes.

    Called by: source_pages.search_inputs()
    """
    ## The reference inserts these attribute quotes into a quoted Solr filter unchanged.
    ## Keep that demonstrated error response without weakening ordinary source-query quoting.
    if any(field == 'published_in' and re.search(r'<html_ent\s+[^>]*="[^>]*>', value) for field, value in filters):
        raise ReferenceSearchError('The reference cannot search this publication annotation.')
