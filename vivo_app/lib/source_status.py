"""
Checks the public search record count through the selected Solr source.
"""

import uuid

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.source_pages import SourceReader, response_object
from vivo_app.lib.source_requests import read_source, status_key


class NoSearchResultsError(PageDataError):
    """Identifies a valid status count with no searchable records."""


def status_data(mode: str, reader: SourceReader = read_source) -> dict[str, str]:
    """
    Builds the normal status response from one bounded Solr count request.

    Called by: views.home_status(), tests
    """
    source = response_object(status_key(), mode, reader)
    body = source.get('response')
    count = body.get('numFound') if isinstance(body, dict) else None
    if type(count) is not int:
        raise PageDataError('The status query returned an invalid record count.')
    if count <= 0:
        raise NoSearchResultsError('The status query found no searchable records.')
    return {'status': 'OK', 'message': f'{count} records found.'}


def status_error_data(error: Exception) -> dict[str, str]:
    """
    Builds the reference error text with a generated tracking ID.

    Called by: views.home_status()
    """
    error_id = str(uuid.uuid4())
    if isinstance(error, NoSearchResultsError):
        message = f'No search results were found ({error_id})'
    else:
        message = f'Exception was found. See the log file ({error_id}).'
    return {'status': 'ERROR', 'message': message}
