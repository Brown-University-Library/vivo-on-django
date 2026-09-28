"""
Builds public structured responses from live or recorded source records.
"""

from collections.abc import Callable
from datetime import date

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RequestKey
from vivo_app.lib.source_graph import visualization_list
from vivo_app.lib.source_pages import documents, entries, first_text, record_data, record_id, response_object
from vivo_app.lib.source_requests import image_path, profile_export_key, read_source, source_origin

FormatReader = Callable[[RequestKey, str], RecordedResponse]


def dated_entries(raw: dict[str, object], field: str, names: tuple[str, ...]) -> list[dict[str, object]]:
    """
    Converts and sorts profile entries with optional start and end dates.

    Called by: profile_json_data()
    """
    converted: list[dict[str, object]] = []
    for row in entries(raw, field):
        item = (
            {name: row[name] for name in names if name in row}
            if field == 'training'
            else {name: row.get(name, None if name in {'start_date', 'end_date'} else '') for name in names}
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
            item['id'] = first_text(row.get('uri'))
        if field == 'appointments':
            item['org_name'] = first_text(row.get('hospital_name')) or first_text(row.get('org_name'))
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
        'book',
        'location_label',
        'publisher_label',
        'editors',
    )
    converted: list[dict[str, object]] = []
    for row in entries(raw, 'contributor_to'):
        item = {name: row[name] for name in names if name in row}
        date_text = first_text(row.get('date'))
        year = int(date_text[:4]) if len(date_text) >= 4 and date_text[:4].isdigit() else 0
        item['year'] = year if 1900 <= year <= 2200 else None
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
    doc = docs[0]
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
        'id': first_text(raw.get('uri')),
        'uri': first_text(raw.get('uri')),
    }
    item['display_name'] = first_text(doc.get('display_name_s')) or first_text(raw.get('name'))
    path = image_path(doc.get('thumbnail_file_path_s'))
    item['thumbnail'] = source_origin('images') + path if path else None
    item['fis_updated'] = first_text(doc.get('fis_updated_s')) or None
    item['profile_updated'] = first_text(doc.get('profile_updated_s')) or None
    item['show_visualizations'] = first_text(doc.get('show_visualizations_s')) == 'true'
    cv = entries(raw, 'cv')
    item['cv_link'] = first_text(cv[0].get('cv_link')) if cv else None
    affiliations = entries(raw, 'affiliations')
    item['affiliations'] = [
        {
            'uri': first_text(row.get('uri')),
            'name': first_text(row.get('name')),
            'id': first_text(row.get('uri')),
            'thumbnail': None,
        }
        for row in sorted(affiliations, key=lambda row: first_text(row.get('name')).lower())
    ]
    education = entries(raw, 'education')
    item['education'] = [
        {key: row[key] for key in ('school_uri', 'date', 'degree', 'school_name') if key in row}
        for row in sorted(education, key=lambda row: first_text(row.get('date')), reverse=True)
    ]
    web_pages = entries(raw, 'on_the_web')
    item['on_the_web'] = [
        {**row, 'rank': int(first_text(row.get('rank')) or '0'), 'id': first_text(row.get('uri'))}
        for row in sorted(web_pages, key=lambda row: int(first_text(row.get('rank')) or '0'))
    ]
    areas = raw.get('research_areas', [])
    if not isinstance(areas, list) or any(not isinstance(area, str) for area in areas):
        raise PageDataError('The source profile has invalid research areas.')
    item['research_areas'] = [
        {'label': area, 'rabid': None, 'vivo_id': '', 'id': ''} for area in sorted(areas, key=str.lower)
    ]
    courses = raw.get('teacher_for', [])
    if not isinstance(courses, list) or any(not isinstance(course, str) for course in courses):
        raise PageDataError('The source profile has invalid teaching data.')
    item['teacher_for'] = sorted(courses, key=str.lower)
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
            **{name: row[name] for name in ('uri', 'name', 'title', 'org_name') if name in row},
            'id': first_text(row.get('uri')),
        }
        for row in sorted(entries(raw, 'collaborators'), key=lambda row: first_text(row.get('name')).lower())
    ]
    uri = first_text(raw.get('uri'))
    if not uri:
        raise PageDataError('The source profile has no URI.')
    item['has_coauthors'] = uri in visualization_list('coauthors', mode, reader)
    item['has_collaborators'] = uri in visualization_list('collaborators', mode, reader) if item['collaborators'] else False
    return item
