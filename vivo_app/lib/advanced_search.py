"""
Builds the fielded search term used by the public advanced search form.
"""

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.source_requests import quoted


def advanced_search_query(title: str, name: str, department: str = '') -> str:
    """
    Combines entered title and name in the same order as the Rails form.

    Called by: views.advanced_search()
    """
    terms = []
    for field, value in (('title_t', title), ('department_t', department), ('name_t', name)):
        clean_value = value.strip()
        if clean_value:
            terms.append(f'{field}:{quoted(clean_value)}')
    result = ' AND '.join(terms)
    if len(result) > 300:
        raise PageDataError('The advanced search terms are too long.')
    return result
