"""
Builds the fielded search term used by the public advanced search form.
"""

from urllib.parse import quote

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.source_requests import quoted


def advanced_search_query(title: str, name: str, department: str = '', *, url_encoded: bool = False) -> str:
    """
    Combines entered fields in the Rails order and optionally encodes the redirect query.

    Encoded terms retain spaces inside values and use the reference +AND+ separators.

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
    if url_encoded:
        result = '+AND+'.join(quote(term, safe=':') for term in terms)
    return result
