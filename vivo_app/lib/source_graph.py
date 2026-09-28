"""
Reads visualization-service lists and graph data through live or recorded requests.
"""

import csv
import io
import json
import math
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


def graph_csv(value: dict[str, object], kind: str) -> str:
    """
    Writes the public graph download columns from connected nodes.

    Called by: views.visualization_network(), tests
    """
    graph = value.get('data') if kind == 'coauthors' else value.get('graph')
    if not isinstance(graph, dict):
        raise PageDataError('The visualization graph is unavailable.')
    nodes = graph.get('nodes')
    links = graph.get('links')
    if not isinstance(nodes, list) or not isinstance(links, list):
        raise PageDataError('The visualization graph is invalid.')
    if any(not isinstance(node, dict) or not isinstance(node.get('id'), str) for node in nodes):
        raise PageDataError('The visualization graph has an invalid node.')
    by_id = {node['id']: node for node in nodes if isinstance(node, dict)}
    if not links:
        return ''
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'name', 'info', 'collab_with', 'count'])
    for link in links:
        if not isinstance(link, dict):
            raise PageDataError('The visualization graph has an invalid link.')
        source_id, target_id = link.get('source'), link.get('target')
        if not isinstance(source_id, str) or not isinstance(target_id, str):
            raise PageDataError('The visualization graph has an invalid link.')
        source = by_id.get(source_id)
        target = by_id.get(target_id)
        if source is None or target is None:
            raise PageDataError('The visualization graph refers to a missing node.')
        weight = link.get('weight') if kind == 'coauthors' else 1
        writer.writerow([source['id'], source.get('name'), source.get('group'), target['id'], weight])
    return output.getvalue()


def graph_page_data(value: dict[str, object], kind: str, identifier: str) -> dict[str, object]:
    """
    Places a source graph into a readable local SVG network page.

    Called by: views.visualization_network(), tests
    """
    graph = value.get('data') if kind == 'coauthors' else value.get('graph')
    if not isinstance(graph, dict):
        raise PageDataError('The visualization graph is unavailable.')
    source_nodes = graph.get('nodes')
    source_links = graph.get('links')
    if not isinstance(source_nodes, list) or not isinstance(source_links, list):
        raise PageDataError('The visualization graph is invalid.')
    nodes: list[dict[str, object]] = []
    positions: dict[str, tuple[float, float]] = {}
    for index, node in enumerate(source_nodes):
        if not isinstance(node, dict) or not isinstance(node.get('id'), str):
            raise PageDataError('The visualization graph has an invalid node.')
        angle = 2 * math.pi * index / max(len(source_nodes), 1)
        x, y = 440 + 300 * math.cos(angle), 350 + 270 * math.sin(angle)
        positions[node['id']] = (x, y)
        nodes.append(
            {
                'id': node['id'],
                'name': node.get('name', ''),
                'x': x,
                'y': y,
                'color': '#8f2d2d'
                if node['id'] in {identifier, 'http://vivo.brown.edu/individual/' + identifier}
                else '#597c99',
            }
        )
    links: list[dict[str, float]] = []
    for link in source_links:
        if not isinstance(link, dict):
            raise PageDataError('The visualization graph has an invalid link.')
        source_id, target_id = link.get('source'), link.get('target')
        if not isinstance(source_id, str) or not isinstance(target_id, str):
            raise PageDataError('The visualization graph has an invalid link.')
        if source_id not in positions or target_id not in positions:
            raise PageDataError('The visualization graph has an invalid link.')
        x1, y1 = positions[source_id]
        x2, y2 = positions[target_id]
        links.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2})
    return {'id': identifier, 'kind': kind, 'nodes': nodes, 'links': links, 'updated': value.get('updated', '')}
