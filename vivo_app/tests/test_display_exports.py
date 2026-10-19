"""
Checks public display downloads, complete membership reads, and compatibility with existing formats.
"""

import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock, patch

from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings

from vivo_app.lib.display_exports import display_faculty, export_request
from vivo_app.lib.page_errors import MissingRecordError, PageDataError
from vivo_app.lib.report_exports import HEADINGS
from vivo_app.tests.test_report_exports import solr_response


def person_doc(identifier: str, **fields: object) -> dict[str, object]:
    """
    Supplies a complete made-up faculty source record with separate update dates.

    Called by: display export tests
    """
    return {
        'id': 'http://vivo.brown.edu/individual/' + identifier,
        'record_type': 'PEOPLE',
        'fis_updated_s': '2020-01-02',
        'profile_updated_s': '2021-03-04',
        'json_txt': [json.dumps({'name': identifier, 'org_label': 'Example Department', 'title': 'Professor', **fields})],
    }


def organization_doc(identifiers: list[str], identifier: str = 'org-example') -> dict[str, object]:
    """
    Supplies made-up organization appointments whose titles differ from faculty titles.

    Called by: display export tests
    """
    people = [
        {
            'faculty_uri': 'http://vivo.brown.edu/individual/' + member,
            'label': member,
            'specific_position': 'Example appointment',
            'general_position': 'http://vivoweb.org/ontology/core#FacultyAdministrativePosition',
        }
        for member in identifiers
    ]
    return {
        'id': 'http://vivo.brown.edu/individual/' + identifier,
        'record_type': 'ORGANIZATION',
        'json_txt': [json.dumps({'name': 'Example Organization', 'people': people})],
    }


class DisplaySourceTests(SimpleTestCase):
    def test_person_fields_and_date_precedence(self) -> None:
        """
        Checks raw text and dates retain Rails precedence without portrait or graph reads.
        """
        reader = Mock(return_value=solr_response([person_doc('invented-a', overview='<p>Example</p>')]))
        item = display_faculty('invented-a', reader)[0]
        self.assertEqual(item['fis_updated'], '2020-01-02')
        self.assertEqual(item['profile_updated'], '2021-03-04')
        self.assertEqual(item['overview'], '<p>Example</p>')
        self.assertEqual(reader.call_count, 1)
        self.assertIn('fis_updated_s', dict(reader.call_args.args[0].query)['fl'])
        reader.return_value = solr_response([person_doc('invented-a', fis_updated='override')])
        self.assertEqual(display_faculty('invented-a', reader)[0]['fis_updated'], 'override')

    def test_organization_batches_order_duplicates_and_absent_members(self) -> None:
        """
        Checks twenty-member batches keep source order, unique appointments, dates, and missing-member behavior.
        """
        identifiers = [f'invented-{n:02}' for n in range(23)]
        first = list(reversed(identifiers[:20]))
        reader = Mock(
            side_effect=[
                solr_response([organization_doc(list(reversed(identifiers)) + identifiers[:2])]),
                solr_response([person_doc(identifier) for identifier in first]),
                solr_response([person_doc(identifiers[22]), person_doc(identifiers[20])]),
            ]
        )
        faculty = display_faculty('org-example', reader)
        self.assertEqual([item['name'] for item in faculty], first + [identifiers[22], identifiers[20]])
        self.assertEqual(reader.call_count, 3)
        for call in reader.call_args_list[1:]:
            query = dict(call.args[0].query)
            self.assertEqual(query['rows'], '20')
            self.assertIn('profile_updated_s', query['fl'])
            self.assertNotIn('sort', query)
        self.assertEqual(faculty[0]['title'], 'Professor')
        self.assertEqual(faculty[0]['profile_updated'], '2021-03-04')

    def test_empty_organization_avoids_member_lookup(self) -> None:
        """
        Checks empty organization exports need only the organization lookup.
        """
        reader = Mock(return_value=solr_response([organization_doc([])]))
        self.assertEqual(display_faculty('org-example', reader), [])
        self.assertEqual(reader.call_count, 1)

    def test_configured_team_and_custom_additions(self) -> None:
        """
        Checks existing team definitions and custom additions feed complete export faculty reads.
        """
        custom_id = 'org-brown-univ-dept124'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'members.json'
            path.write_text(
                json.dumps(
                    {
                        'teams': {'team-example': {'name': 'Example Team', 'member_ids': ['invented-b', 'invented-a']}},
                        'organizations': {custom_id: {'extra_member_ids': ['invented-b', 'invented-a']}},
                    }
                )
            )
            with override_settings(TEAM_SOURCE_MANIFEST=str(path)):
                reader = Mock(return_value=solr_response([person_doc('invented-a'), person_doc('invented-b')]))
                self.assertEqual(
                    [row['name'] for row in display_faculty('team-example', reader)], ['invented-a', 'invented-b']
                )
                self.assertEqual(reader.call_count, 1)
                reader = Mock(
                    side_effect=[
                        solr_response([organization_doc(['invented-a'], custom_id)]),
                        solr_response([person_doc('invented-b'), person_doc('invented-a')]),
                        solr_response([person_doc('invented-b'), person_doc('invented-a')]),
                    ]
                )
                self.assertEqual([row['name'] for row in display_faculty(custom_id, reader)], ['invented-b', 'invented-a'])
                self.assertEqual(reader.call_count, 3)
                query = dict(reader.call_args.args[0].query)['q']
                self.assertEqual(query.count('/invented-a'), 1)

    def test_missing_wrong_malformed_and_incomplete_records(self) -> None:
        """
        Checks absence differs from source failures and incomplete exports never become successful files.
        """
        with self.assertRaises(MissingRecordError):
            display_faculty('invented-a', Mock(return_value=solr_response([])))
        cases = [
            solr_response([person_doc('invented-b')]),
            solr_response([person_doc('invented-a')], total=2),
            solr_response([{**person_doc('invented-a'), 'json_txt': ['bad']}]),
            solr_response([{**person_doc('invented-a'), 'record_type': 'OTHER'}]),
        ]
        for response in cases:
            with self.subTest(response=response), self.assertRaises(PageDataError):
                display_faculty('invented-a', Mock(return_value=response))
        for response in [
            solr_response([], total=1),
            solr_response([person_doc('unrelated')]),
            solr_response([person_doc('invented-a'), person_doc('invented-a')]),
            solr_response([{**person_doc('invented-a'), 'record_type': 'ORGANIZATION'}]),
        ]:
            with self.subTest(response=response), self.assertRaises(PageDataError):
                display_faculty(
                    'org-example', Mock(side_effect=[solr_response([organization_doc(['invented-a'])]), response])
                )


