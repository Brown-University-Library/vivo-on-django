"""
Selects current report faculty from Solr in Rails report order.
"""

import json

from vivo_app.lib.page_errors import PageDataError
from vivo_app.lib.reports import Report, ReportError
from vivo_app.lib.source_pages import SourceReader, documents, response_object
from vivo_app.lib.source_requests import profile_export_key, quoted, read_source
from vivo_app.lib.source_types import RequestKey


def department_ids(department: str, reader: SourceReader) -> list[str]:
    """
    Reads every department page using the source's default query and ordering.

    Called by: report_faculty(), tests
    """
    identifiers: list[str] = []
    seen: set[str] = set()
    total: int | None = None
    start = 0
    while total is None or start < total:
        key = RequestKey(
            'solr',
            '/select',
            (
                ('fl', 'id'),
                ('wt', 'json'),
                ('fq', '(record_type:"PEOPLE")'),
                ('fq', f'(affiliations:{quoted(department)})'),
                ('rows', '100'),
                ('start', str(start)),
                ('q.op', 'AND'),
            ),
        )
        docs, count = documents(response_object(key, reader))
        if total is not None and total != count:
            raise ReportError('Department membership changed while reading report pages; retry the report.')
        total = count
        if not docs and start < total:
            raise ReportError('Solr report paging stopped before all faculty were read.')
        for doc in docs:
            uri = doc.get('id')
            if not isinstance(uri, str) or not uri.rstrip('/'):
                raise ReportError('A report department result has no faculty identifier.')
            if uri in seen:
                raise ReportError('Solr report paging repeated a faculty record; retry the report.')
            seen.add(uri)
            identifiers.append(uri.rstrip('/').rsplit('/', 1)[-1])
        start += len(docs)
        if start > total:
            raise ReportError('Solr report paging returned more records than its count.')
    return identifiers


def report_faculty(report: Report, reader: SourceReader = read_source) -> list[dict[str, object]]:
    """
    Combines selectors, skips absent faculty, and retains raw fields for export.

    Called by: report_cache.generate_report(), tests
    """
    faculty: list[dict[str, object]] = []
    try:
        identifiers = list(report.definition.get('faculty_ids', []))
        for department in report.definition.get('department_names', []):
            identifiers.extend(department_ids(department, reader))
        for identifier in dict.fromkeys(identifiers):
            docs, count = documents(response_object(profile_export_key(identifier), reader))
            if count == 0 and not docs:
                continue
            if count != 1 or len(docs) != 1:
                raise ReportError('A report faculty lookup returned an unexpected number of records.')
            doc = docs[0]
            raw = doc.get('json_txt')
            if isinstance(raw, list):
                raw = raw[0] if raw else None
            if not isinstance(raw, str):
                raise ReportError('A report faculty record has no JSON content.')
            try:
                item = json.loads(raw)
            except ValueError as exc:
                raise ReportError('A report faculty record contains invalid JSON.') from exc
            if not isinstance(item, dict):
                raise ReportError('A report faculty record is not a JSON object.')
            item = {'fis_updated': doc.get('fis_updated_s'), 'profile_updated': doc.get('profile_updated_s'), **item}
            faculty.append(item)
    except PageDataError as exc:
        raise ReportError('The report could not read the required Solr data.') from exc
    return faculty
