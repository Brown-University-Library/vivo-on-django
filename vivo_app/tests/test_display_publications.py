"""
Checks unsupported publication entry paths retain their existing unavailable response.
"""

from django.http import HttpResponse
from django.test import SimpleTestCase


class DisplayPublicationsTests(SimpleTestCase):
    def test_publication_entry_remains_unavailable(self) -> None:
        """
        Checks HTML and JSON query variants retain the same status, media type, and message.
        """
        for query in ('', '?format=json'):
            response = self.client.get('/display/example/publications/' + query)
            assert isinstance(response, HttpResponse)
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response['Content-Type'], 'text/plain')
            self.assertEqual(response.content, b'This endpoint is not connected to source data yet.')
