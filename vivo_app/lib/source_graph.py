"""
Reads visualization-service lists and graph data through live or recorded requests.
"""

import csv
import datetime
import io
import json
import math
import re
import time
from collections.abc import Callable

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RequestKey
from vivo_app.lib.source_formats import faculty_item_from_doc
from vivo_app.lib.source_pages import documents, entries, first_text, record_data, record_id, response_object
from vivo_app.lib.source_requests import graph_root_key, member_details_key, profile_key, read_source
from vivo_app.lib.source_teams import CUSTOM_ORGANIZATION_IDS, custom_organization_members, team_definition

GraphReader = Callable[[RequestKey, str], RecordedResponse]
GRAPH_MEMBER_BATCH_SIZE = 20


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
    if reader is None:
        reader = read_source
    if kind == 'collaborators' and (identifier.startswith('team-') or identifier in CUSTOM_ORGANIZATION_IDS):
        return custom_collaboration_graph(identifier, mode, reader)
    value = visualization_response(visualization_key(kind, identifier), mode, reader)
    if not value:
        return value
    graph = value.get('graph') if kind == 'collaborators' else value.get('data')
    if not isinstance(graph, dict) or not isinstance(graph.get('nodes'), list) or not isinstance(graph.get('links'), list):
        raise PageDataError('The visualization service returned an invalid graph.')
    return value


def custom_graph_members(identifier: str, mode: str, reader: GraphReader) -> tuple[str, list[str]]:
    """
    Reads the same configured and organization members used by custom collaboration graphs.

    Called by: custom_collaboration_graph()
    """
    if identifier.startswith('team-'):
        name, members = team_definition(identifier)
    else:
        response = response_object(profile_key(identifier), mode, reader)
        docs, _ = documents(response)
        if not docs or first_text(docs[0].get('record_type')) != 'ORGANIZATION':
            raise PageDataError('The custom collaboration organization is unavailable.')
        item = record_data(docs[0])
        name = first_text(item.get('name'))
        members = [record_id({'id': first_text(row.get('faculty_uri'))}) for row in entries(item, 'people')]
        members.extend(custom_organization_members(identifier, mode, reader))
    result = list(dict.fromkeys(members))
    if not name or not result or len(result) > 500:
        raise PageDataError('The custom collaboration member list is unavailable or too large.')
    return name, result


def custom_graph_records(
    identifiers: list[str], mode: str, reader: GraphReader, require_all: bool, full: bool = False
) -> dict[str, dict[str, object]]:
    """
    Reads small member batches, retaining complete Solr documents for graph roots.

    Called by: custom_collaboration_graph()
    """
    if len(identifiers) > 500:
        raise PageDataError('The collaboration graph needs too many member records.')
    result: dict[str, dict[str, object]] = {}
    batch_size = 5 if full else GRAPH_MEMBER_BATCH_SIZE
    for start in range(0, len(identifiers), batch_size):
        batch = identifiers[start : start + batch_size]
        if start and mode == 'live':
            time.sleep(0.25)
        response = response_object(graph_root_key(batch) if full else member_details_key(batch), mode, reader)
        docs, _ = documents(response)
        for doc in docs:
            member_id = record_id(doc)
            if member_id not in batch or first_text(doc.get('record_type')) != 'PEOPLE' or member_id in result:
                raise PageDataError('Solr returned an unrelated collaboration member.')
            record_data(doc)
            result[member_id] = doc
    if require_all and set(result) != set(identifiers):
        raise PageDataError('Solr did not return every custom collaboration member.')
    return result


def add_custom_node(nodes: dict[str, dict[str, object]], uri: str, label: str, group: str, title: str, level: int) -> None:
    """
    Keeps the closest level and first available group for a collaboration node.

    Called by: custom_collaboration_graph(), add_custom_collaborators()
    """
    current = nodes.get(uri)
    if current is None:
        nodes[uri] = {'id': uri, 'name': label, 'group': group or None, 'title': title, 'level': level}
    else:
        old_level = current.get('level')
        if isinstance(old_level, int):
            current['level'] = min(old_level, level)
        if not current.get('group') and group:
            current['group'] = group


def add_custom_collaborators(
    nodes: dict[str, dict[str, object]],
    links: dict[tuple[str, str], dict[str, object]],
    source_uri: str,
    person: dict[str, object],
    level: int,
) -> list[str]:
    """
    Adds one person's collaborators and returns Brown IDs that can be expanded.

    Called by: custom_collaboration_graph()
    """
    neighbors: list[str] = []
    prefix = 'http://vivo.brown.edu/individual/'
    for collaborator in entries(person, 'collaborators'):
        uri = first_text(collaborator.get('uri'))
        if not uri or any(ord(character) < 32 for character in uri):
            continue
        add_custom_node(
            nodes,
            uri,
            first_text(collaborator.get('name')),
            first_text(collaborator.get('org_name')),
            first_text(collaborator.get('title')),
            level,
        )
        pair = (source_uri, uri)
        if pair in links:
            old_weight = links[pair].get('weight')
            if isinstance(old_weight, int):
                links[pair]['weight'] = old_weight + 1
        else:
            links[pair] = {'source': source_uri, 'target': uri, 'weight': 1}
        if level == 1 and uri.startswith(prefix):
            neighbor_id = uri.removeprefix(prefix)
            if re.fullmatch(r'[A-Za-z0-9_-]{1,80}', neighbor_id):
                neighbors.append(neighbor_id)
    return neighbors


