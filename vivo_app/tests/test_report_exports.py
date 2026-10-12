"""
Checks report selection and Rails-compatible table and file output.
"""

import json
import xml.etree.ElementTree as ET
from unittest.mock import Mock

from django.test import SimpleTestCase

from vivo_app.lib.report_exports import csv_bytes, report_tables, xml_bytes
from vivo_app.lib.report_sources import department_ids, report_faculty
from vivo_app.lib.reports import ReportError, parse_report
from vivo_app.lib.source_types import SourceResponse
from vivo_app.tests.test_report_entry import example_row


def solr_response(docs: list[dict[str, object]], total: int | None = None) -> SourceResponse:
    """
    Supplies a made-up successful Solr response.

    Called by: report selection tests
    """
    data = {'responseHeader': {'status': 0}, 'response': {'docs': docs, 'numFound': len(docs) if total is None else total}}
    return SourceResponse(200, (), json.dumps(data).encode())


class ReportSourceTests(SimpleTestCase):
    def test_combined_selectors_keep_first_order_and_skip_missing(self) -> None:
        """
        Checks combined selectors fetch unique faculty once and distinguish absent from failed records.
        """
        row = {
            **example_row(),
            'definition': json.dumps(
                {'faculty_ids': ['first', 'absent', 'first'], 'department_names': ['Example Department']}
            ),
        }
        reader = Mock(
            side_effect=[
                solr_response([{'id': 'http://example.invalid/first'}, {'id': 'http://example.invalid/second'}]),
                solr_response([{'json_txt': ['{"name":"First"}'], 'fis_updated_s': '2020'}]),
                solr_response([]),
                solr_response([{'json_txt': ['{"name":"Second"}']}]),
            ]
        )
        faculty = report_faculty(parse_report(row), reader)
        self.assertEqual([item['name'] for item in faculty], ['First', 'Second'])
        self.assertEqual(faculty[0]['fis_updated'], '2020')
        self.assertEqual(reader.call_count, 4)
        query = reader.call_args_list[0].args[0].query
        self.assertIn(('fq', '(affiliations:"Example Department")'), query)
        self.assertNotIn('sort', dict(query))
        self.assertNotIn('q', dict(query))
        for invalid in (
            solr_response([{}]),
            solr_response([{'json_txt': ['bad']}]),
            solr_response([{'json_txt': ['{}']}], total=2),
        ):
            with self.assertRaises(ReportError):
                report_faculty(parse_report(example_row()), Mock(return_value=invalid))

    def test_paging_and_incomplete_or_repeated_results(self) -> None:
        """
        Checks all department pages, escaping, empty departments, and failure on inconsistent paging.
        """
        first: list[dict[str, object]] = [{'id': f'http://example.invalid/faculty-{number}'} for number in range(100)]
        reader = Mock(side_effect=[solr_response(first, 101), solr_response([{'id': 'http://example.invalid/last'}], 101)])
        self.assertEqual(len(department_ids('Example "A"', reader)), 101)
        self.assertIn(('start', '100'), reader.call_args.args[0].query)
        self.assertIn(('fq', '(affiliations:"Example \\"A\\"")'), reader.call_args.args[0].query)
        self.assertEqual(department_ids('Empty', Mock(return_value=solr_response([]))), [])
        for second in (solr_response([], 101), solr_response(first[:1], 101), solr_response([], 0)):
            with self.assertRaises(ReportError):
                department_ids('Example', Mock(side_effect=[solr_response(first, 101), second]))


