"""
Checks visualization response routing with made-up graph data and no network.
"""

import json
from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase, override_settings

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RequestKey
from vivo_app.lib.source_graph import graph_csv, visualization_graph, visualization_key
from vivo_app.lib.source_requests import member_details_key, profile_key


@override_settings(PAGE_DATA_MODE='live', VIZ_SERVICE_URL='http://example.invalid')
class SourceGraphTests(TestCase):
    """Checks source graph paths, response shapes, and explicit failures."""

    def setUp(self) -> None:
        """
        Creates two made-up graph responses.
        """
        graph = {
            'nodes': [
                {'id': 'invented-a', 'name': 'Invented A', 'group': 'Example Group'},
                {'id': 'invented-b', 'name': 'Invented B'},
            ],
            'links': [{'source': 'invented-a', 'target': 'invented-b', 'weight': 3}],
        }
        self.replies = {
            visualization_key('collaborators', 'invented-a'): {'graph': graph, 'rabid': 'invented-a'},
            visualization_key('coauthors', 'invented-a'): {'data': graph, 'rabid': 'invented-a'},
            profile_key('invented-a'): {
                'responseHeader': {'status': 0},
                'response': {
                    'numFound': 1,
                    'docs': [
                        {
                            'id': 'http://vivo.brown.edu/individual/invented-a',
                            'record_type': 'PEOPLE',
                            'display_name_s': 'Invented A',
                            'json_txt': json.dumps({'name': 'Invented A', 'title': 'Example Professor'}),
                        }
                    ],
                },
            },
        }

    def read(self, key: RequestKey, mode: str) -> RecordedResponse:
        """
        Reads only a made-up graph named by the test.

        Called by: test_graph_json_uses_the_matching_source_family()
        """
        if key not in self.replies:
            raise PageDataError('No invented graph matches this request.')
        return RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(self.replies[key]).encode())

    def get_page(self, path: str) -> HttpResponse:
        """
        Requests one local graph response for a test.

        Called by: test_graph_json_uses_the_matching_source_family()
        """
        response = self.client.get(path)
        assert isinstance(response, HttpResponse)
        return response

    def test_graph_json_uses_the_matching_source_family(self) -> None:
        """
        Checks collaborator and coauthor JSON use their separate source requests.
        """
        with patch('vivo_app.lib.source_graph.read_source', side_effect=self.read):
            collab = self.get_page('/display/invented-a/viz/collab.json')
            coauthor = self.get_page('/display/invented-a/viz/coauthor.json')
            missing = self.get_page('/display/other/viz/collab.json')
        self.assertEqual(collab.status_code, 200)
        self.assertEqual(coauthor.status_code, 200)
        self.assertEqual(json.loads(collab.content), self.replies[visualization_key('collaborators', 'invented-a')])
        self.assertEqual(json.loads(coauthor.content), self.replies[visualization_key('coauthors', 'invented-a')])
        self.assertEqual(missing.status_code, 503)

    def test_invalid_graph_shape_is_rejected(self) -> None:
        """
        Checks a successful JSON response still needs graph nodes and links.
        """
        bad = RecordedResponse(200, (('content-type', 'application/json'),), b'{"graph": {"nodes": []}}')
        with self.assertRaises(PageDataError):
            visualization_graph('collaborators', 'invented-a', 'replay', lambda key, mode: bad)
        with self.assertRaises(PageDataError):
            visualization_key('collaborators', '../private')
        with self.assertRaises(PageDataError):
            visualization_graph('collaborators', 'team-example', 'replay', self.read)

    def test_network_page_and_downloads_use_graph_data(self) -> None:
        """
        Checks both network pages and CSV downloads use the matching graph family.
        """
        with patch('vivo_app.lib.source_graph.read_source', side_effect=self.read):
            page = self.get_page('/display/invented-a/viz/coauthor/')
            public_page = self.get_page('/display/invented-a/viz/coauthor')
            download = self.get_page('/display/invented-a/viz/coauthor/?format=csv')
            public_download = self.get_page('/display/invented-a/viz/coauthor.csv')
            collab = self.get_page('/display/invented-a/viz/collab/?format=csv')
            missing = self.get_page('/display/other/viz/coauthor/')
        self.assertEqual(page.status_code, 200)
        self.assertEqual(public_page.status_code, 200)
        self.assertContains(page, 'Invented A')
        self.assertContains(public_page, '/display/invented-a/viz/coauthor.csv')
        self.assertIn('id,name,info,collab_with,count', download.content.decode())
        self.assertEqual(public_download.content, download.content)
        self.assertEqual(public_download['Content-Type'], 'text/plain; charset=utf-8')
        self.assertIn('invented-a,Invented A,Example Group,invented-b,3', download.content.decode())
        self.assertNotIn(b'\r\n', public_download.content)
        self.assertIn('invented-a,Invented A,Example Group,invented-b,1', collab.content.decode())
        self.assertEqual(missing.status_code, 503)

    def test_empty_public_graph_remains_an_empty_success(self) -> None:
        """
        Checks an empty service response stays empty in JSON and CSV and shows a page warning.
        """
        self.replies[visualization_key('collaborators', 'invented-a')] = {}
        with patch('vivo_app.lib.source_graph.read_source', side_effect=self.read):
            json_response = self.get_page('/display/invented-a/viz/collab.json')
            csv_response = self.get_page('/display/invented-a/viz/collab/?format=csv')
            direct_csv = self.get_page('/display/invented-a/viz/collab.csv')
            page = self.get_page('/display/invented-a/viz/collab/')
        self.assertEqual(json_response.status_code, 200)
        self.assertEqual(json.loads(json_response.content), {})
        self.assertEqual(csv_response.status_code, 200)
        self.assertEqual(csv_response.content, b'')
        self.assertEqual(direct_csv.status_code, 200)
        self.assertEqual(direct_csv.content, b'')
        self.assertContains(page, 'No collaboration data is available')

    def test_coauthor_treemap_reuses_the_network_graph(self) -> None:
        """
        Checks the treemap page and its downloads use the existing coauthor source request.
        """
        with patch('vivo_app.lib.source_graph.read_source', side_effect=self.read):
            page = self.get_page('/display/invented-a/viz/coauthor_treemap')
            json_response = self.get_page('/display/invented-a/viz/coauthor_treemap?format=json')
            csv_response = self.get_page('/display/invented-a/viz/coauthor_treemap?format=csv')
        self.assertContains(page, 'The coauthor treemap is created')
        self.assertContains(page, 'treemap_graph.js')
        self.assertEqual(json.loads(json_response.content), self.replies[visualization_key('coauthors', 'invented-a')])
        self.assertIn('invented-a,Invented A,Example Group,invented-b,3', csv_response.content.decode())


