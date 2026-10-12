"""
Produces the five Rails report tables as CSV and Excel-readable SpreadsheetML.
"""

import re
from xml.sax.saxutils import escape

from vivo_app.lib.reports import ReportError, rails_integer

type Cell = str | int | None
type Matrix = list[list[Cell]]

HEADINGS = {
    'General Info': ['Name', 'Organization', 'Title', 'FIS updated', 'Profile updated', 'CV link', 'Research Area'],
    'Teacher For': ['Name', 'Organization', 'Course Code', 'Course Name'],
    'Contributor To': [
        'Name',
        'Organization',
        'Title',
        'Type',
        'Volume',
        'Issue',
        'Date',
        'Authors',
        'Venue',
        'DOI',
        'Year',
        'Published In',
    ],
    'Published In': ['Name', 'Organization', 'Journal Name'],
    'Text Fields': [
        'Name',
        'Organization',
        'Overview',
        'Teaching Overview',
        'Research Statement',
        'Research Overview',
        'Funded Research',
    ],
}
TEXT_FIELDS = ('overview', 'teaching_overview', 'research_statement', 'research_overview', 'funded_research')


def scalar(value: object) -> Cell:
    """
    Requires a printable field while preserving null versus empty string.

    Called by: report_tables(), publications(), sequence(), csv_bytes(), xml_bytes()
    """
    if value is not None and not isinstance(value, str) and type(value) is not int:
        raise ReportError('A report field has an unsupported value type.')
    return value


def sequence(item: dict[str, object], field: str) -> list[object]:
    """
    Requires an array for repeating faculty fields.

    Called by: report_tables(), publications()
    """
    value = item.get(field, [])
    if not isinstance(value, list):
        raise ReportError('A repeating report field is not a list.')
    return value


def sorted_labels(values: list[object]) -> list[str | None]:
    """
    Sorts courses and research labels case-insensitively as Rails does.

    Called by: report_tables()
    """
    labels: list[str | None] = []
    for value in values:
        if value is not None and not isinstance(value, str):
            raise ReportError('A report label is not a string.')
        labels.append(value)
    return sorted(labels, key=label_sort_key)


def label_sort_key(value: str | None) -> str:
    """
    Supplies the case-insensitive ordering used by Rails labels.

    Called by: sorted_labels()
    """
    return (value or '').lower()


def truncate(value: Cell) -> Cell:
    """
    Preserves Rails' inclusive index 500 before appending its truncation marker.

    Called by: publications(), report_tables()
    """
    if value is not None and not isinstance(value, str):
        raise ReportError('A report text field is not a string.')
    result = value[:501] + '(truncated)' if isinstance(value, str) and len(value) > 500 else value
    return result


def publication_year(pub: dict[str, Cell]) -> int | None:
    """
    Derives a plausible year from the leading decimal part of the publication date.

    Called by: publication_sort_key(), publications()
    """
    number = rails_integer(str(pub.get('date') or ''))
    return number if 1900 <= number <= 2200 else None


def publication_sort_key(pub: dict[str, Cell]) -> tuple[int, str]:
    """
    Orders publications by descending year then stripped lowercase title.

    Called by: publications()
    """
    return (-(publication_year(pub) or 0), str(pub.get('title') or '').strip(' \t\r\n\v\f\0').lower())


def publications(item: dict[str, object]) -> Matrix:
    """
    Expands publication fields using Rails array handling, type labels, and ordering.

    Called by: report_tables()
    """
    pubs: list[dict[str, Cell]] = []
    fields = ('title', 'type', 'volume', 'issue', 'date', 'authors', 'venue', 'doi', 'published_in')
    for raw in sequence(item, 'contributor_to'):
        if not isinstance(raw, dict):
            raise ReportError('A report publication is not an object.')
        pub: dict[str, Cell] = {}
        for field in fields:
            value = raw.get(field)
            if isinstance(value, list):
                value = value[0] if value else None
            pub[field] = scalar(value)
        pub['title'] = pub['title'] or ''
        pubs.append(pub)
    rows: Matrix = []
    for pub in sorted(pubs, key=publication_sort_key):
        kind = pub['type']
        prefix = 'http://vivo.brown.edu/ontology/citation#'
        if isinstance(kind, str) and kind.startswith(prefix):
            kind = kind.replace(prefix, '')
            kind = 'Other' if kind == 'Citation' else kind
            kind = re.sub(r'[A-Z]', r' \g<0>', kind)
        else:
            kind = None
        rows.append(
            [
                pub['title'],
                kind,
                pub['volume'],
                pub['issue'],
                pub['date'],
                truncate(pub['authors']),
                pub['venue'],
                pub['doi'],
                publication_year(pub),
                pub['published_in'],
            ]
        )
    return rows


