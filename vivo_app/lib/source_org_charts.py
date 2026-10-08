"""
Builds organization publication and research-area charts from Solr member records.
"""

import csv
import datetime
import io
import time
from collections import Counter

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.source_pages import (
    CUSTOM_ORGANIZATION_IDS,
    SourceReader,
    documents,
    first_text,
    organization_members,
    publication_year,
    record_data,
    record_id,
    response_object,
)
from vivo_app.lib.source_requests import chart_member_key, profile_key, read_source
from vivo_app.lib.source_teams import custom_organization_members, team_definition


def organization_chart_members(
    identifier: str, mode: str, reader: SourceReader | None = None
) -> tuple[str, list[tuple[str, dict[str, object], str]]]:
    """
    Reads one organization and its distinct members for either chart.

    Called by: publication_history_data(), research_areas_data()
    """
    if reader is None:
        reader = read_source
    if identifier.startswith('team-'):
        name, member_ids = team_definition(identifier)
    else:
        response = response_object(profile_key(identifier), mode, reader)
        docs, _ = documents(response)
        if not docs or record_id(docs[0]) != identifier or first_text(docs[0].get('record_type')) != 'ORGANIZATION':
            raise PageDataError('The requested chart organization is unavailable.')
        organization = record_data(docs[0])
        name = first_text(organization.get('name')) or first_text(docs[0].get('display_name_s'))
        extras = custom_organization_members(identifier, mode, reader)
        members = organization_members(organization, extras, mode, reader)
        members = sorted(
            members,
            key=lambda row: (
                first_text(row.get('label'))
                if identifier in CUSTOM_ORGANIZATION_IDS
                else first_text(row.get('label')).upper()
            ),
        )
        member_ids = list(dict.fromkeys(record_id({'id': first_text(row.get('faculty_uri'))}) for row in members))
    if not name or len(member_ids) > 500:
        raise PageDataError('The chart organization has no usable member list.')
    found: dict[str, tuple[dict[str, object], str]] = {}
    ## preserves the reference's twenty-member batches and each response's faculty order.
    for start in range(0, len(member_ids), 20):
        if start and mode == 'live':
            time.sleep(0.25)
        batch = member_ids[start : start + 20]
        response = response_object(chart_member_key(batch), mode, reader)
        docs, _ = documents(response)
        for doc in docs:
            member_id = record_id(doc)
            if member_id not in batch or first_text(doc.get('record_type')) != 'PEOPLE' or member_id in found:
                raise PageDataError('Solr returned an unrelated chart member.')
            found[member_id] = (record_data(doc), first_text(doc.get('display_name_s')))
    result = [(member_id, person, display) for member_id, (person, display) in found.items()]
    return name, result


def publication_history_data(
    identifier: str, mode: str, reader: SourceReader | None = None
) -> tuple[str, dict[str, object]]:
    """
    Counts each member's valid publications by year in the public chart format.

    Called by: views.visualization_publications(), tests
    """
    name, members = organization_chart_members(identifier, mode, reader)
    current_year = datetime.datetime.now().astimezone().year
    summaries: list[tuple[str, str, str, dict[int, int]]] = []
    all_years: set[int] = set()
    for member_id, person, _ in members:
        publications = person.get('contributor_to')
        if not isinstance(publications, list) or not publications or any(not isinstance(row, dict) for row in publications):
            continue
        counts: dict[int, int] = {}
        for publication in publications:
            year_text = publication_year(publication)
            year = int(year_text) if year_text else 0
            if year and year <= current_year:
                counts[year] = counts.get(year, 0) + 1
                all_years.add(year)
        summaries.append((member_id, first_text(person.get('name')), first_text(person.get('title')), counts))
    columns = [member_id for member_id, _, _, counts in summaries if counts]
    nodes = [
        {'faculty_id': member_id, 'name': member_name, 'group': title}
        for member_id, member_name, title, counts in summaries
        if counts
    ]
    matrix: list[dict[str, int]] = []
    for year in range(min(all_years), max(all_years) + 1) if all_years else []:
        row = {'year': year, 'total': 0}
        for member_id, _, _, counts in summaries:
            if not counts:
                continue
            count = counts.get(year, 0)
            row[member_id] = count
            row['total'] += count
        if row['total']:
            matrix.append(row)
    result: dict[str, object] = {
        'matrix': matrix,
        'years': [str(row['year']) for row in matrix],
        'columns': columns,
        'nodes': nodes,
    }
    return name, result


def publication_history_csv(value: dict[str, object]) -> str:
    """
    Writes the chart's public CSV header and yearly rows.

    Called by: views.visualization_publications(), tests
    """
    columns = value.get('columns')
    matrix = value.get('matrix')
    if (
        not isinstance(columns, list)
        or any(not isinstance(column, str) for column in columns)
        or not isinstance(matrix, list)
    ):
        raise PageDataError('The publication chart is invalid.')
    output = io.StringIO()
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(['year', 'year_total', *columns])
    for row in matrix:
        if not isinstance(row, dict):
            raise PageDataError('A publication chart year is invalid.')
        writer.writerow([row.get('year', ''), row.get('total', ''), *(row.get(column, '') for column in columns)])
    return output.getvalue().removesuffix('\n')


def research_areas_data(identifier: str, mode: str, reader: SourceReader | None = None) -> tuple[str, dict[str, object]]:
    """
    Links members to research areas named by at least two members.

    Called by: views.visualization_research(), tests
    """
    name, members = organization_chart_members(identifier, mode, reader)
    areas_by_member: list[list[str]] = []
    for _, person, _ in members:
        raw = person.get('research_areas')
        if raw is None:
            raw = []
        areas = [area for area in raw if isinstance(area, str) and area.strip()] if isinstance(raw, list) else []
        areas_by_member.append(sorted(areas, key=str.lower))
    counts = Counter(area for areas in areas_by_member for area in areas)
    shared = sorted((area for area, count in counts.items() if count > 1), key=lambda area: counts[area])
    shared.reverse()
    areas_to_ids = {area: len(members) + index + 1 for index, area in enumerate(shared)}
    people_nodes: list[dict[str, object]] = []
    area_nodes: list[dict[str, object]] = []
    links: list[dict[str, int]] = []
    for index, ((member_id, person, display), areas) in enumerate(zip(members, areas_by_member, strict=True), 1):
        shared_count = 0
        for area in areas:
            area_id = areas_to_ids.get(area)
            if area_id is not None:
                links.append({'source': index, 'target': area_id, 'value': 1})
                shared_count += 1
        people_nodes.append(
            {
                'id': index,
                'nodeName': member_id,
                'display': display or first_text(person.get('name')),
                'incoming': [],
                'nodeValue': shared_count if shared_count else 0.9,
                'areas': ', '.join(areas),
            }
        )
    for area in shared:
        area_nodes.append(
            {
                'id': areas_to_ids[area],
                'nodeName': area,
                'display': area,
                'incoming': [],
                'nodeValue': counts[area],
                'areas': None,
            }
        )
    return name, {'nodes': [people_nodes, area_nodes], 'links': links}
