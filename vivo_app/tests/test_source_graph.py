"""
Checks visualization response routing with made-up graph data and no network.
"""

import json
from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase, override_settings

from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RequestKey
from vivo_app.lib.source_graph import visualization_graph, visualization_key


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
            download = self.get_page('/display/invented-a/viz/coauthor/?format=csv')
            collab = self.get_page('/display/invented-a/viz/collab/?format=csv')
            missing = self.get_page('/display/other/viz/coauthor/')
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Invented A')
        self.assertIn('id,name,info,collab_with,count', download.content.decode())
        self.assertIn('invented-a,Invented A,Example Group,invented-b,3', download.content.decode())
        self.assertIn('invented-a,Invented A,Example Group,invented-b,1', collab.content.decode())
        self.assertEqual(missing.status_code, 503)