def report_tables(faculty: list[dict[str, object]]) -> dict[str, Matrix]:
    """
    Builds the five ordered tables, including each faculty's blank fallback rows.

    Called by: report_cache.generate_report(), tests
    """
    tables: dict[str, Matrix] = {name: [list(headings)] for name, headings in HEADINGS.items()}
    for item in faculty:
        base = [scalar(item.get('name', '')), scalar(item.get('org_label', ''))]
        cvs = item.get('cv') or []
        cv = item.get('cv_link')
        if 'cv' in item:
            if not isinstance(cvs, list) or (cvs and not isinstance(cvs[0], dict)):
                raise ReportError('A report CV field has an unsupported value.')
            cv = cvs[0].get('cv_link') if cvs else None
        general = base + [
            scalar(item.get('title', '')),
            scalar(item.get('fis_updated')),
            scalar(item.get('profile_updated')),
            scalar(cv),
        ]
        for area in sorted_labels(sequence(item, 'research_areas')) or [None]:
            tables['General Info'].append(general + [area])
        courses = sorted_labels(sequence(item, 'teacher_for'))
        if not courses:
            tables['Teacher For'].append(base + [None, None])
        for course in courses:
            if not isinstance(course, str):
                raise ReportError('A report course has no text.')
            dash = course.find('-')
            code = course if dash <= 0 else course[:dash]
            title = course[dash + 1 :].strip(' \t\r\n\v\f\0') if dash >= 0 else None
            tables['Teacher For'].append(base + [code, title])
        for pub in publications(item) or [[None] * 10]:
            tables['Contributor To'].append(base + pub)
        for journal in sequence(item, 'published_in') or [None]:
            tables['Published In'].append(base + [scalar(journal)])
        texts: list[Cell] = []
        for field in TEXT_FIELDS:
            value = item.get(field, '')
            if not isinstance(value, str):
                raise ReportError('A report narrative field is not text.')
            texts.append(truncate(value.replace('"', '')))
        tables['Text Fields'].append(base + texts)
    return tables


def csv_cell(value: Cell) -> str:
    """
    Matches Ruby CSV quoting, including quoted empty strings and unquoted nulls.

    Called by: csv_bytes()
    """
    result = '' if value is None else str(value)
    if value is not None and (result == '' or any(character in result for character in ',"\r\n')):
        result = '"' + result.replace('"', '""') + '"'
    return result


def csv_bytes(tables: dict[str, Matrix]) -> bytes:
    """
    Serializes LF rows and the four CRLF table separators used by Rails.

    Called by: report_cache.generate_report(), tests
    """
    sections = [''.join(','.join(csv_cell(cell) for cell in row) + '\n' for row in rows) for rows in tables.values()]
    return '\r\n'.join(sections).encode('utf-8')


def xml_bytes(tables: dict[str, Matrix]) -> bytes:
    """
    Serializes the Rails SpreadsheetML layout with string cells and XML escaping.

    Called by: report_cache.generate_report(), tests
    """
    lines = ['<?xml version="1.0"?>', '<ss:Workbook xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">']
    for name, rows in tables.items():
        lines.extend([f'  <ss:Worksheet ss:Name="{name}">', '    <ss:Table>'])
        for row in rows:
            lines.append('      <ss:Row>')
            for cell in row:
                value = '' if cell is None else str(cell)
                if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]', value):
                    raise ReportError('A report cell contains text that XML cannot represent.')
                text = escape(value).replace('\r', '&#xD;')
                text = ''.join(f'&#x{ord(character):X};' if ord(character) > 127 else character for character in text)
                data = f'<ss:Data ss:Type="String">{text}</ss:Data>'
                lines.extend(['        <ss:Cell>', '          ' + data, '        </ss:Cell>'])
            lines.append('      </ss:Row>')
        lines.extend(['    </ss:Table>', '  </ss:Worksheet>'])
    lines.append('</ss:Workbook>')
    return ('\n'.join(lines) + '\n').encode('utf-8')
