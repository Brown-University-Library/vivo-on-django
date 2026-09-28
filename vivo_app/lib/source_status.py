"""
Checks the public search record count through the selected Solr source.
"""

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.source_pages import SourceReader, response_object
from vivo_app.lib.source_requests import read_source, status_key


def status_data(mode: str, reader: SourceReader = read_source) -> dict[str, str]:
    """
    Builds the normal status response from one bounded Solr count request.

    Called by: views.home_status(), tests
    """
    source = response_object(status_key(), mode, reader)
    body = source.get('response')
    count = body.get('numFound') if isinstance(body, dict) else None
    if type(count) is not int or count <= 0:
        raise PageDataError('The status query found no searchable records.')
    return {'status': 'OK', 'message': f'{count} records found.'}