def custom_collaboration_graph(identifier: str, mode: str, reader: GraphReader) -> dict[str, object]:
    """
    Calculates a two-level team or specialized-organization graph from Solr profiles.

    Called by: visualization_graph()
    """
    name, member_ids = custom_graph_members(identifier, mode, reader)
    roots = custom_graph_records(member_ids, mode, reader, False, full=True)
    member_ids = [member_id for member_id in member_ids if member_id in roots]
    if not member_ids:
        raise PageDataError('The custom collaboration organization has no available member records.')
    prefix = 'http://vivo.brown.edu/individual/'
    nodes: dict[str, dict[str, object]] = {}
    links: dict[tuple[str, str], dict[str, object]] = {}

    neighbors: list[str] = []
    people = {member_id: record_data(roots[member_id]) for member_id in member_ids}
    coauthors = visualization_list('coauthors', mode, reader)
    collaborators = (
        visualization_list('collaborators', mode, reader)
        if any(entries(person, 'collaborators') for person in people.values())
        else {}
    )
    for member_id in member_ids:
        person = people[member_id]
        uri = prefix + member_id
        group = first_text(person.get('org_label')) if identifier == 'team-advctr' else name
        add_custom_node(nodes, uri, first_text(person.get('name')), group, first_text(person.get('title')), 0)
        nodes[uri]['faculty'] = {
            'solr_doc': roots[member_id],
            'json_txt': person,
            'item': faculty_item_from_doc(roots[member_id], coauthors, collaborators),
            'errors': [],
        }
    for member_id in member_ids:
        neighbors.extend(add_custom_collaborators(nodes, links, prefix + member_id, people[member_id], 1))
    missing_neighbors = sorted(set(neighbors) - set(roots))
    second_level = custom_graph_records(missing_neighbors, mode, reader, False) if missing_neighbors else {}
    for neighbor_id in neighbors:
        doc = roots.get(neighbor_id) or second_level.get(neighbor_id)
        if doc is not None:
            person = record_data(doc)
            add_custom_node(
                nodes,
                prefix + neighbor_id,
                first_text(person.get('name')),
                first_text(person.get('org_label')),
                first_text(person.get('title')),
                0 if neighbor_id in roots else 1,
            )
            add_custom_collaborators(nodes, links, prefix + neighbor_id, person, 2)
    yesterday = datetime.datetime.now(tz=datetime.UTC).date() - datetime.timedelta(days=1)
    return {
        'graph': {'nodes': list(nodes.values()), 'links': list(links.values())},
        'rabid': identifier,
        'updated': yesterday.isoformat(),
    }


def graph_subject_data(kind: str, identifier: str, mode: str, reader: GraphReader | None = None) -> dict[str, str]:
    """
    Reads the person or organization heading shown on a source-backed graph page.

    Called by: views.visualization_network()
    """
    if reader is None:
        reader = read_source
    if identifier.startswith('team-'):
        if kind != 'collaborators':
            raise PageDataError('A team has no coauthor network.')
        name, _ = team_definition(identifier)
        return {'name': name, 'page_title': name, 'title': '', 'type': 'TEAM'}
    response = response_object(profile_key(identifier), mode, reader)
    docs, _ = documents(response)
    if not docs or record_id(docs[0]) != identifier:
        raise PageDataError('The visualization profile is unavailable.')
    doc = docs[0]
    record_type = first_text(doc.get('record_type'))
    if record_type not in ({'PEOPLE'} if kind == 'coauthors' else {'PEOPLE', 'ORGANIZATION'}):
        raise PageDataError('The requested record has no matching visualization page.')
    item = record_data(doc)
    name = first_text(doc.get('display_name_s')) or first_text(item.get('name'))
    if not name:
        raise PageDataError('The visualization profile has no display name.')
    return {
        'name': name,
        'page_title': first_text(item.get('name')) or name,
        'title': first_text(item.get('title')),
        'type': record_type,
    }


def graph_csv(value: dict[str, object], kind: str) -> str:
    """
    Writes the public graph download columns from connected nodes.

    Called by: views.visualization_network(), tests
    """
    if not value:
        return ''
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
    writer = csv.writer(output, lineterminator='\n')
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
        identifier = value.get('rabid')
        is_custom = isinstance(identifier, str) and (identifier.startswith('team-') or identifier in CUSTOM_ORGANIZATION_IDS)
        weight = link.get('weight') if kind == 'coauthors' or is_custom else 1
        writer.writerow([source['id'], source.get('name'), source.get('group'), target['id'], weight])
    return output.getvalue()


def graph_page_data(
    value: dict[str, object], kind: str, identifier: str, subject: dict[str, str] | None = None
) -> dict[str, object]:
    """
    Places a source graph into a readable local SVG network page.

    Called by: views.visualization_network(), tests
    """
    graph = (value.get('data') if kind == 'coauthors' else value.get('graph')) if value else {'nodes': [], 'links': []}
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
    return {
        'id': identifier,
        'kind': kind,
        'name': subject['name'] if subject else identifier,
        'page_title': subject['page_title'] if subject else identifier,
        'title': subject['title'] if subject else '',
        'type': subject['type'] if subject else 'PEOPLE',
        'nodes': nodes,
        'links': links,
        'source': graph,
        'updated': value.get('updated', ''),
    }