@override_settings(
    TURNSTILE_ENABLED=False,
    REPORT_CACHE_TIMEOUT_SECONDS=0,
    REPORT_DEFINITIONS_PATH='',
    REPORTS_ALLOW_LOCAL_DEVELOPMENT=False,
)
class DisplayDownloadTests(SimpleTestCase):
    def setUp(self) -> None:
        """
        Checks public downloads with made-up source responses and no staff attributes.
        """
        self.person = person_doc(
            'invented-a',
            name='Example, "Zoë"',
            research_areas=['Zebra', 'apple'],
            teacher_for=['EX01 - Example Course'],
            overview='"' + 'x' * 502 + '"',
            cv=[{'cv_link': 'https://example.invalid/cv'}],
        )
        self.reader = patch('vivo_app.lib.display_exports.read_source', return_value=solr_response([self.person]))
        self.source = self.reader.start()
        self.addCleanup(self.reader.stop)

    def response(self, path: str, method: str = 'GET', script_name: str = '') -> HttpResponse:
        """
        Requires a regular response from the public display endpoint.

        Called by: DisplayDownloadTests
        """
        response = self.client.generic(method, path, SCRIPT_NAME=script_name, HTTP_ACCEPT='text/html')
        assert isinstance(response, HttpResponse)
        return response

    def test_suffix_query_slash_precedence_and_headers(self) -> None:
        """
        Checks confirmed Rails format forms, mounted requests, filenames, and attachment metadata.
        """
        cases = [
            ('invented-a.csv', 'csv'),
            ('invented-a.xml', 'xml'),
            ('invented-a?format=csv', 'csv'),
            ('invented-a/?format=xml', 'xml'),
            ('invented-a.csv/', 'csv'),
            ('invented-a.xml/', 'xml'),
            ('invented-a.csv?format=xml', 'csv'),
            ('invented-a.xml?format=csv', 'xml'),
            ('invented-a.csv?format=json', 'csv'),
            ('invented-a?format=csv&format=xml', 'xml'),
            ('invented-a?format=xml&format=csv', 'csv'),
            ('invented-a?format=csv&utm_source=example', 'csv'),
            ('invented-a.xml?format=json&utm_source=example', 'xml'),
        ]
        for path, fmt in cases:
            with self.subTest(path=path):
                response = self.response('/display/' + path, script_name='/mounted-app')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response['Content-Type'], 'application/xml')
                self.assertEqual(
                    response['Content-Disposition'],
                    f'attachment; filename="invented-a.{fmt}"; filename*=UTF-8\'\'invented-a.{fmt}',
                )
                self.assertNotIn('.csv', dict(self.source.call_args.args[0].query)['q'])
                self.assertNotIn('.xml', dict(self.source.call_args.args[0].query)['q'])

    def test_csv_and_workbook_content(self) -> None:
        """
        Checks real serialization includes source dates, all sheets, escaped text, and truncation.
        """
        csv = self.response('/display/invented-a.csv').content
        self.assertIn(b'"Example, ""Zo\xc3\xab"""', csv)
        self.assertIn(b'Professor,2020-01-02,2021-03-04,https://example.invalid/cv,apple', csv)
        self.assertIn(b'x' * 501 + b'(truncated)', csv)
        self.assertEqual(csv.count(b'\r\n'), 4)
        workbook = ET.fromstring(self.response('/display/invented-a.xml').content)
        ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
        self.assertEqual([sheet.attrib['{' + ns['ss'] + '}Name'] for sheet in workbook], list(HEADINGS))
        cells = workbook.findall('ss:Worksheet/ss:Table/ss:Row/ss:Cell/ss:Data', ns)
        self.assertIn('Example, "Zoë"', [cell.text for cell in cells])
        self.assertTrue(all(cell.attrib['{' + ns['ss'] + '}Type'] == 'String' for cell in cells))

    def test_empty_organization_downloads_and_head(self) -> None:
        """
        Checks empty organizations retain five headings and HEAD retains attachment headers without a body.
        """
        self.source.return_value = solr_response([organization_doc([])])
        csv = self.response('/display/org-example.csv')
        self.assertEqual(len(csv.content.decode().splitlines()), 9)
        xml = self.response('/display/org-example.xml')
        workbook = ET.fromstring(xml.content)
        self.assertEqual(len(workbook), 5)
        head = self.response('/display/org-example.xml', 'HEAD')
        self.assertEqual(head.content, b'')
        self.assertEqual(head['Content-Length'], str(len(xml.content)))
        self.assertEqual(head['Content-Disposition'], xml['Content-Disposition'])

    def test_error_pages_and_protected_reports_remain_protected(self) -> None:
        """
        Checks missing records, source failures, bad export text, and unsupported requests do not download partial files.
        """
        self.source.return_value = solr_response([])
        self.assertContains(self.response('/display/missing-example.xml'), 'Page not found', status_code=404)
        self.source.side_effect = PageDataError('Example private detail')
        failed = self.response('/display/invented-a.csv')
        self.assertContains(failed, 'Oops! Something went wrong', status_code=500)
        self.assertNotContains(failed, 'Example private detail', status_code=500)
        self.assertNotIn('Content-Disposition', failed)
        self.source.side_effect = None
        self.source.return_value = solr_response([person_doc('invented-a', overview='invalid\x00text')])
        self.assertEqual(self.response('/display/invented-a.csv').status_code, 500)
        self.assertEqual(self.response('/display/invented-a?format=').status_code, 400)
        self.assertEqual(self.response('/display/invented-a.unsupported').status_code, 500)
        self.assertEqual(self.response('/display/invented-a.csv', 'POST').status_code, 405)
        self.assertEqual(self.response('/reports/subject-lib/1.csv').status_code, 403)

    def test_existing_json_dispatch_is_unchanged(self) -> None:
        """
        Checks JSON and raw JSON requests still reach their existing handlers and validation.
        """
        for suffix, loader in [('json', 'profile_json_data'), ('json_txt', 'raw_record_json_data')]:
            with patch('vivo_app.views.' + loader, return_value={}) as source:
                self.assertEqual(self.response('/display/invented-a.' + suffix).status_code, 200)
                source.assert_called_once_with('invented-a')
            self.assertIsNone(export_request('invented-a.' + suffix, 'csv'))
        self.source.assert_not_called()
