"""
Reads visualization-service lists and graph data through live or recorded requests.
"""

import json
import re
from collections.abc import Callable

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RequestKey
from vivo_app.lib.source_requests import read_source

GraphReader = Callable[[RequestKey, str], RecordedResponse]


def visualization_key(kind: str, identifier: str = '') -> RequestKey:
    """
    Limits visualization requests to the public graph families and safe identifiers.

    Called by: visualization_list(), visualization_graph(), tests
    """
    if kind not in {'coauthors', 'collaborators'} or (
        identifier and re.fullmatch(r'[A-Za-z0-9_-]{1,80}', identifier) is None
    ):
        raise PageDataError('The requested visualization is unsupported.')
    path = '/' + kind + '/' + identifier
    query = (('ds', 'graph'),) if kind == 'coauthors' and identifier else ()
    return RequestKey('viz', path, query)


def visualization_response(key: RequestKey, mode: str, reader: GraphReader) -> dict[str, object]:
    """
    Parses a visualization-service response without substituting page JSON.

    Called by: visualization_list(), visualization_graph()
    """
    response = reader(key, mode)
    try:
        value: object = json.loads(response.body)
    except (ValueError, UnicodeError) as exc:
        raise PageDataError('The visualization service returned invalid JSON.') from exc
    if not isinstance(value, dict) or any(not isinstance(name, str) for name in value):
        raise PageDataError('The visualization service returned an invalid object.')
    return value


def visualization_list(kind: str, mode: str, reader: GraphReader | None = None) -> dict[str, object]:
    """
    Reads one graph-availability list used by public profile flags.

    Called by: profile_json_data(), tests
    """
    if reader is None:
        reader = read_source
    return visualization_response(visualization_key(kind), mode, reader)


def visualization_graph(kind: str, identifier: str, mode: str, reader: GraphReader | None = None) -> dict[str, object]:
    """
    Reads one graph for a retained visualization JSON route.

    Called by: views.visualization_graph_json(), tests
    """
    if kind == 'collaborators' and (
        identifier.startswith('team-') or identifier in {'org-brown-univ-dept124', 'org-brown-univ-dept148'}
    ):
        raise PageDataError('This collaboration graph needs custom member processing that is not connected yet.')
    if reader is None:
        reader = read_source
    value = visualization_response(visualization_key(kind, identifier), mode, reader)
    graph = value.get('graph') if kind == 'collaborators' else value.get('data')
    if not isinstance(graph, dict) or not isinstance(graph.get('nodes'), list) or not isinstance(graph.get('links'), list):
        raise PageDataError('The visualization service returned an invalid graph.')
    return value
