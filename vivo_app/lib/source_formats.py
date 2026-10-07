"""
Builds public structured responses from live or recorded source records.
"""

import json
from collections.abc import Callable
from datetime import date

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RequestKey
from vivo_app.lib.source_pages import (
    documents,
    entries,
    first_text,
    organization_members,
    publication_year,
    record_data,
    record_id,
    response_object,
    website_rank,
)
from vivo_app.lib.source_requests import image_path, member_key, profile_export_key, profile_key, read_source, source_origin

FormatReader = Callable[[RequestKey, str], RecordedResponse]


def profile_json_text(data: dict[str, object]) -> str:
    """
    Encodes public profile and chart values with Rails' compact HTML escaping.

    Called by: views.display_show(), views.visualization_publications(), tests
    """
    result = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    for character, escaped in (
        ('<', r'\u003c'),
        ('>', r'\u003e'),
        ('&', r'\u0026'),
        ('\u2028', r'\u2028'),
        ('\u2029', r'\u2029'),
    ):
        result = result.replace(character, escaped)
    return result


def raw_record_json_data(identifier: str, mode: str, reader: FormatReader | None = None) -> dict[str, object]:
    """
    Returns the original parsed Solr record for a person or organization.

    Called by: views.display_show(), tests
    """
    if reader is None:
        reader = read_source
    response = response_object(profile_key(identifier), mode, reader)
    docs, _ = documents(response)
    if (
        not docs
        or record_id(docs[0]) != identifier
        or first_text(docs[0].get('record_type'))
        not in {
            'PEOPLE',
            'ORGANIZATION',
        }
    ):
        raise PageDataError('The requested source record is unavailable.')
    return record_data(docs[0])


def organization_json_data(
    identifier: str, mode: str, reader: FormatReader | None = None, extra_member_ids: list[str] | None = None
) -> dict[str, object]:
    """
    Converts an organization record and its member portraits for public JSON.

    Called by: views.display_show(), tests
    """
    if reader is None:
        reader = read_source
    response = response_object(profile_key(identifier), mode, reader)
    docs, _ = documents(response)
    if not docs or record_id(docs[0]) != identifier or first_text(docs[0].get('record_type')) != 'ORGANIZATION':
        raise PageDataError('The requested source record is not an organization.')
    doc = docs[0]
    raw = record_data(doc)
    uri = first_text(raw.get('uri')) or first_text(doc.get('id'))
    path = image_path(doc.get('thumbnail_file_path_s'))
    members = organization_members(raw, extra_member_ids or [], mode, reader)
    ids = list(dict.fromkeys(record_id({'id': first_text(row.get('faculty_uri'))}) for row in members))
    portraits: dict[str, str] = {}
    seen_ids: set[str] = set()
    for start in range(0, len(ids), 20):
        batch = ids[start : start + 20]
        member_response = response_object(member_key(batch), mode, reader)
        member_docs, _ = documents(member_response)
        for member_doc in member_docs:
            member_id = record_id(member_doc)
            if member_id not in batch or first_text(member_doc.get('record_type')) != 'PEOPLE' or member_id in seen_ids:
                raise PageDataError('Solr returned an unrelated organization member.')
            seen_ids.add(member_id)
            member_path = image_path(member_doc.get('thumbnail_file_path_s'))
            if member_path:
                portraits[member_id] = source_origin('images') + member_path
    people: list[dict[str, object]] = []
    for row in sorted(members, key=lambda item: first_text(item.get('label')).upper()):
        faculty_uri = first_text(row.get('faculty_uri'))
        member_id = record_id({'id': faculty_uri})
        people.append(
            {
                'id': faculty_uri,
                'faculty_uri': faculty_uri,
                'label': first_text(row.get('label')),
                'general_position': first_text(row.get('general_position')),
                'specific_position': first_text(row.get('specific_position')),
                'thumbnail_url': portraits.get(member_id, 'person_placeholder.jpg'),
            }
        )
    web_pages: list[dict[str, object]] = []
    for row in entries(raw, 'web_pages'):
        url = first_text(row.get('url')).strip()
        web_pages.append(
            {
                'id': first_text(row.get('uri')),
                'uri': first_text(row.get('uri')),
                'rank': website_rank(row.get('rank')),
                'url': url,
                'text': website_text(row),
            }
        )
    return {
        'id': uri,
        'record_type': first_text(raw.get('record_type')) or 'ORGANIZATION',
        'uri': uri,
        'name': first_text(raw.get('name')),
        'overview': first_text(raw.get('overview')),
        'thumbnail': source_origin('images') + path if path else None,
        'people': people,
        'web_pages': web_pages,
        'faculty': [],
    }