class CustomGraphTests(TestCase):
    """Checks Rails-calculated collaboration graphs use member records in both source modes."""

    def setUp(self) -> None:
        """
        Creates made-up root and neighboring faculty records.
        """
        prefix = 'http://vivo.brown.edu/individual/'
        root = {
            'name': 'Invented Root',
            'title': 'Example Professor',
            'org_label': 'Example Unit',
            'collaborators': [{'uri': prefix + 'invented-neighbor', 'name': 'Invented Neighbor'}],
        }
        neighbor = {
            'name': 'Invented Neighbor',
            'collaborators': [{'uri': 'https://example.invalid/person', 'name': 'Outside Person'}],
        }
        self.responses = {
            member_details_key(['invented-root']): self.solr_response([('invented-root', root)]),
            member_details_key(['invented-neighbor']): self.solr_response([('invented-neighbor', neighbor)]),
        }
        self.requested: list[tuple[RequestKey, str]] = []

    def solr_response(self, people: list[tuple[str, dict[str, object]]]) -> RecordedResponse:
        """
        Wraps made-up people in the Solr response shape.

        Called by: setUp()
        """
        docs = [
            {
                'id': 'http://vivo.brown.edu/individual/' + identifier,
                'record_type': 'PEOPLE',
                'json_txt': json.dumps(person),
            }
            for identifier, person in people
        ]
        body = {'responseHeader': {'status': 0}, 'response': {'numFound': len(docs), 'docs': docs}}
        return RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(body).encode())

    def read(self, key: RequestKey, mode: str) -> RecordedResponse:
        """
        Reads only the made-up member responses and records the exact requests.

        Called by: test_live_and_replay_use_the_same_member_requests(), test_missing_recording_fails()
        """
        self.requested.append((key, mode))
        if key not in self.responses:
            raise PageDataError('The requested recording is missing.')
        return self.responses[key]

    def test_live_and_replay_use_the_same_member_requests(self) -> None:
        """
        Checks team roots, neighboring people, graph levels, and CSV use the same source requests.
        """
        with patch('vivo_app.lib.source_graph.team_definition', return_value=('Example Team', ['invented-root'])):
            live = visualization_graph('collaborators', 'team-example', 'live', self.read)
            live_keys = [key for key, _ in self.requested]
            self.requested.clear()
            replay = visualization_graph('collaborators', 'team-example', 'replay', self.read)
        self.assertEqual(live, replay)
        self.assertEqual(live_keys, [key for key, _ in self.requested])
        self.assertEqual(live_keys, list(self.responses))
        graph = live['graph']
        assert isinstance(graph, dict)
        nodes = graph['nodes']
        assert isinstance(nodes, list)
        self.assertEqual([node['level'] for node in nodes], [0, 1, 2])
        self.assertIn('Invented Root', graph_csv(live, 'collaborators'))

    def test_missing_recording_fails(self) -> None:
        """
        Checks that a missing second-level member batch does not contact another source.
        """
        self.responses.pop(member_details_key(['invented-neighbor']))
        with (
            patch('vivo_app.lib.source_graph.team_definition', return_value=('Example Team', ['invented-root'])),
            self.assertRaisesRegex(PageDataError, 'recording is missing'),
        ):
            visualization_graph('collaborators', 'team-example', 'replay', self.read)

    @override_settings(PAGE_DATA_MODE='replay', UPSTREAM_RECORDING_MANIFEST='unused-in-this-test')
    def test_team_page_uses_calculated_graph_in_replay(self) -> None:
        """
        Checks the team graph page and fit option render from the same recorded Solr inputs.
        """
        with (
            patch('vivo_app.lib.source_graph.team_definition', return_value=('Example Team', ['invented-root'])),
            patch('vivo_app.lib.source_graph.read_source', side_effect=self.read),
        ):
            page = self.client.get('/display/team-example/viz/collab/')
            fit = self.client.get('/display/team-example/viz/collab/?fit=1')
        assert isinstance(page, HttpResponse)
        assert isinstance(fit, HttpResponse)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Example Team')
        self.assertContains(page, 'Intradepartmental collaboration')
        self.assertContains(page, 'js/network_graph.js')
        self.assertContains(fit, 'id="forceToFit" type="checkbox" checked')
        self.assertEqual(len(self.requested), 4)
        self.assertTrue(all(mode == 'replay' for _, mode in self.requested))
