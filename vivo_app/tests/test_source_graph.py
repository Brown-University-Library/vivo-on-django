"""
Checks visualization response routing with made-up graph data and no network.
"""

import json
from unittest.mock import patch

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.test import TestCase, override_settings

from vivo_app.lib.page_errors import PageDataError
from vivo_app.lib.source_graph import (
    custom_graph_members,
    custom_graph_records,
    graph_csv,
    graph_page_data,
    visualization_graph,
    visualization_key,
)
from vivo_app.lib.source_requests import graph_root_key, member_details_key, profile_key
from vivo_app.lib.source_types import RequestKey, SourceResponse


@override_settings(VIZ_SERVICE_URL='http://example.invalid')
class SourceGraphTests(TestCase):
    """Checks source graph paths, response shapes, and explicit failures."""

    def test_network_control_text_preserves_reference_click_behavior(self) -> None:
        """
        Checks person and organization text match reference behavior while team labels remain unchanged.
        """
        for record_type in ('ORGANIZATION', 'PEOPLE', 'TEAM'):
            with self.subTest(record_type=record_type):
                page = render_to_string(
                    'visualization/network_data.html',
                    {
                        'graph': {
                            'id': 'invented-graph',
                            'name': 'Invented Graph',
                            'page_title': 'Invented Graph',
                            'type': record_type,
                            'kind': 'collaborators',
                            'links': [{'source': 'invented-a', 'target': 'invented-b'}],
                        },
                    },
                )
                for checkbox in ('showLabels', 'showDetails', 'forceToFit'):
                    label = f'<label for="{checkbox}">'
                    if record_type != 'TEAM':
                        self.assertNotIn(label, page)
                    else:
                        self.assertIn(label, page)
                    self.assertIn(f'id="{checkbox}" type="checkbox"', page)
                scope_name = 'Network scope' if record_type == 'TEAM' else '...'
                self.assertIn(f'class="btn-group network-scope" role="group" aria-label="{scope_name}"', page)
                self.assertIn(
                    'title="Forces the graph to fit on the screen (useful when some nodes fall outside the display area)"',
                    page,
                )

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

    def read(
        self,
        key: RequestKey,
    ) -> SourceResponse:
        """
        Reads only a made-up graph named by the test.

        Called by: test_graph_json_uses_the_matching_source_family()
        """
        if key not in self.replies:
            raise PageDataError('No invented graph matches this request.')
        return SourceResponse(200, (('content-type', 'application/json'),), json.dumps(self.replies[key]).encode())

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

    def test_graph_json_preserves_reference_utf8_and_compact_text(self) -> None:
        """
        Checks every public graph JSON route preserves Unicode, HTML escaping and unchanged source data.
        """
        graph = {
            'nodes': [{'id': 'invented-a', 'name': 'Café <Example>&\u2028'}],
            'links': [],
        }
        graph_text = '{"nodes":[{"id":"invented-a","name":"Café \\u003cExample\\u003e\\u0026\\u2028"}],"links":[]}'
        for kind, field, paths in (
            (
                'collaborators',
                'graph',
                ('/display/invented-a/viz/collab.json', '/display/invented-a/viz/collab?format=json'),
            ),
            (
                'coauthors',
                'data',
                (
                    '/display/invented-a/viz/coauthor.json',
                    '/display/invented-a/viz/coauthor?format=json',
                    '/display/invented-a/viz/coauthor_treemap?format=json',
                ),
            ),
        ):
            self.replies[visualization_key(kind, 'invented-a')] = {field: graph, 'rabid': 'invented-a'}
            expected = ('{"' + field + '":' + graph_text + ',"rabid":"invented-a"}').encode('utf-8')
            for path in paths:
                with self.subTest(path=path), patch('vivo_app.lib.source_graph.read_source', side_effect=self.read):
                    response = self.get_page(path)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
                    self.assertEqual(response.content, expected)
                    self.assertEqual(json.loads(response.content), self.replies[visualization_key(kind, 'invented-a')])

    def test_invalid_graph_shape_is_rejected(self) -> None:
        """
        Checks a successful JSON response still needs graph nodes and links.
        """
        bad = SourceResponse(200, (('content-type', 'application/json'),), b'{"graph": {"nodes": []}}')
        with self.assertRaises(PageDataError):
            visualization_graph('collaborators', 'invented-a', lambda key,: bad)
        with self.assertRaises(PageDataError):
            visualization_key('collaborators', '../private')
        with self.assertRaises(PageDataError):
            visualization_graph('collaborators', 'team-example', self.read)

    def test_empty_graph_preserves_json_and_renders_recovery_links(self) -> None:
        """
        Checks a valid empty graph preserves JSON and its recovery page and produces a successful empty CSV.
        """
        empty = {'graph': {}, 'rabid': 'invented-a', 'updated': '2026-01-02'}
        self.replies[visualization_key('collaborators', 'invented-a')] = empty
        with patch('vivo_app.lib.source_graph.read_source', side_effect=self.read):
            data = self.get_page('/display/invented-a/viz/collab.json')
            csv = self.get_page('/display/invented-a/viz/collab.csv')
            query_csv = self.get_page('/display/invented-a/viz/collab?format=csv')
            page = self.get_page('/display/invented-a/viz/collab')
        self.assertEqual(json.loads(data.content), empty)
        self.assertEqual(csv.status_code, 200)
        self.assertEqual(csv.content, b'')
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
        self.assertTrue(graph['empty_network'])

    def test_invalid_collaboration_csv_remains_an_error(self) -> None:
        """
        Checks missing or malformed graph data cannot become a successful empty CSV.
        """
        for value in ({'rabid': 'invented-a'}, {'graph': None}, {'graph': []}, {'graph': {'nodes': []}}):
            self.replies[visualization_key('collaborators', 'invented-a')] = value
            for path in ('/display/invented-a/viz/collab.csv', '/display/invented-a/viz/collab?format=csv'):
                with (
                    self.subTest(value=value, path=path),
                    patch('vivo_app.lib.source_graph.read_source', side_effect=self.read),
                ):
                    response = self.get_page(path)
                self.assertEqual(response.status_code, 503)
                self.assertIn(b'Page data unavailable', response.content)

    def test_collaboration_csv_source_failure_remains_an_error(self) -> None:
        """
        Checks a failed source read cannot become a successful empty CSV.
        """
        for path in ('/display/invented-a/viz/collab.csv', '/display/invented-a/viz/collab?format=csv'):
            with (
                self.subTest(path=path),
                patch(
                    'vivo_app.lib.source_graph.read_source', side_effect=PageDataError('The graph source is unavailable.')
                ),
            ):
                response = self.get_page(path)
            self.assertEqual(response.status_code, 503)
            self.assertIn(b'Page data unavailable', response.content)

    def test_empty_coauthor_graph_keeps_recovery_and_original_links(self) -> None:
        """
        Checks an empty coauthor response retains its explanation, controls and bare profile links.
        """
        self.replies[visualization_key('coauthors', 'invented-a')] = {}
        with patch('vivo_app.lib.source_graph.read_source', side_effect=self.read):
            data = self.get_page('/display/invented-a/viz/coauthor.json')
            page = self.get_page('/display/invented-a/viz/coauthor')
        self.assertEqual(json.loads(data.content), {})
        self.assertContains(page, 'No coauthor data is available for this researcher.')
        self.assertContains(page, 'two Brown University coauthors must approve the same publication.')
        self.assertContains(page, 'review and approve your publications via the')
        self.assertContains(page, 'network-empty-coauthor')
        self.assertContains(page, 'href="/display/invented-a#Publications"')
        self.assertContains(page, 'href="/display/invented-a"')
        self.assertContains(page, 'Display labels&nbsp;')
        self.assertContains(page, '<a id="embedHtml" href="#"')
        graph = graph_page_data({}, 'coauthors', 'invented-a')
        self.assertTrue(graph['empty_network'])
        self.assertFalse(graph['empty_collaboration'])

    def test_coauthor_nodes_without_links_use_empty_recovery(self) -> None:
        """
        Checks isolated nodes retain their source data while the page shows empty-network recovery.
        """
        value: dict[str, object] = {'data': {'nodes': [{'id': 'invented-a', 'name': 'Invented A'}], 'links': []}}
        graph = graph_page_data(value, 'coauthors', 'invented-a')
        self.assertTrue(graph['empty_network'])
        self.assertEqual(graph['source'], value['data'])

    def test_populated_graph_keeps_its_existing_rendering(self) -> None:
        """
        Checks populated graphs retain their nodes and use the populated-page controls.
        """
        value = self.replies[visualization_key('collaborators', 'invented-a')]
        graph = graph_page_data(value, 'collaborators', 'invented-a')
        self.assertEqual(graph['source'], value['graph'])
        self.assertFalse(graph['empty_collaboration'])
        self.assertFalse(graph['empty_network'])
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
        self.assertContains(page, 'href="/display/invented-a#Publications"')
        self.assertContains(page, 'href="/display/invented-a"')
        self.assertContains(page, 'role="button" href="/display/invented-a/viz/coauthor"')
        self.assertContains(page, '<a id="embedHtml" href="#"')
        self.assertContains(page, '<a id="downloadPng" href="#"')
        self.assertContains(page, 'rows="15" class="htmlSnippet"')
        self.assertEqual(json.loads(json_response.content), self.replies[visualization_key('coauthors', 'invented-a')])
        self.assertIn('invented-a,Invented A,Example Group,invented-b,3', csv_response.content.decode())