def model_scalar(value: object) -> object:
    """
    Preserves scalar values and takes the first array value as Rails models do.

    Called by: website_text(), dated_entries(), publication_entries(), faculty_item_from_doc()
    """
    result = value
    if isinstance(value, list):
        result = value[0] if value else None
    return result


def website_text(row: dict[str, object]) -> str:
    """
    Trims website text while preserving explicit blank labels from Rails.

    Called by: organization_json_data(), faculty_item_from_doc()
    """
    value = model_scalar(row.get('text'))
    if value is None or value is False:
        value = row.get('url')
    return first_text(value).strip()


def sorted_profile_text_values(value: object) -> list[str | None | bool]:
    """
    Sorts nullable profile text lists with the values accepted by Rails.

    Unsupported entries produce Rails' empty-list result for the entire JSON field.

    Called by: faculty_item_from_doc()
    """
    result: list[str | None | bool] = []
    if isinstance(value, list) and all(item is None or item is False or isinstance(item, str) for item in value):
        result = sorted(value, key=lambda item: item.lower() if isinstance(item, str) else '')
    return result


def dated_entries(raw: dict[str, object], field: str, names: tuple[str, ...]) -> list[dict[str, object]]:
    """
    Converts and sorts profile entries with optional start and end dates.

    Called by: profile_json_data()
    """
    converted: list[dict[str, object]] = []
    for row in entries(raw, field):
        item = (
            {name: model_scalar(value) for name, value in row.items() if name in names}
            if field == 'training'
            else {name: model_scalar(row.get(name, None if name in {'start_date', 'end_date'} else '')) for name in names}
        )
        if field == 'training':
            item.setdefault('start_date', None)
            item.setdefault('end_date', None)
        for name in ('start_date', 'end_date'):
            if name in item:
                value = item[name]
                try:
                    item[name] = date.fromisoformat(value.split('T', 1)[0]).isoformat() if isinstance(value, str) else None
                except ValueError:
                    item[name] = None
        if 'id' in item:
            item['id'] = model_scalar(row.get('uri', ''))
        if field == 'appointments':
            org_name = row.get('hospital_name')
            if org_name is None or org_name is False:
                org_name = row.get('org_name')
            item['org_name'] = '' if org_name is None or org_name is False else org_name
        converted.append(item)
    converted.sort(key=lambda row: str(row.get('start_date') or '1900-01-01'))
    converted.reverse()
    return converted


def publication_entries(raw: dict[str, object]) -> list[dict[str, object]]:
    """
    Converts publications and sorts by descending year, then title.

    Called by: profile_json_data()
    """
    names = (
        'uri',
        'authors',
        'title',
        'volume',
        'issue',
        'date',
        'pages',
        'published_in',
        'venue',
        'type',
        'doi',
        'pub_med_id',
        'external_url',
        'book',
        'location_label',
        'publisher_label',
        'editors',
    )
    converted: list[dict[str, object]] = []
    for row in entries(raw, 'contributor_to'):
        item = {name: model_scalar(value) for name, value in row.items() if name in names}
        item['title'] = first_text(model_scalar(row.get('title')))
        year = publication_year(item)
        item['year'] = int(year) if year else None
        item['external_url'] = row.get('url')
        converted.append(item)
    converted.sort(
        key=lambda row: (-(row['year'] if isinstance(row['year'], int) else 0), first_text(row.get('title')).strip().lower())
    )
    return converted


def profile_json_data(identifier: str, mode: str, reader: FormatReader | None = None) -> dict[str, object]:
    """
    Converts a person Solr record and graph lists to the public profile JSON fields.

    Called by: views.display_show(), tests
    """
    if reader is None:
        reader = read_source
    response = response_object(profile_export_key(identifier), mode, reader)
    docs, _ = documents(response)
    if not docs or record_id(docs[0]) != identifier or first_text(docs[0].get('record_type')) != 'PEOPLE':
        raise PageDataError('The requested source record is not a person.')
    from vivo_app.lib.source_graph import visualization_list

    try:
        coauthors = visualization_list('coauthors', mode, reader)
    except PageDataError:
        if mode == 'replay':
            raise
        coauthors = {}
    collaborators = {}
    if entries(record_data(docs[0]), 'collaborators'):
        try:
            collaborators = visualization_list('collaborators', mode, reader)
        except PageDataError:
            if mode == 'replay':
                raise
    return faculty_item_from_doc(docs[0], coauthors, collaborators)


