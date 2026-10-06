"""
Checks visualization response routing with made-up graph data and no network.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase, override_settings

from tools.source_capture import capture_custom_graph
from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RequestKey
from vivo_app.lib.source_graph import (
    custom_graph_members,
    custom_graph_records,
    graph_csv,
    graph_page_data,
    visualization_graph,
    visualization_key,
)
from vivo_app.lib.source_requests import graph_root_key, member_details_key, profile_key


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

    def test_empty_graph_preserves_json_and_renders_recovery_links(self) -> None:
        """
        Checks a valid empty graph preserves JSON, the CSV error and its recovery page.
        """
        empty = {'graph': {}, 'rabid': 'invented-a', 'updated': '2026-01-02'}
        self.replies[visualization_key('collaborators', 'invented-a')] = empty
        with patch('vivo_app.lib.source_graph.read_source', side_effect=self.read):
            data = self.get_page('/display/invented-a/viz/collab.json')
            csv = self.get_page('/display/invented-a/viz/collab.csv')
            query_csv = self.get_page('/display/invented-a/viz/collab?format=csv')
            page = self.get_page('/display/invented-a/viz/collab')
        self.assertEqual(json.loads(data.content), empty)
        self.assertEqual(csv.status_code, 500)
        self.assertEqual(csv.content, b'error')
        self.assertEqual(csv['Content-Type'], 'text/plain; charset=utf-8')
        self.assertEqual(query_csv.status_code, csv.status_code)
        self.assertEqual(query_csv.content, csv.content)
        self.assertContains(page, 'No collaboration data is available for this researcher.')
        self.assertContains(page, 'If this is your profile you can define collaborators via the')
        self.assertContains(page, '/display/invented-a#Affiliations')
        self.assertContains(page, 'network-empty-collaboration')
        graph = graph_page_data(empty, 'collaborators', 'invented-a')
        self.assertEqual(graph['source'], {'nodes': [], 'links': []})
        self.assertTrue(graph['empty_collaboration'])

    def test_populated_graph_keeps_its_existing_rendering(self) -> None:
        """
        Checks populated graphs retain their nodes and use the populated-page controls.
        """
        value = self.replies[visualization_key('collaborators', 'invented-a')]
        graph = graph_page_data(value, 'collaborators', 'invented-a')
        self.assertEqual(graph['source'], value['graph'])
        self.assertFalse(graph['empty_collaboration'])
        with patch('vivo_app.lib.source_graph.read_source', side_effect=self.read):
            page = self.get_page('/display/invented-a/viz/collab')
        self.assertNotContains(page, 'network-empty-collaboration')
        self.assertContains(page, 'Show Collaborators')

    def test_graph_download_and_page_merge_repeated_nodes(self) -> None:
        """
        Checks repeated graph nodes use one display point and the available group.
        """
        value: dict[str, object] = {
            'graph': {
                'nodes': [
                    {'id': 'invented-a', 'name': 'Invented A', 'group': None},
                    {'id': 'invented-a', 'name': 'Invented A', 'group': 'Example Unit'},
                    {'id': 'invented-b', 'name': 'Invented B'},
                ],
                'links': [{'source': 'invented-a', 'target': 'invented-b', 'weight': 1}],
            }
        }
        csv_text = graph_csv(value, 'collaborators')
        self.assertIn('invented-a,Invented A,Example Unit,invented-b,1', csv_text)
        page = graph_page_data(value, 'collaborators', 'invented-a')
        nodes = page['nodes']
        if not isinstance(nodes, list):
            self.fail('Graph page nodes should be a list.')
        self.assertEqual(len(nodes), 2)

    def test_graph_download_and_page_merge_repeated_links(self) -> None:
        """
        Checks repeated directed links form one displayed edge and CSV row.
        """
        value: dict[str, object] = {
            'data': {
                'nodes': [{'id': 'invented-a', 'name': 'Invented A'}, {'id': 'invented-b', 'name': 'Invented B'}],
                'links': [
                    {'source': 'invented-a', 'target': 'invented-b', 'weight': 3},
                    {'source': 'invented-a', 'target': 'invented-b', 'weight': 1},
                ],
            }
        }
        rows = graph_csv(value, 'coauthors').splitlines()
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[1].endswith(',4'))
        page = graph_page_data(value, 'coauthors', 'invented-a')
        links = page['links']
        if not isinstance(links, list):
            self.fail('Graph page links should be a list.')
        self.assertEqual(len(links), 1)

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
        self.root: dict[str, object] = {
            'uri': prefix + 'invented-root',
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
            graph_root_key(['invented-root']): self.solr_response([('invented-root', self.root)]),
            visualization_key('coauthors'): self.json_response({prefix + 'invented-root': True}),
            visualization_key('collaborators'): self.json_response({prefix + 'invented-root': True}),
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

    def json_response(self, value: dict[str, object]) -> RecordedResponse:
        """Wraps a made-up visualization availability list."""
        return RecordedResponse(200, (('content-type', 'application/json'),), json.dumps(value).encode())

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
        self.assertIsNone(nodes[2]['group'])
        self.assertEqual(nodes[0]['faculty']['item']['name'], 'Invented Root')
        self.assertTrue(nodes[0]['faculty']['item']['has_coauthors'])
        self.assertTrue(nodes[0]['faculty']['item']['has_collaborators'])
        self.assertNotIn('faculty', nodes[1])
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

    def test_unusable_collaborator_does_not_hide_team_graph(self) -> None:
        """
        Checks one missing collaborator address does not hide the other graph links.
        """
        self.root['collaborators'] = [
            {'name': 'Unknown Person'},
            {'uri': 'http://vivo.brown.edu/individual/invented-neighbor', 'name': 'Invented Neighbor'},
        ]
        self.responses[graph_root_key(['invented-root'])] = self.solr_response([('invented-root', self.root)])
        with patch('vivo_app.lib.source_graph.team_definition', return_value=('Example Team', ['invented-root'])):
            value = visualization_graph('collaborators', 'team-example', 'live', self.read)
        graph = value['graph']
        if not isinstance(graph, dict):
            self.fail('The collaboration graph should be a mapping.')
        links = graph['links']
        if not isinstance(links, list):
            self.fail('The collaboration links should be a list.')
        self.assertEqual(len(links), 2)

    def test_team_graph_uses_members_still_present_in_solr(self) -> None:
        """
        Checks a missing team profile does not hide the remaining graph.
        """
        self.responses[graph_root_key(['invented-root', 'invented-missing'])] = self.responses.pop(
            graph_root_key(['invented-root'])
        )
        with patch(
            'vivo_app.lib.source_graph.team_definition',
            return_value=('Example Team', ['invented-root', 'invented-missing']),
        ):
            result = visualization_graph('collaborators', 'team-example', 'replay', self.read)
        graph = result['graph']
        assert isinstance(graph, dict)
        nodes = graph['nodes']
        assert isinstance(nodes, list)
        self.assertEqual(nodes[0]['name'], 'Invented Root')

    def test_missing_availability_list_fails_replay(self) -> None:
        """Requires the production availability list used by nested faculty fields."""
        self.responses.pop(visualization_key('coauthors'))
        with (
            patch('vivo_app.lib.source_graph.team_definition', return_value=('Example Team', ['invented-root'])),
            self.assertRaisesRegex(PageDataError, 'recording is missing'),
        ):
            visualization_graph('collaborators', 'team-example', 'replay', self.read)

    def test_member_batches_limit_response_size(self) -> None:
        """
        Checks twenty-one member records use two bounded Solr requests.
        """
        identifiers = [f'invented-{index:02d}' for index in range(21)]
        first, last = identifiers[:20], identifiers[20:]
        self.responses = {
            member_details_key(first): self.solr_response([(identifier, {'name': identifier}) for identifier in first]),
            member_details_key(last): self.solr_response([(identifier, {'name': identifier}) for identifier in last]),
        }
        records = custom_graph_records(identifiers, 'replay', self.read, True)
        self.assertEqual(set(records), set(identifiers))
        self.assertEqual([key for key, _ in self.requested], list(self.responses))

    def test_specialized_organization_uses_its_added_members(self) -> None:
        """
        Checks a specialized organization combines its profile with configured members.
        """
        identifier = 'org-brown-univ-dept124'
        profile = {
            'responseHeader': {'status': 0},
            'response': {
                'numFound': 1,
                'docs': [
                    {
                        'id': 'http://vivo.brown.edu/individual/' + identifier,
                        'record_type': 'ORGANIZATION',
                        'json_txt': json.dumps({'name': 'Invented Institute', 'people': []}),
                    }
                ],
            },
        }
        self.responses[profile_key(identifier)] = RecordedResponse(200, (), json.dumps(profile).encode())
        self.responses[graph_root_key(['invented-root', 'invented-missing'])] = self.solr_response(
            [('invented-root', self.root)]
        )
        with patch(
            'vivo_app.lib.source_graph.custom_organization_members', return_value=['invented-root', 'invented-missing']
        ) as members:
            live = visualization_graph('collaborators', identifier, 'live', self.read)
            live_keys = [key for key, _ in self.requested]
            self.requested.clear()
            replay = visualization_graph('collaborators', identifier, 'replay', self.read)
        self.assertEqual(live['graph'], replay['graph'])
        self.assertEqual(live_keys, [key for key, _ in self.requested])
        self.assertEqual(
            live_keys,
            [
                profile_key(identifier),
                graph_root_key(['invented-root', 'invented-missing']),
                visualization_key('coauthors'),
                visualization_key('collaborators'),
                member_details_key(['invented-neighbor']),
            ],
        )
        members.assert_called_with(identifier, 'replay', self.read)
        graph = replay['graph']
        assert isinstance(graph, dict)
        nodes = graph['nodes']
        assert isinstance(nodes, list)
        self.assertEqual(nodes[0]['group'], 'Invented Institute')
        self.assertNotIn('http://vivo.brown.edu/individual/invented-missing', {node['id'] for node in nodes})

    def test_specialized_graph_rejects_an_unrelated_organization(self) -> None:
        """
        Checks an unrelated organization cannot supply a specialized graph's members.
        """
        identifier = 'org-brown-univ-dept124'
        other = {
            'responseHeader': {'status': 0},
            'response': {
                'numFound': 1,
                'docs': [
                    {
                        'id': 'http://vivo.brown.edu/individual/org-other',
                        'record_type': 'ORGANIZATION',
                        'json_txt': json.dumps({'name': 'Other Organization', 'people': []}),
                    }
                ],
            },
        }
        self.responses[profile_key(identifier)] = RecordedResponse(200, (), json.dumps(other).encode())
        with self.assertRaisesRegex(PageDataError, 'organization is unavailable'):
            custom_graph_members(identifier, 'live', self.read)

    def test_specialized_graph_keeps_members_with_valid_addresses(self) -> None:
        """
        Checks one unusable member address does not hide a specialized graph.
        """
        identifier = 'org-brown-univ-dept124'
        profile = {
            'responseHeader': {'status': 0},
            'response': {
                'numFound': 1,
                'docs': [
                    {
                        'id': 'http://vivo.brown.edu/individual/' + identifier,
                        'record_type': 'ORGANIZATION',
                        'json_txt': json.dumps(
                            {
                                'name': 'Invented Institute',
                                'people': [
                                    {'faculty_uri': 'invalid address'},
                                    {'faculty_uri': 'http://vivo.brown.edu/individual/invented-root'},
                                ],
                            }
                        ),
                    }
                ],
            },
        }
        self.responses[profile_key(identifier)] = RecordedResponse(200, (), json.dumps(profile).encode())
        with patch('vivo_app.lib.source_graph.custom_organization_members', return_value=[]):
            name, members = custom_graph_members(identifier, 'live', self.read)
        self.assertEqual(name, 'Invented Institute')
        self.assertEqual(members, ['invented-root'])

    def test_custom_graph_capture_replays_exact_member_requests(self) -> None:
        """
        Checks the bounded capture keeps all Solr responses needed by replay.
        """
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'custom-graph'
            with (
                patch('vivo_app.lib.source_graph.team_definition', return_value=('Example Team', ['invented-root'])),
                patch('tools.source_capture.read_source', side_effect=self.read),
                patch('tools.source_capture.time.sleep'),
                patch('vivo_app.lib.source_graph.time.sleep'),
            ):
                self.assertEqual(capture_custom_graph('team-example', output), 4)
            with (
                override_settings(
                    UPSTREAM_RECORDING_MANIFEST=str(output / 'manifest.json'), UPSTREAM_RECORDING_CASE='custom-graph'
                ),
                patch('vivo_app.lib.source_graph.team_definition', return_value=('Example Team', ['invented-root'])),
            ):
                graph = visualization_graph('collaborators', 'team-example', 'replay')
            self.assertEqual(graph['rabid'], 'team-example')
        with self.assertRaisesRegex(PageDataError, 'calculated Solr graph'):
            capture_custom_graph('invented-other', Path(directory) / 'unused')

    def test_team_csv_keeps_collaboration_counts(self) -> None:
        """
        Checks calculated team downloads retain repeated collaboration counts.
        """
        graph = {
            'graph': {
                'nodes': [
                    {'id': 'invented-a', 'name': 'Invented A', 'group': 'Example Team'},
                    {'id': 'invented-b', 'name': 'Invented B', 'group': None},
                ],
                'links': [{'source': 'invented-a', 'target': 'invented-b', 'weight': 3}],
            },
            'rabid': 'team-example',
        }
        self.assertIn('invented-a,Invented A,Example Team,invented-b,3', graph_csv(graph, 'collaborators'))
        graph['rabid'] = 'invented-a'
        self.assertIn('invented-a,Invented A,Example Team,invented-b,1', graph_csv(graph, 'collaborators'))

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
        self.assertEqual(len(self.requested), 8)
        self.assertTrue(all(mode == 'replay' for _, mode in self.requested))
