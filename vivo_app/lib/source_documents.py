"""
Returns complete PDFs or the single byte range requested by a document viewer.
"""

import re

from django.http import HttpRequest, HttpResponse, StreamingHttpResponse

RANGE_ERROR_BODY = (
    b'<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">\n'
    b'<html><head>\n'
    b'<title>416 Requested Range Not Satisfiable</title>\n'
    b'</head><body>\n'
    b'<h1>Requested Range Not Satisfiable</h1>\n'
    b'<p>None of the range-specifier values in the Range\n'
    b'request-header field overlap the current extent\n'
    b'of the selected resource.</p>\n'
    b'</body></html>\n'
)


def single_byte_range(value: str, size: int) -> tuple[int, int] | None:
    """
    Parses one inclusive byte range, leaving unsupported or invalid fields unused.

    Called by: document_response()
    """
    result: tuple[int, int] | None = None
    match = re.fullmatch(r'bytes=([0-9]*)-([0-9]*)', value.strip(), flags=re.IGNORECASE)
    if match and (match[1] or match[2]):
        try:
            if match[1]:
                first = int(match[1])
                last = int(match[2]) if match[2] else size - 1
                if not match[2] or last >= first:
                    result = (first, min(last, size - 1))
            else:
                length = int(match[2])
                if length > 0:
                    result = (max(0, size - length), size - 1)
        except ValueError:
            result = None
    return result


def document_response(request: HttpRequest, body: bytes) -> HttpResponse | StreamingHttpResponse:
    """
    Serves PDF bytes with complete lengths, single ranges, and body-free HEAD responses.

    Called by: vivo_app.views.source_document()
    """
    size = len(body)
    response: HttpResponse | StreamingHttpResponse = HttpResponse(body, content_type='application/pdf')
    range_value = request.META.get('HTTP_RANGE', '')
    if request.method == 'GET' and 'HTTP_IF_RANGE' not in request.META and isinstance(range_value, str):
        selected = single_byte_range(range_value, size)
        if selected is not None:
            first, last = selected
            if first > last:
                ## Streaming keeps middleware from adding a length absent from the reference error.
                response = StreamingHttpResponse(
                    (RANGE_ERROR_BODY,), status=416, content_type='text/html; charset=iso-8859-1'
                )
            else:
                response = HttpResponse(body[first : last + 1], status=206, content_type='application/pdf')
                response['Content-Range'] = f'bytes {first}-{last}/{size}'
    if isinstance(response, HttpResponse):
        response['Accept-Ranges'] = 'bytes'
        response['Content-Length'] = str(len(response.content))
        if request.method == 'HEAD':
            response.content = b''
    return response