def faculty_item_from_doc(
    doc: dict[str, object], coauthors: dict[str, object], collaborators: dict[str, object]
) -> dict[str, object]:
    """
    Converts one full person document for profile JSON and calculated graph roots.

    Called by: profile_json_data(), source_graph.custom_collaboration_graph()
    """
    raw = record_data(doc)
    item = dict(raw)
    item.pop('cv', None)
    defaults: dict[str, object] = {
        'record_type': 'PEOPLE',
        'affiliations_text': '',
        'affiliations': [],
        'awards': '',
        'collaborators': [],
        'contributor_to': [],
        'published_in': [],
        'education': [],
        'email': '',
        'funded_research': '',
        'name': '',
        'display_name': '',
        'org_label': '',
        'overview': '',
        'research_overview': '',
        'research_statement': '',
        'scholarly_work': '',
        'teacher_for': [],
        'teaching_overview': '',
        'title': '',
        'thumbnail': '',
        'research_areas': [],
        'on_the_web': [],
        'appointments': [],
        'hidden': False,
        'cv_link': None,
        'credentials': [],
        'training': [],
        'fis_updated': None,
        'profile_updated': None,
        'show_visualizations': False,
        'has_coauthors': False,
        'has_collaborators': False,
    }
    item = {name: item.get(name, default) for name, default in defaults.items()} | {
        'id': raw.get('id'),
        'uri': first_text(raw.get('uri')),
    }
    display_name = doc.get('display_name_s')
    if display_name is None:
        name = raw.get('name')
        display_name = '' if name is None or name is False else name
    item['display_name'] = display_name
    path = image_path(doc.get('thumbnail_file_path_s'))
    item['thumbnail'] = source_origin('images') + path if path else None
    item['fis_updated'] = doc.get('fis_updated_s')
    item['profile_updated'] = doc.get('profile_updated_s')
    item['show_visualizations'] = first_text(doc.get('show_visualizations_s')) == 'true'
    cv = entries(raw, 'cv')
    item['cv_link'] = cv[0].get('cv_link') if cv else None
    affiliations = entries(raw, 'affiliations')
    item['affiliations'] = [
        {
            'uri': model_scalar(row.get('uri', '')),
            'name': model_scalar(row.get('name', '')),
            'id': model_scalar(row.get('uri', '')),
            'thumbnail': None,
        }
        for row in sorted(affiliations, key=lambda row: first_text(row.get('name')).lower())
    ]
    education = entries(raw, 'education')
    sorted_education = sorted(education, key=lambda row: first_text(model_scalar(row.get('date'))))
    sorted_education.reverse()
    item['education'] = [
        {
            key: first_text(model_scalar(value)).strip() if key == 'school_name' else model_scalar(value)
            for key, value in row.items()
            if key in ('school_uri', 'date', 'degree', 'school_name')
        }
        for row in sorted_education
    ]
    web_pages = entries(raw, 'on_the_web')
    websites: list[dict[str, object]] = []
    for row in sorted(web_pages, key=lambda row: website_rank(model_scalar(row.get('rank')))):
        website = {name: model_scalar(value) for name, value in row.items() if name in ('uri', 'rank', 'url', 'text')}
        website['id'] = model_scalar(row.get('uri'))
        website['rank'] = website_rank(model_scalar(row.get('rank')))
        website['url'] = first_text(row.get('url')).strip()
        website['text'] = website_text(row)
        websites.append(website)
    item['on_the_web'] = websites
    areas = sorted_profile_text_values(raw.get('research_areas', []))
    item['research_areas'] = [{'label': area, 'rabid': None, 'vivo_id': '', 'id': ''} for area in areas]
    item['teacher_for'] = sorted_profile_text_values(raw.get('teacher_for', []))
    item['contributor_to'] = publication_entries(raw)
    item['appointments'] = dated_entries(
        raw, 'appointments', ('uri', 'id', 'org_name', 'name', 'department', 'start_date', 'end_date')
    )
    item['credentials'] = dated_entries(
        raw,
        'credentials',
        ('uri', 'id', 'name', 'number', 'start_date', 'end_date', 'grantor_name', 'specialty_name'),
    )
    item['training'] = dated_entries(
        raw,
        'training',
        ('name', 'start_date', 'end_date', 'city', 'state', 'country', 'org_name', 'hospital_name', 'specialty_name'),
    )
    item['collaborators'] = [
        {
            **{name: model_scalar(value) for name, value in row.items() if name in ('uri', 'name', 'title', 'org_name')},
            'id': model_scalar(row.get('uri')),
        }
        for row in sorted(entries(raw, 'collaborators'), key=lambda row: first_text(row.get('name')).lower())
    ]
    uri = first_text(raw.get('uri'))
    if not uri:
        raise PageDataError('The source profile has no URI.')
    graph_id = first_text(item['id']).rsplit('/', 1)[-1]
    graph_key = 'http://vivo.brown.edu/individual/' + graph_id
    item['has_coauthors'] = graph_key in coauthors
    item['has_collaborators'] = graph_key in collaborators if item['collaborators'] else False
    return item
