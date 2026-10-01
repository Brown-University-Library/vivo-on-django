"""
Checks organization charts with made-up Solr responses and no network access.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase, override_settings

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RequestKey
from vivo_app.lib.source_org_charts import publication_history_csv, publication_history_data, research_areas_data
from vivo_app.lib.source_requests import chart_member_key, profile_key


@override_settings(PAGE_DATA_MODE='live')
class OrganizationChartTests(TestCase):
    """Checks the chart data, routes, and matching live/replay requests."""

    def setUp(self) -> None:
        """
        Creates a small organization and three made-up researchers.
        """
        prefix = 'http://vivo.brown.edu/individual/'
        organization: dict[str, object] = {
            'id': prefix + 'org-example',
            'record_type': 'ORGANIZATION',
            'json_txt': json.dumps(
                {
                    'name': 'Example Organization',
                    'people': [
                        {'faculty_uri': prefix + person_id} for person_id in ('invented-a', 'invented-b', 'invented-c')
                    ],
                }
            ),
        }
        people = [
            (
                'invented-a',
                {
                    'name': 'Invented A',
                    'title': 'Professor',
                    'research_areas': ['Area A', 'Area B'],
                    'contributor_to': [{'date': '2020-01-01'}, {'date': '2020-04-01'}, {'date': '2021-01-01'}],
                },
            ),
            (
                'invented-b',
                {
                    'name': 'Invented B',
                    'title': 'Lecturer',
                    'research_areas': ['Area A'],
                    'contributor_to': [{'date': '1899-01-01'}, {'date': '2020-01-01'}, {'date': '2999-01-01'}],
                },
            ),
            (
                'invented-c',
                {
                    'name': 'Invented C',
                    'title': 'Researcher',
                    'research_areas': ['Area C'],
                    'contributor_to': [{'date': '2999-01-01'}],
                },
            ),
        ]
        member_docs: list[dict[str, object]] = [
            {'id': prefix + identifier, 'record_type': 'PEOPLE', 'json_txt': json.dumps(person)}
            for identifier, person in people
        ]
        self.responses = {
            profile_key('org-example'): self.response([organization]),
            chart_member_key(['invented-a', 'invented-b', 'invented-c']): self.response(member_docs),
        }
        self.requested: list[tuple[RequestKey, str]] = []

    def response(self, docs: list[dict[str, object]]) -> RecordedResponse:
        """
        Wraps made-up records in the expected Solr response.

        Called by: setUp()
        """
        body = {'responseHeader': {'status': 0}, 'response': {'numFound': len(docs), 'docs': docs}}
        return RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(body).encode())

    def read(self, key: RequestKey, mode: str) -> RecordedResponse:
        """
        Reads only the exact made-up request keys.

        Called by: test_chart_data_and_replay(), test_chart_routes(), test_missing_recording_fails()
        """
        self.requested.append((key, mode))
        if key not in self.responses:
            raise PageDataError('The requested recording is missing.')
        return self.responses[key]

    def test_chart_data_and_replay(self) -> None:
        """
        Checks public chart shapes and identical live and offline request keys.
        """
        name, publications = publication_history_data('org-example', 'live', self.read)
        live_keys = [key for key, _ in self.requested]
        self.requested.clear()
        _, replay = publication_history_data('org-example', 'replay', self.read)
        self.assertEqual(name, 'Example Organization')
        self.assertEqual(publications, replay)
        self.assertEqual(live_keys, [key for key, _ in self.requested])
        self.assertEqual(publications['years'], ['2020', '2021'])
        self.assertEqual(publications['columns'], ['invented-a', 'invented-b'])
        matrix = publications['matrix']
        assert isinstance(matrix, list)
        self.assertEqual([row['total'] for row in matrix if isinstance(row, dict)], [3, 1])
        self.assertEqual(
            publication_history_csv(publications),
            'year,year_total,invented-a,invented-b\n2020,3,2,1\n2021,1,1,0',
        )
        _, research = research_areas_data('org-example', 'replay', self.read)
        nodes = research['nodes']
        links = research['links']
        assert isinstance(nodes, list) and isinstance(nodes[1], list)
        assert isinstance(links, list)
        self.assertEqual([node['nodeName'] for node in nodes[1] if isinstance(node, dict)], ['Area A'])
        self.assertEqual(len(links), 2)

    def test_publication_csv_follows_its_header_column_order(self) -> None:
        """
        Checks CSV rows follow the named columns even when source keys are reordered.
        """
        chart = {
            'columns': ['invented-a', 'invented-b'],
            'matrix': [{'invented-b': 2, 'total': 3, 'year': 2020, 'invented-a': 1}],
        }
        self.assertEqual(
            publication_history_csv(chart),
            'year,year_total,invented-a,invented-b\n2020,3,1,2',
        )

    def test_chart_skips_listed_member_missing_from_solr(self) -> None:
        """Uses available members when a listed person has no Solr record."""
        key = chart_member_key(['invented-a', 'invented-b', 'invented-c'])
        response = json.loads(self.responses[key].body)
        response['response']['docs'] = response['response']['docs'][:2]
        response['response']['numFound'] = 2
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        _, chart = publication_history_data('org-example', 'live', self.read)
        self.assertEqual(chart['columns'], ['invented-a', 'invented-b'])

    def test_team_chart_uses_solr_member_order(self) -> None:
        """Keeps the order in which the source returns team faculty records."""
        source = json.loads(self.responses[chart_member_key(['invented-a', 'invented-b', 'invented-c'])].body)
        docs = source['response']['docs'][:2]
        self.responses[chart_member_key(['invented-a', 'invented-b'])] = self.response(list(reversed(docs)))
        with TemporaryDirectory() as directory:
            manifest = Path(directory) / 'teams.json'
            manifest.write_text(
                json.dumps(
                    {'teams': {'team-example': {'name': 'Invented Team', 'member_ids': ['invented-a', 'invented-b']}}}
                )
            )
            with override_settings(TEAM_SOURCE_MANIFEST=str(manifest)):
                _, chart = publication_history_data('team-example', 'live', self.read)
        self.assertEqual(chart['columns'], ['invented-b', 'invented-a'])

    def test_chart_reads_publication_year_after_leading_space(self) -> None:
        """Counts the year accepted by the public publication parser."""
        key = chart_member_key(['invented-a', 'invented-b', 'invented-c'])
        response = json.loads(self.responses[key].body)
        first = json.loads(response['response']['docs'][0]['json_txt'])
        first['contributor_to'].append({'date': ' 2022-01-01'})
        response['response']['docs'][0]['json_txt'] = json.dumps(first)
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        _, chart = publication_history_data('org-example', 'live', self.read)
        years = chart['years']
        if not isinstance(years, list):
            self.fail('Chart years should be a list.')
        self.assertIn('2022', years)

    def test_research_chart_keeps_other_members_when_one_area_list_is_invalid(self) -> None:
        """
        Checks malformed optional research areas do not hide the organization chart.
        """
        key = chart_member_key(['invented-a', 'invented-b', 'invented-c'])
        response = json.loads(self.responses[key].body)
        first = json.loads(response['response']['docs'][0]['json_txt'])
        first['research_areas'] = 'unreadable list'
        response['response']['docs'][0]['json_txt'] = json.dumps(first)
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        _, chart = research_areas_data('org-example', 'live', self.read)
        nodes = chart['nodes']
        if not isinstance(nodes, list):
            self.fail('Research chart nodes should be a list.')
        self.assertEqual(len(nodes[0]), 3)
        self.assertEqual(nodes[1], [])

    def test_publication_chart_keeps_other_members_when_one_list_is_invalid(self) -> None:
        """
        Checks invalid optional publications do not hide other member counts.
        """
        key = chart_member_key(['invented-a', 'invented-b', 'invented-c'])
        response = json.loads(self.responses[key].body)
        first = json.loads(response['response']['docs'][0]['json_txt'])
        first['contributor_to'].append('invalid row')
        response['response']['docs'][0]['json_txt'] = json.dumps(first)
        self.responses[key] = RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        _, chart = publication_history_data('org-example', 'live', self.read)
        self.assertEqual(chart['columns'], ['invented-b'])

    def test_chart_routes(self) -> None:
        """
        Checks the pages and public JSON and CSV paths use the same source records.
        """
        with patch('vivo_app.lib.source_org_charts.read_source', side_effect=self.read):
            page = self.client.get('/display/org-example/viz/publications')
            json_response = self.client.get('/display/org-example/viz/publications.json')
            csv_response = self.client.get('/display/org-example/viz/publications.csv')
            research_page = self.client.get('/display/org-example/viz/research')
            research_json = self.client.get('/display/org-example/viz/research.json')
        self.assertContains(page, 'Example Organization')
        self.assertContains(page, 'Last 10 years')
        assert isinstance(json_response, HttpResponse)
        assert isinstance(csv_response, HttpResponse)
        assert isinstance(research_json, HttpResponse)
        self.assertEqual(json.loads(json_response.content)['years'], ['2020', '2021'])
        self.assertEqual(csv_response['Content-Type'], 'text/csv')
        self.assertIn('attachment;', csv_response['Content-Disposition'])
        self.assertContains(research_page, 'research areas and how common')
        self.assertContains(research_page, '/display/org-example/viz/collab.json')
        self.assertEqual(len(json.loads(research_json.content)['links']), 2)

    def test_missing_recording_fails(self) -> None:
        """
        Checks that replay cannot substitute a different member batch.
        """
        self.responses.pop(chart_member_key(['invented-a', 'invented-b', 'invented-c']))
        with self.assertRaisesRegex(PageDataError, 'recording is missing'):
            publication_history_data('org-example', 'replay', self.read)