class ReportExportTests(SimpleTestCase):
    def test_empty_faculty_rows_and_exact_csv_null_handling(self) -> None:
        """
        Checks every section has headers and blank fallback cells retain Ruby CSV spelling.
        """
        tables = report_tables([{'name': 'Example', 'org_label': ''}])
        self.assertEqual([len(rows) for rows in tables.values()], [2] * 5)
        csv = csv_bytes(tables)
        self.assertIn(b'Example,"","",,,,\n\r\n', csv)
        self.assertIn(b'Example,"","","","","",""\n', csv)
        self.assertEqual(csv.count(b'\r\n'), 4)
        self.assertEqual(len(report_tables([])), 5)

    def test_every_field_sorting_and_rails_truncation(self) -> None:
        """
        Checks field values, repeated rows, publication ordering/types, and inclusive truncation.
        """
        item = {
            'name': 'Example, "Researcher"',
            'org_label': 'Example & Department',
            'title': 'Professor',
            'fis_updated': '2020',
            'profile_updated': '2021',
            'cv': [{'cv_link': 'https://example.invalid/cv'}],
            'research_areas': ['Zebra', 'apple'],
            'teacher_for': ['Z100', 'a100 - Example', '-Odd'],
            'published_in': ['Z Journal', 'A Journal'],
            'contributor_to': [
                {'title': ['Old'], 'date': '1999', 'type': 'http://vivo.brown.edu/ontology/citation#Citation'},
                {
                    'title': 'New',
                    'date': '2022-01-01',
                    'type': 'http://vivo.brown.edu/ontology/citation#BookSection',
                    'authors': 'a' * 502,
                    'volume': '2',
                    'issue': '3',
                    'venue': 'Venue',
                    'doi': 'Example DOI',
                    'published_in': 'Book',
                },
            ],
            'overview': '"' + 'x' * 502 + '"',
        }
        tables = report_tables([item])
        self.assertEqual([row[-1] for row in tables['General Info'][1:]], ['apple', 'Zebra'])
        self.assertEqual(tables['General Info'][1][2:6], ['Professor', '2020', '2021', 'https://example.invalid/cv'])
        self.assertEqual(
            [row[2:] for row in tables['Teacher For'][1:]], [['-Odd', 'Odd'], ['a100 ', 'Example'], ['Z100', None]]
        )
        pubs = tables['Contributor To']
        self.assertEqual(
            pubs[1][2:],
            [
                'New',
                ' Book Section',
                '2',
                '3',
                '2022-01-01',
                'a' * 501 + '(truncated)',
                'Venue',
                'Example DOI',
                2022,
                'Book',
            ],
        )
        self.assertEqual(pubs[2][3], ' Other')
        self.assertEqual(tables['Text Fields'][1][2], 'x' * 501 + '(truncated)')
        self.assertEqual([row[-1] for row in tables['Published In'][1:]], ['Z Journal', 'A Journal'])
        self.assertIn(b'"Example, ""Researcher"""', csv_bytes(tables))
        root = ET.fromstring(xml_bytes(tables))
        ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
        self.assertEqual([sheet.attrib['{' + ns['ss'] + '}Name'] for sheet in root], list(tables))
        for sheet, rows in zip(root, tables.values(), strict=True):
            xml_rows = sheet.findall('ss:Table/ss:Row', ns)
            self.assertEqual(len(xml_rows), len(rows))
            for xml_row, row in zip(xml_rows, rows, strict=True):
                cells = xml_row.findall('ss:Cell/ss:Data', ns)
                self.assertEqual([cell.text or '' for cell in cells], ['' if v is None else str(v) for v in row])
                self.assertTrue(all(cell.attrib['{' + ns['ss'] + '}Type'] == 'String' for cell in cells))

    def test_control_characters_and_bad_types_fail(self) -> None:
        """
        Checks unusable source fields cannot turn into successful partial report output.
        """
        bad_items: list[dict[str, object]] = [
            {'overview': None},
            {'teacher_for': None},
            {'contributor_to': ['bad']},
            {'research_areas': [{}]},
        ]
        for item in bad_items:
            with self.assertRaises(ReportError):
                report_tables([item])
        with self.assertRaises(ReportError):
            xml_bytes({'Example': [['bad\x00text']]})

    def test_xml_matches_ruby_empty_and_unicode_serialization(self) -> None:
        """
        Checks the empty tags and numeric escapes observed in original Ruby output.
        """
        result = xml_bytes({'Example': [[None, '', 'é “text”\r\n<&>']]})
        self.assertEqual(result.count(b'<ss:Data ss:Type="String"></ss:Data>'), 2)
        self.assertIn(b'&#xE9; &#x201C;text&#x201D;&#xD;\n&lt;&amp;&gt;</ss:Data>', result)
        self.assertTrue(result.startswith(b'<?xml version="1.0"?>\n'))
        self.assertTrue(result.endswith(b'</ss:Workbook>\n'))
