"""
Checks URL additions and invalid requests without contacting public data sources.
"""

import json
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings

from vivo_app.lib.page_errors import PageDataError
from vivo_app.lib.source_requests import document_key, vitro_key
from vivo_app.lib.source_types import SourceResponse


class PublicRequestHandlingTests(SimpleTestCase):
    def setUp(self) -> None:
        """
        Checks requests against temporary shared caches and made-up responses.
        """
        directory = self.enterContext(TemporaryDirectory())
        self.enterContext(
            override_settings(
                MEDIA_CACHE_TIMEOUT_SECONDS=60,
                CHART_CACHE_TIMEOUT_SECONDS=60,
                VIVO_EXPORT_CACHE_TIMEOUT_SECONDS=60,
                REPORT_CACHE_LOCK_DIR=directory + '/locks',
                CACHES={
                    'default': {
                        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
                        'LOCATION': directory + '/cache',
                    }
                },
            )
        )
        self.pdf = SourceResponse(200, (('content-type', 'application/pdf'),), b'%PDF-1.7 Example CV')
        self.publications: dict[str, object] = {'matrix': [], 'years': [], 'columns': [], 'nodes': []}
        self.research: dict[str, object] = {'nodes': [[], []], 'links': []}

    def request_response(self, path: str, method: str = 'GET', range_value: str = '') -> HttpResponse:
        """
        Requests a local page or download and checks the response type.

        Called by: PublicRequestHandlingTests test methods
        """
        response = self.client.generic(method, path, HTTP_RANGE=range_value)
        assert isinstance(response, HttpResponse)
        return response

    def test_document_additions_share_cache_without_delaying_replacements(self) -> None:
        """
        Checks tracking and translation additions preserve PDF bytes, versions, ranges, and fixed cache expiry.
        """
        with (
            patch('vivo_app.views.read_source', return_value=self.pdf) as reader,
            patch('django.utils.log.AdminEmailHandler.emit') as email,
            patch('time.time', return_value=100) as clock,
        ):
            for prefix in ('', '/source-documents'):
                for extra in ('', '&utm_source=example', '&_x_tr_sl=en', '&amp;_x_tr_sl=en', '&shem=share,'):
                    path = prefix + '/docs/i/invented_cv.pdf?dt=1' + extra
                    with self.subTest(path=path):
                        response = self.request_response(path)
                        self.assertEqual(response.content, self.pdf.body)
                        self.assertEqual(response['Content-Type'], 'application/pdf')
                        self.assertIn('no-store', response['Cache-Control'])
                        head = self.request_response(path, 'HEAD')
                        self.assertEqual(head.content, b'')
                        self.assertEqual(head['Content-Length'], str(len(self.pdf.body)))
            partial = self.request_response('/docs/i/invented_cv.pdf?dt=1&utm_source=range', range_value='bytes=0-4')
            self.assertEqual(partial.status_code, 206)
            self.assertEqual(partial.content, b'%PDF-')
            reader.assert_called_once_with(document_key('/docs/i/invented_cv.pdf', (('dt', '1'),)))
            updated = SourceResponse(200, self.pdf.headers, b'%PDF-1.7 Updated CV')
            reader.return_value = updated
            clock.return_value = 159
            self.assertEqual(self.request_response('/docs/i/invented_cv.pdf?dt=1&utm_source=late').content, self.pdf.body)
            clock.return_value = 161
            self.assertEqual(self.request_response('/docs/i/invented_cv.pdf?dt=1&_x_tr_sl=en').content, updated.body)
            self.assertEqual(reader.call_count, 2)
            self.request_response('/docs/i/invented_cv.pdf?dt=2&utm_source=example')
            reader.assert_called_with(document_key('/docs/i/invented_cv.pdf', (('dt', '2'),)))
            email.assert_not_called()

    def test_chart_additions_share_formats_and_keep_fixed_expiry(self) -> None:
        """
        Checks extra URL parameters reuse completed charts without postponing faculty updates.
        """
        with (
            patch(
                'vivo_app.views.publication_history_data', return_value=('Example Organization', self.publications)
            ) as pubs,
            patch('vivo_app.views.research_areas_data', return_value=('Example Organization', self.research)) as research,
            patch('django.utils.log.AdminEmailHandler.emit') as email,
            patch('time.time', return_value=100) as clock,
        ):
            for kind, suffixes in (('publications', ('', '.json', '.csv')), ('research', ('', '.json'))):
                for suffix in suffixes:
                    for extra in ('', '?utm_source=example', '?_x_tr_sl=en&amp;_x_tr_tl=es'):
                        response = self.request_response('/display/org-example/viz/' + kind + suffix + extra)
                        self.assertEqual(response.status_code, 200)
                        self.assertIn('no-store', response['Cache-Control'])
                        if not suffix:
                            self.assertContains(response, 'Example Organization')
                        elif suffix == '.json':
                            self.assertEqual(
                                json.loads(response.content), self.publications if kind == 'publications' else self.research
                            )
                        else:
                            self.assertEqual(response.content, b'year,year_total')
            pubs.assert_called_once_with('org-example')
            research.assert_called_once_with('org-example')
            pubs.return_value = ('Updated Organization', self.publications)
            research.return_value = ('Updated Organization', self.research)
            for instant, name in ((159, 'Example Organization'), (161, 'Updated Organization')):
                clock.return_value = instant
                for kind in ('publications', 'research'):
                    self.assertContains(self.request_response('/display/org-example/viz/' + kind + '?utm_source=late'), name)
            self.assertEqual(pubs.call_count, 2)
            self.assertEqual(research.call_count, 2)
            email.assert_not_called()

    def test_graph_additions_preserve_pages_downloads_and_fit(self) -> None:
        """
        Checks collaboration, coauthor, and treemap pages retain their formats and layout option with extra parameters.
        """
        graph = {'nodes': [], 'links': []}
        value = {'graph': graph, 'data': graph}
        subject = {'name': 'Example Person', 'page_title': 'Example Person', 'title': 'Professor', 'type': 'PEOPLE'}
        with (
            patch('vivo_app.views.visualization_graph', return_value=value) as source,
            patch('vivo_app.views.graph_subject_data', return_value=subject),
            patch('django.utils.log.AdminEmailHandler.emit') as email,
        ):
            for kind in ('collab', 'coauthor', 'coauthor_treemap'):
                for query in ('', 'format=json&', 'format=csv&'):
                    response = self.request_response('/display/invented-a/viz/' + kind + '?' + query + 'utm_source=example')
                    self.assertEqual(response.status_code, 200)
                    if not query:
                        self.assertContains(response, 'Example Person')
                    elif query.startswith('format=json'):
                        self.assertEqual(json.loads(response.content), value)
                if kind != 'coauthor_treemap':
                    fit = self.request_response('/display/invented-a/viz/' + kind + '?fit=1&_x_tr_sl=en')
                    self.assertEqual(fit.status_code, 200)
                    self.assertContains(fit, 'id="forceToFit" type="checkbox" checked')
                    for suffix in ('json', 'csv'):
                        response = self.request_response(
                            '/display/invented-a/viz/' + kind + '.' + suffix + '?utm_source=example'
                        )
                        self.assertEqual(response.status_code, 200)
            self.assertTrue(all(call.args[1] == 'invented-a' for call in source.call_args_list))
            email.assert_not_called()

    def test_invalid_request_details_stop_before_cache_or_sources_without_email(self) -> None:
        """
        Checks invalid paths, versions, formats, and layout values receive ordinary client errors before expensive work.
        """
        cases = (
            ('/source-images/profile-images/abc/', 404),
            ('/source-documents/docs/i/invented_cv.txt', 404),
            ('/docs/i/invented_cv.pdf?dt=bad%27', 400),
            ('/docs/i/invented_cv.pdf?dt=bad%27[0]', 400),
            ('/docs/i/invented_cv.pdf?dt=', 400),
            ('/docs/i/invented_cv.pdf?dt=1&dt=2&utm_source=example', 400),
            ('/individual/invented-a,%22Example,', 404),
            ('/individual/invented-a%22,%22level%22:0', 404),
            ('/individual/invented-a/other.rdf', 404),
            ('/individual/invented-a/invented-a.unknown', 404),
            ('/individual/invented-a/invented-a.rdf?format=json', 400),
            ('/display/bad%22name/viz/collab', 404),
            ('/display/bad%22name/viz/research', 404),
            ('/display/invented-a/viz/collab?format=bad&utm_source=example', 400),
            ('/display/invented-a/viz/coauthor?fit=0', 400),
            ('/display/invented-a/viz/coauthor_treemap?format=json&format=csv', 400),
            ('/display/invented-a/viz/collab.json?format=csv', 400),
            ('/display/org-example/viz/publications.json?format=csv', 400),
            ('/display/org-example/viz/research?format=bad', 400),
        )
        with (
            patch('vivo_app.views.cached_media') as media,
            patch('vivo_app.views.cached_chart') as chart,
            patch('vivo_app.views.cached_representation') as download,
            patch('vivo_app.views.visualization_graph') as graph,
            patch('vivo_app.views.graph_subject_data') as subject,
            patch('django.utils.log.AdminEmailHandler.emit') as email,
        ):
            for path, status in cases:
                for method in ('get', 'head'):
                    with self.subTest(path=path, method=method):
                        response = self.request_response(path, method.upper())
                        self.assertEqual(response.status_code, status)
            for operation in (media, chart, download, graph, subject, email):
                operation.assert_not_called()

    def test_unsupported_methods_stop_before_cache_or_sources(self) -> None:
        """
        Checks unsupported methods return 405 and advertise GET and HEAD without reading data or sending error email.
        """
        paths = (
            '/source-images/profile-images/abc/',
            '/source-images/profile-images/abc/portrait.jpg',
            '/source-documents/docs/i/invented_cv.pdf',
            '/docs/i/invented_cv.pdf',
            '/display/org-example/viz/publications',
            '/display/org-example/viz/research.json',
            '/display/invented-a/viz/collab',
            '/display/invented-a/viz/coauthor.json',
            '/display/invented-a/viz/collab.csv',
            '/display/invented-a/viz/coauthor_treemap',
            '/individual/invented-a',
            '/individual/invented-a/invented-a.rdf',
        )
        with (
            patch('vivo_app.views.cached_media') as media,
            patch('vivo_app.views.cached_chart') as chart,
            patch('vivo_app.views.cached_representation') as download,
            patch('vivo_app.views.visualization_graph') as graph,
            patch('vivo_app.views.graph_subject_data') as subject,
            patch('django.utils.log.AdminEmailHandler.emit') as email,
        ):
            for path in paths:
                for method in ('OPTIONS', 'POST', 'PUT', 'DELETE'):
                    with self.subTest(path=path, method=method):
                        response = self.request_response(path, method)
                        self.assertEqual(response.status_code, 405)
                        self.assertEqual(response['Allow'], 'GET, HEAD')
            for operation in (media, chart, download, graph, subject, email):
                operation.assert_not_called()

    def test_download_additions_share_original_bytes_and_exact_source_requests(self) -> None:
        """
        Checks ignored additions cannot create separate download entries or change what the source receives.
        """
        source = SourceResponse(200, (), b'Example original bytes')
        with (
            patch('vivo_app.views.read_source', return_value=source) as reader,
            patch('django.utils.log.AdminEmailHandler.emit') as email,
        ):
            for fmt in ('rdf', 'ttl', 'jsonld'):
                for extra in ('', '?utm_source=example', '?format=' + fmt + '&_x_tr_sl=en'):
                    path = '/individual/invented-a/invented-a.' + fmt + extra
                    response = self.request_response(path)
                    self.assertEqual(response.content, source.body)
                    self.assertIn('no-store', response['Cache-Control'])
                    self.assertEqual(self.request_response(path, 'HEAD').content, b'')
            self.assertEqual(
                [call.args[0] for call in reader.call_args_list],
                [vitro_key('invented-a', fmt) for fmt in ('rdf', 'ttl', 'jsonld')],
            )
            email.assert_not_called()

    def test_real_source_failures_with_url_additions_keep_error_alerts(self) -> None:
        """
        Checks request cleanup does not hide failures while retrieving media, charts, graphs, or original downloads.
        """
        failure = PageDataError('Example source failure.')
        paths = (
            '/docs/i/invented_cv.pdf?dt=1&utm_source=example',
            '/source-images/profile-images/abc/portrait.jpg?utm_source=example',
            '/display/org-example/viz/publications?utm_source=example',
            '/display/org-example/viz/research?utm_source=example',
            '/display/invented-a/viz/collab?format=json&utm_source=example',
            '/individual/invented-a/invented-a.rdf?utm_source=example',
        )
        with (
            patch('vivo_app.views.read_source', side_effect=failure),
            patch('vivo_app.views.publication_history_data', side_effect=failure),
            patch('vivo_app.views.research_areas_data', side_effect=failure),
            patch('vivo_app.views.visualization_graph', side_effect=failure),
            patch('django.utils.log.AdminEmailHandler.emit') as email,
        ):
            for path in paths:
                with self.subTest(path=path):
                    self.assertEqual(self.request_response(path).status_code, 503)
            self.assertEqual(email.call_count, len(paths))

    def test_invalid_source_redirect_remains_a_source_error(self) -> None:
        """
        Checks an invalid version supplied by the document source is not mistaken for a bad visitor request.
        """
        source = SourceResponse(302, (('location', 'https://source.invalid/docs/i/invented_cv.pdf?dt=bad!'),), b'')
        with (
            patch('vivo_app.views.read_source', return_value=source),
            patch('django.utils.log.AdminEmailHandler.emit') as email,
        ):
            self.assertEqual(self.request_response('/docs/i/invented_cv.pdf?dt=1&utm_source=example').status_code, 503)
            email.assert_called_once()
