"""
Checks PDF delivery for document viewers using made-up document bytes.
"""

from functools import partial
from unittest.mock import patch

from django.http import HttpResponse, StreamingHttpResponse
from django.middleware.common import CommonMiddleware
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import get_script_prefix, set_script_prefix

from vivo_app.lib.recorded_responses import RecordedResponse
from vivo_app.lib.source_documents import document_response
from vivo_app.lib.source_requests import document_key


class SourceDocumentTests(SimpleTestCase):
    def test_original_document_path_uses_selected_reader_and_range_handler(self) -> None:
        """
        Checks live and replay original paths preserve version queries, full GET, HEAD and ranges.
        """
        body = b'%PDF-1.7 made-up document'
        result = RecordedResponse(200, (('content-type', 'application/pdf'),), body)
        for mode in ('live', 'replay'):
            for method, headers, status, expected in (
                ('get', {}, 200, body),
                ('head', {}, 200, b''),
                ('get', {'HTTP_RANGE': 'bytes=0-4'}, 206, body[:5]),
            ):
                with self.subTest(mode=mode, method=method, headers=headers):
                    with (
                        override_settings(
                            PAGE_DATA_MODE=mode,
                            SOLR_URL='https://source.invalid/core',
                            UPSTREAM_RECORDING_MANIFEST='unused-recording.json',
                            TURNSTILE_ENABLED=False,
                        ),
                        patch('vivo_app.views.read_source', return_value=result) as read,
                    ):
                        response = getattr(self.client, method)('/docs/i/invented_cv.pdf?dt=1', **headers)
                    self.assertEqual(response.status_code, status)
                    self.assertEqual(response['Content-Type'], 'application/pdf')
                    self.assertEqual(response.content, expected)
                    read.assert_called_once_with(document_key('/docs/i/invented_cv.pdf', (('dt', '1'),)), mode)

    @override_settings(PAGE_DATA_MODE='live', DOCUMENTS_URL='https://source.invalid')
    def test_original_document_version_redirect_stays_mounted(self) -> None:
        """
        Checks a source version redirect keeps the existing reader route and deployment prefix.
        """
        result = RecordedResponse(302, (('location', 'https://source.invalid/docs/i/invented_cv.pdf?dt=1'),), b'')
        previous_prefix = get_script_prefix()
        set_script_prefix('/mounted')
        try:
            with patch('vivo_app.views.read_source', return_value=result):
                response = self.client.get('/docs/i/invented_cv.pdf', SCRIPT_NAME='/mounted')
        finally:
            set_script_prefix(previous_prefix)
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/mounted/source-documents/docs/i/invented_cv.pdf?dt=1')

    @override_settings(PAGE_DATA_MODE='prototype')
    def test_original_saved_document_does_not_fall_back_to_live(self) -> None:
        """
        Checks an absent saved document remains unavailable without contacting a source.
        """
        with patch('vivo_app.views.get_response_data', return_value=None), patch('vivo_app.views.read_source') as read:
            response = self.client.get('/docs/i/invented_cv.pdf?dt=1')
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 404)
        read.assert_not_called()

    def test_complete_pdf_and_head_report_the_same_length(self) -> None:
        """
        Checks full downloads retain all bytes and HEAD omits the body while keeping its length.
        """
        body = b'%PDF-1.7 made-up document'
        factory = RequestFactory()
        for method in ('get', 'head'):
            with self.subTest(method=method):
                request = getattr(factory, method)('/source-documents/docs/i/invented.pdf')
                response = document_response(request, body)
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response['Content-Type'], 'application/pdf')
                self.assertEqual(response['Accept-Ranges'], 'bytes')
                self.assertEqual(response['Content-Length'], str(len(body)))
                self.assertEqual(response.content, body if method == 'get' else b'')

    def test_single_ranges_return_the_requested_document_bytes(self) -> None:
        """
        Checks closed, open-ended, suffix, and end-clamped ranges preserve PDF bytes and offsets.
        """
        body = b'%PDF-1.7 made-up document'
        for field, first, last in (
            ('bytes=0-4', 0, 4),
            ('bytes=5-', 5, len(body) - 1),
            ('bytes=-3', len(body) - 3, len(body) - 1),
            ('bytes=5-999', 5, len(body) - 1),
            ('bytes=-999', 0, len(body) - 1),
            ('BYTES=0-0', 0, 0),
        ):
            with self.subTest(field=field):
                request = RequestFactory().get('/source-documents/docs/i/invented.pdf', HTTP_RANGE=field)
                response = document_response(request, body)
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, 206)
                self.assertEqual(response.content, body[first : last + 1])
                self.assertEqual(response['Content-Range'], f'bytes {first}-{last}/{len(body)}')
                self.assertEqual(response['Content-Length'], str(last - first + 1))

    def test_unsatisfied_ranges_keep_the_reference_error_response(self) -> None:
        """
        Checks offsets beyond the document return the reference HTML error without document metadata.
        """
        body = b'%PDF-1.7 made-up document'
        for field in ('bytes=999-', 'bytes=999-1000'):
            with self.subTest(field=field):
                request = RequestFactory().get('/source-documents/docs/i/invented.pdf', HTTP_RANGE=field)
                response = document_response(request, body)
                assert isinstance(response, StreamingHttpResponse)
                self.assertEqual(response.status_code, 416)
                self.assertEqual(response['Content-Type'], 'text/html; charset=iso-8859-1')
                self.assertFalse(response.is_async)
                content = b''.join(response)
                self.assertEqual(len(content), 314)
                self.assertIn(b'<h1>Requested Range Not Satisfiable</h1>', content)
                self.assertIn(b'of the selected resource.</p>', content)
                for header in ('Content-Range', 'Content-Length', 'Accept-Ranges'):
                    self.assertNotIn(header, response)

    def test_common_middleware_keeps_error_length_absent(self) -> None:
        """
        Checks response middleware preserves the reference error's omitted length header.
        """
        body = b'%PDF-1.7 made-up document'
        request = RequestFactory().get('/source-documents/docs/i/invented.pdf', HTTP_RANGE='bytes=999-')
        response = document_response(request, body)
        response = CommonMiddleware(partial(document_response, body=body)).process_response(request, response)
        self.assertEqual(response.status_code, 416)
        self.assertNotIn('Content-Length', response)

    def test_unsupported_or_invalid_ranges_keep_the_complete_document(self) -> None:
        """
        Checks multiple ranges, unknown units, malformed offsets, and oversized integers fall back to a full PDF.
        """
        body = b'%PDF-1.7 made-up document'
        for field in (
            'bytes=0-1,4-5',
            'items=0-4',
            'bytes=-',
            'bytes=-0',
            'bytes=x-4',
            'bytes=8-4',
            'bytes=' + '9' * 5000 + '-',
        ):
            with self.subTest(field=field[:40]):
                request = RequestFactory().get('/source-documents/docs/i/invented.pdf', HTTP_RANGE=field)
                response = document_response(request, body)
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, body)
                self.assertNotIn('Content-Range', response)

    def test_head_and_unconfirmed_if_range_ignore_range(self) -> None:
        """
        Checks HEAD ignores ranges and an unmatched If-Range requests the complete document.
        """
        body = b'%PDF-1.7 made-up document'
        factory = RequestFactory()
        requests = (
            factory.head('/source-documents/docs/i/invented.pdf', HTTP_RANGE='bytes=0-4'),
            factory.get('/source-documents/docs/i/invented.pdf', HTTP_RANGE='bytes=0-4', HTTP_IF_RANGE='"previous"'),
        )
        for request in requests:
            with self.subTest(method=request.method):
                response = document_response(request, body)
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, b'' if request.method == 'HEAD' else body)
                self.assertEqual(response['Content-Length'], str(len(body)))
                self.assertNotIn('Content-Range', response)
