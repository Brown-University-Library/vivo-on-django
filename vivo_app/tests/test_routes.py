"""
Checks retained public redirects, unavailable routes, and export validation.
"""

from django.http import HttpResponse
from django.test import SimpleTestCase


class RoutesTests(SimpleTestCase):
    def test_public_entry_redirects(self) -> None:
        """
        Checks public entry URLs retain their status and destination.
        """
        for path, status, location in (
            ('/display/', 302, '/search'),
            ('/reports/subject-lib/', 302, '/'),
            ('/people/', 302, 'http://testserver/search?fq=record_type|PEOPLE'),
            ('/ous/', 302, 'http://testserver/search?fq=record_type|ORGANIZATION'),
            ('/individual/example/', 303, 'http://testserver/display/example'),
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, status)
                self.assertEqual(response['Location'], location)

    def test_unsupported_handlers_remain_unavailable(self) -> None:
        """
        Checks previously rejected handlers cannot expose sample pages after cleanup.
        """
        for path in ('/display/example/viz/', '/reports/subject-lib/example/', '/side_stuff/brown_classic/'):
            response = self.client.get(path)
            assert isinstance(response, HttpResponse)
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.content, b'This endpoint is not connected to source data yet.')

    def test_unsupported_exports_keep_their_error(self) -> None:
        """
        Checks unconfirmed export forms keep their error instead of returning made-up records.
        """
        for path in ('/individual/example.json/', '/individual/example/example.json/'):
            response = self.client.get(path)
            assert isinstance(response, HttpResponse)
            self.assertEqual(response.status_code, 503)

    def test_file_old_image_returns_404(self) -> None:
        """
        Checks an unsupported old image path remains absent.
        """
        response = self.client.get('/file/1/foo.png/')
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 404)
