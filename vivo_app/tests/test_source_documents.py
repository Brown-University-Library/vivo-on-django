"""
Checks PDF delivery for document viewers using made-up document bytes.
"""

from django.test import RequestFactory, SimpleTestCase

from vivo_app.lib.source_documents import document_response


class SourceDocumentTests(SimpleTestCase):
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
                self.assertEqual(response.status_code, 206)
                self.assertEqual(response.content, body[first : last + 1])
                self.assertEqual(response['Content-Range'], f'bytes {first}-{last}/{len(body)}')
                self.assertEqual(response['Content-Length'], str(last - first + 1))

    def test_unsatisfied_ranges_report_the_document_length(self) -> None:
        """
        Checks an offset beyond the document and a zero-length suffix return an empty 416 response.
        """
        body = b'%PDF-1.7 made-up document'
        for field in ('bytes=999-', 'bytes=999-1000', 'bytes=-0'):
            with self.subTest(field=field):
                request = RequestFactory().get('/source-documents/docs/i/invented.pdf', HTTP_RANGE=field)
                response = document_response(request, body)
                self.assertEqual(response.status_code, 416)
                self.assertEqual(response.content, b'')
                self.assertEqual(response['Content-Range'], f'bytes */{len(body)}')
                self.assertEqual(response['Content-Length'], '0')

    def test_unsupported_or_invalid_ranges_keep_the_complete_document(self) -> None:
        """
        Checks multiple ranges, unknown units, malformed offsets, and oversized integers fall back to a full PDF.
        """
        body = b'%PDF-1.7 made-up document'
        for field in ('bytes=0-1,4-5', 'items=0-4', 'bytes=-', 'bytes=x-4', 'bytes=8-4', 'bytes=' + '9' * 5000 + '-'):
            with self.subTest(field=field[:40]):
                request = RequestFactory().get('/source-documents/docs/i/invented.pdf', HTTP_RANGE=field)
                response = document_response(request, body)
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
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, b'' if request.method == 'HEAD' else body)
                self.assertEqual(response['Content-Length'], str(len(body)))
                self.assertNotIn('Content-Range', response)
