"""
Checks PDF delivery for document viewers using made-up document bytes.
"""

import io
import zipfile
from functools import partial
from unittest.mock import patch

from django.http import HttpResponse, StreamingHttpResponse
from django.middleware.common import CommonMiddleware
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import get_script_prefix, set_script_prefix

from vivo_app.lib.source_documents import document_response
from vivo_app.lib.source_requests import document_key
from vivo_app.lib.source_types import SourceResponse


def word_document_bytes() -> bytes:
    """
    Builds a small Word archive with made-up content for format checks.

    Called by: SourceDocumentTests, SourceMediaTests
    """
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as archive:
        archive.writestr('[Content_Types].xml', '<Types/>')
        archive.writestr('word/document.xml', '<document>Example CV</document>')
    return output.getvalue()


class SourceDocumentTests(SimpleTestCase):
    def test_word_files_at_pdf_urls_show_friendly_404_without_error_email(self) -> None:
        """
        Checks Word CVs are withheld with a friendly page and warning, including HEAD and original URLs.
        """
        for body in (
            b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' + b'\x00' * 64 + 'WordDocument'.encode('utf-16-le'),
            word_document_bytes(),
        ):
            source = SourceResponse(200, (('content-type', 'application/pdf'),), body)
            for prefix in ('/source-documents', ''):
                for method in ('get', 'head'):
                    with self.subTest(prefix=prefix, method=method, signature=body[:4]):
                        with (
                            patch('vivo_app.views.read_source', return_value=source),
                            patch('django.utils.log.AdminEmailHandler.emit') as email,
                            self.assertLogs('vivo_app.views', level='WARNING') as logs,
                        ):
                            response = getattr(self.client, method)(
                                prefix + '/docs/i/invented_cv.pdf?dt=1', HTTP_RANGE='bytes=0-4'
                            )
                        self.assertEqual(response.status_code, 404)
                        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
                        if method == 'get':
                            self.assertContains(
                                response,
                                'This CV is temporarily unavailable. Please contact the profile owner.',
                                status_code=404,
                            )
                            self.assertTemplateUsed(response, 'documents/unavailable.html')
                        else:
                            self.assertEqual(response.content, b'')
                        self.assertNotIn(body, response.content)
                        self.assertNotIn('Content-Disposition', response)
                        self.assertNotIn('Accept-Ranges', response)
                        self.assertIn('no-store', response['Cache-Control'])
                        self.assertIn('cv_pdf_validation_failed', logs.output[0])
                        self.assertIn('filename, ``docs/i/invented_cv.pdf``', logs.output[0])
                        self.assertTrue(all(record.levelname == 'WARNING' for record in logs.records))
                        email.assert_not_called()

    def test_unsupported_files_are_not_sent_as_successful_documents(self) -> None:
        """
        Checks HTML, incomplete ZIPs, unrelated containers, and empty documents keep the unavailable response.
        """
        other_zip = io.BytesIO()
        with zipfile.ZipFile(other_zip, 'w') as archive:
            archive.writestr('example.txt', 'Example content')
        for body in (b'<html>Example error</html>', b'PK\x03\x04broken', other_zip.getvalue(), b''):
            with self.subTest(body=body[:20]):
                with patch(
                    'vivo_app.views.read_source',
                    return_value=SourceResponse(200, (('content-type', 'application/pdf'),), body),
                ):
                    response = self.client.get('/source-documents/docs/i/invented_cv.pdf')
                assert isinstance(response, HttpResponse)
                self.assertContains(response, 'This CV is temporarily unavailable.', status_code=404)
                self.assertIn('no-store', response['Cache-Control'])

    def test_pdf_signature_alone_does_not_bypass_content_type_check(self) -> None:
        """
        Checks that PDF-looking bytes still need the source's PDF content type.
        """
        for content_type in ('application/octet-stream', 'application/msword', 'text/html', ''):
            source = SourceResponse(200, (('content-type', content_type),), b'%PDF-1.7 Example CV')
            with self.subTest(content_type=content_type), patch('vivo_app.views.read_source', return_value=source):
                response = self.client.get('/source-documents/docs/i/invented_cv.pdf')
            assert isinstance(response, HttpResponse)
            self.assertContains(response, 'This CV is temporarily unavailable.', status_code=404)

    def test_unavailable_cv_page_keeps_mounted_search_link(self) -> None:
        """
        Checks the error page renders a usable search link when the application has a browser prefix.
        """
        source = SourceResponse(200, (('content-type', 'application/pdf'),), b'Example invalid document')
        previous_prefix = get_script_prefix()
        set_script_prefix('/mounted')
        try:
            with patch('vivo_app.views.read_source', return_value=source):
                response = self.client.get('/docs/i/invented_cv.pdf', SCRIPT_NAME='/mounted')
        finally:
            set_script_prefix(previous_prefix)
        assert isinstance(response, HttpResponse)
        self.assertContains(response, 'href="/mounted/search"', status_code=404)

    def test_original_document_path_uses_selected_reader_and_range_handler(self) -> None:
        """
        Checks source original paths preserve version queries, full GET, HEAD and ranges.
        """
        body = b'%PDF-1.7 made-up document'
        result = SourceResponse(200, (('content-type', 'application/pdf'),), body)
        for method, headers, status, expected in (
            ('get', {}, 200, body),
            ('head', {}, 200, b''),
            ('get', {'HTTP_RANGE': 'bytes=0-4'}, 206, body[:5]),
        ):
            with self.subTest(method=method, headers=headers):
                with (
                    override_settings(SOLR_URL='https://source.invalid/core', TURNSTILE_ENABLED=False),
                    patch('vivo_app.views.read_source', return_value=result) as read,
                ):
                    response = getattr(self.client, method)('/docs/i/invented_cv.pdf?dt=1', **headers)
                self.assertEqual(response.status_code, status)
                self.assertEqual(response['Content-Type'], 'application/pdf')
                self.assertEqual(response.content, expected)
                read.assert_called_once_with(document_key('/docs/i/invented_cv.pdf', (('dt', '1'),)))

    @override_settings(DOCUMENTS_URL='https://source.invalid')
    def test_original_document_version_redirect_stays_mounted(self) -> None:
        """
        Checks a source version redirect keeps the existing reader route and deployment prefix.
        """
        result = SourceResponse(302, (('location', 'https://source.invalid/docs/i/invented_cv.pdf?dt=1'),), b'')
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
