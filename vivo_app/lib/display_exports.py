"""
Selects faculty for public display downloads and reuses the Rails export formatters.
"""

from functools import partial

from vivo_app.lib.page_errors import MissingRecordError, PageDataError
from vivo_app.lib.report_exports import csv_bytes, report_tables, xml_bytes
from vivo_app.lib.source_pages import (
    CUSTOM_ORGANIZATION_IDS,
    SourceReader,
    documents,
    first_text,
    organization_members,
    record_data,
    record_id,
    response_object,
)
from vivo_app.lib.source_requests import member_details_key, profile_export_key, read_source
from vivo_app.lib.source_teams import custom_organization_members, team_definition
from vivo_app.lib.source_types import RequestKey, SourceResponse


def export_request(identifier: str, query_format: str | None) -> tuple[str, str] | None:
    """
    Selects public exports, giving a URL suffix precedence over the query format.

    Called by: views.display_show()
    """
    base, separator, suffix = identifier.rpartition('.')
    selected = suffix if separator else query_format
    result = None
    if selected in {'csv', 'xml'}:
        result = (base if separator else identifier, selected)
    return result


def faculty_fields(doc: dict[str, object]) -> dict[str, object]:
    """
    Keeps raw faculty values and Rails' precedence for separately stored update dates.

    Called by: display_faculty(), member_faculty()
    """
    if first_text(doc.get('record_type')) != 'PEOPLE':
        raise PageDataError('The export source record is not a person.')
    return {'fis_updated': doc.get('fis_updated_s'), 'profile_updated': doc.get('profile_updated_s'), **record_data(doc)}


def member_export_key(identifiers: list[str]) -> RequestKey:
    """
    Requests full export fields in the twenty-record batches used by Rails SolrLite.

    Called by: member_faculty()
    """
    base = member_details_key(identifiers)
    fields = 'id,record_type,json_txt,fis_updated_s,profile_updated_s'
    values = {'fl': fields, 'rows': '20'}
    return RequestKey('solr', base.path, tuple((key, values.get(key, value)) for key, value in base.query))


def member_faculty(identifiers: list[str], reader: SourceReader) -> list[dict[str, object]]:
    """
    Reads every batch in source order, skipping absent members but rejecting incomplete responses.

    Called by: display_faculty()
    """
    faculty: list[dict[str, object]] = []
    for start in range(0, len(identifiers), 20):
        batch = identifiers[start : start + 20]
        docs, count = documents(response_object(member_export_key(batch), reader))
        if count != len(docs):
            raise PageDataError('The export member response is incomplete.')
        seen: set[str] = set()
        for doc in docs:
            identifier = record_id(doc)
            if identifier not in batch or identifier in seen:
                raise PageDataError('The export source returned an unrelated or repeated member.')
            seen.add(identifier)
            faculty.append(faculty_fields(doc))
    return faculty


def organization_ids(identifier: str, item: dict[str, object], reader: SourceReader) -> list[str]:
    """
    Applies existing custom membership and Rails appointment ordering before removing repeated IDs.

    Called by: display_faculty()
    """
    checked_reader = partial(complete_member_response, reader=reader)
    extra_ids = custom_organization_members(identifier, checked_reader)
    members = organization_members(item, extra_ids, checked_reader)
    custom = identifier in CUSTOM_ORGANIZATION_IDS
    members.sort(key=lambda member: first_text(member.get('label')) if custom else first_text(member.get('label')).upper())
    return list(dict.fromkeys(record_id({'id': first_text(member.get('faculty_uri'))}) for member in members))


def complete_member_response(key: RequestKey, reader: SourceReader) -> SourceResponse:
    """
    Rejects truncated custom-member responses before existing membership helpers process them.

    Called by: organization_ids() through the existing membership readers
    """
    response = reader(key)
    docs, count = documents(response_object(key, lambda _: response))
    if count != len(docs):
        raise PageDataError('The custom export member response is incomplete.')
    return response


def display_faculty(identifier: str, reader: SourceReader | None = None) -> list[dict[str, object]]:
    """
    Loads a person, organization, or configured team without report definitions or page-only services.

    Called by: display_files()
    """
    if reader is None:
        reader = read_source
    key = profile_export_key(identifier)
    if identifier.startswith('team-'):
        _, identifiers = team_definition(identifier)
        faculty = member_faculty(identifiers, reader)
    else:
        docs, count = documents(response_object(key, reader))
        if count == 0 and not docs:
            raise MissingRecordError('The requested export record is absent from Solr.')
        if count != 1 or len(docs) != 1 or record_id(docs[0]) != identifier:
            raise PageDataError('The export lookup returned an unexpected record.')
        doc = docs[0]
        if first_text(doc.get('record_type')) == 'ORGANIZATION':
            faculty = member_faculty(organization_ids(identifier, record_data(doc), reader), reader)
        else:
            faculty = [faculty_fields(doc)]
    return faculty


def display_files(identifier: str) -> tuple[bytes, bytes]:
    """
    Builds both completed files from the same faculty reads and five ordered tables.

    Called by: display_cache.generate_display()
    """
    tables = report_tables(display_faculty(identifier))
    return csv_bytes(tables), xml_bytes(tables)