class CustomGraphTests(TestCase):
    """Checks Rails-calculated collaboration graphs use member records in repeated requests."""

    def setUp(self) -> None:
        """
        Creates made-up root and neighboring faculty records.
        """
        prefix = 'http://vivo.brown.edu/individual/'
        self.root: dict[str, object] = {
            'id': prefix + 'invented-root',
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
        self.requested: list[RequestKey] = []

    def solr_response(self, people: list[tuple[str, dict[str, object]]]) -> SourceResponse:
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
        return SourceResponse(200, (('content-type', 'application/json'),), json.dumps(body).encode())

    def json_response(self, value: dict[str, object]) -> SourceResponse:
        """Wraps a made-up visualization availability list."""
        return SourceResponse(200, (('content-type', 'application/json'),), json.dumps(value).encode())

    def read(
        self,
        key: RequestKey,
    ) -> SourceResponse:
        """
        Reads only the made-up member responses and records the exact requests.

        Called by: test_repeated_reads_use_the_same_member_requests(), test_missing_source_response_fails()
        """
        self.requested.append(key)
        if key not in self.responses:
            raise PageDataError('The requested source response is missing.')
        return self.responses[key]

    def test_repeated_reads_use_the_same_member_requests(self) -> None:
        """
        Checks team roots, neighboring people, graph levels, and CSV use the same source requests.
        """
        with patch('vivo_app.lib.source_graph.team_definition', return_value=('Example Team', ['invented-root'])):
            first = visualization_graph('collaborators', 'team-example', self.read)
            first_keys = list(self.requested)
            self.requested.clear()
            repeated = visualization_graph('collaborators', 'team-example', self.read)
        self.assertEqual(first, repeated)
        self.assertEqual(first_keys, list(self.requested))
        self.assertEqual(first_keys, list(self.responses))
        graph = first['graph']
        assert isinstance(graph, dict)
        nodes = graph['nodes']
        assert isinstance(nodes, list)
        self.assertEqual([node['level'] for node in nodes], [0, 1, 2])
        self.assertIsNone(nodes[2]['group'])
        self.assertEqual(nodes[0]['faculty']['item']['name'], 'Invented Root')
        self.assertTrue(nodes[0]['faculty']['item']['has_coauthors'])
        self.assertTrue(nodes[0]['faculty']['item']['has_collaborators'])
        self.assertNotIn('faculty', nodes[1])
        self.assertIn('Invented Root', graph_csv(first, 'collaborators'))

    def test_missing_source_response_fails(self) -> None:
        """
        Checks that a missing second-level member batch does not contact another source.
        """
        self.responses.pop(member_details_key(['invented-neighbor']))
        with (
            patch('vivo_app.lib.source_graph.team_definition', return_value=('Example Team', ['invented-root'])),
            self.assertRaisesRegex(PageDataError, 'source response is missing'),
        ):
            visualization_graph('collaborators', 'team-example', self.read)

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
            value = visualization_graph('collaborators', 'team-example', self.read)
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
            'vivo_app.lib.source_graph.team_definition', return_value=('Example Team', ['invented-root', 'invented-missing'])
        ):
            result = visualization_graph('collaborators', 'team-example', self.read)
        graph = result['graph']
        assert isinstance(graph, dict)
        nodes = graph['nodes']
        assert isinstance(nodes, list)
        self.assertEqual(nodes[0]['name'], 'Invented Root')

    def test_missing_availability_list_fails(self) -> None:
        """Requires the production availability list used by nested faculty fields."""
        self.responses.pop(visualization_key('coauthors'))
        with (
            patch('vivo_app.lib.source_graph.team_definition', return_value=('Example Team', ['invented-root'])),
            self.assertRaisesRegex(PageDataError, 'source response is missing'),
        ):
            visualization_graph('collaborators', 'team-example', self.read)

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
        records = custom_graph_records(identifiers, self.read, True)
        self.assertEqual(set(records), set(identifiers))
        self.assertEqual(list(self.requested), list(self.responses))

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
        self.responses[profile_key(identifier)] = SourceResponse(200, (), json.dumps(profile).encode())
        self.responses[graph_root_key(['invented-root', 'invented-missing'])] = self.solr_response(
            [('invented-root', self.root)]
        )
        with patch(
            'vivo_app.lib.source_graph.custom_organization_members', return_value=['invented-root', 'invented-missing']
        ) as members:
            first = visualization_graph('collaborators', identifier, self.read)
            first_keys = list(self.requested)
            self.requested.clear()
            repeated = visualization_graph('collaborators', identifier, self.read)
        self.assertEqual(first['graph'], repeated['graph'])
        self.assertEqual(first_keys, list(self.requested))
        self.assertEqual(
            first_keys,
            [
                profile_key(identifier),
                graph_root_key(['invented-root', 'invented-missing']),
                visualization_key('coauthors'),
                visualization_key('collaborators'),
                member_details_key(['invented-neighbor']),
            ],
        )
        members.assert_called_with(identifier, self.read)
        graph = repeated['graph']
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
        self.responses[profile_key(identifier)] = SourceResponse(200, (), json.dumps(other).encode())
        with self.assertRaisesRegex(PageDataError, 'organization is unavailable'):
            custom_graph_members(identifier, self.read)

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
        self.responses[profile_key(identifier)] = SourceResponse(200, (), json.dumps(profile).encode())
        with patch('vivo_app.lib.source_graph.custom_organization_members', return_value=[]):
            name, members = custom_graph_members(identifier, self.read)
        self.assertEqual(name, 'Invented Institute')
        self.assertEqual(members, ['invented-root'])

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

    def test_team_page_uses_calculated_graph_from_sources(self) -> None:
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
