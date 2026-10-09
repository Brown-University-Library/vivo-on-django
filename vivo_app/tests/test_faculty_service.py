"""Checks redirects to the existing faculty data service with made-up identifiers."""

from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings
from django.urls import get_script_prefix, set_script_prefix


@override_settings(
    SOLR_URL='https://source.invalid/solr',
    UPSTREAM_RECORDING_MANIFEST='unused-recordings.json',
    TURNSTILE_ENABLED=False,
)
class FacultyServiceTests(SimpleTestCase):
    def test_both_route_forms_reach_service_outside_mount(self) -> None:
        """
        Checks both path forms permanently redirect outside the Django mount in every data mode.
        """
        previous_prefix = get_script_prefix()
        set_script_prefix('/mounted-app/')
        try:
            for mode in ('prototype', 'prepared', 'replay', 'live'):
                with self.subTest(mode=mode), override_settings(PAGE_DATA_MODE=mode):
                    for suffix in ('', '/'):
                        response = self.client.get(
                            '/services/data/v1/faculty/invented-a' + suffix,
                            SCRIPT_NAME='/mounted-app',
                        )
                        assert isinstance(response, HttpResponse)
                        self.assertEqual(response.status_code, 301)
                        self.assertEqual(response['Location'], 'http://testserver/services/data/v1/faculty/invented-a/')
                        self.assertEqual(response['Access-Control-Allow-Origin'], '*')
        finally:
            set_script_prefix(previous_prefix)

    def test_query_values_and_https_are_preserved(self) -> None:
        """
        Checks repeated values and their encoding reach the HTTPS service unchanged.
        """
        response = self.client.get(
            '/services/data/v1/faculty/invented-a?format=json&x=a%20b&x=c%2Fd',
            secure=True,
            SCRIPT_NAME='/mounted-app',
        )
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(
            response['Location'],
            'https://testserver/services/data/v1/faculty/invented-a/?format=json&x=a%20b&x=c%2Fd',
        )

    def test_identifier_stays_in_path(self) -> None:
        """
        Checks an encoded question mark stays in the identifier rather than becoming a query.
        """
        response = self.client.get('/services/data/v1/faculty/invented%3Fa')
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'http://testserver/services/data/v1/faculty/invented%3Fa/')

    def test_head_redirects_and_post_is_not_allowed(self) -> None:
        """
        Checks HEAD follows the same redirect and POST cannot submit data through this route.
        """
        response = self.client.head('/services/data/v1/faculty/invented-a')
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.content, b'')
        self.assertEqual(response['Location'], 'http://testserver/services/data/v1/faculty/invented-a/')
        rejected = self.client.post('/services/data/v1/faculty/invented-a')
        assert isinstance(rejected, HttpResponse)
        self.assertEqual(rejected.status_code, 405)
        self.assertNotIn('Location', rejected)
