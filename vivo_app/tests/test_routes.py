import json

from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse


class RoutesTests(TestCase):
    def test_home_and_static(self) -> None:
        standard_paths = [
            '/',
            '/about/',
            '/faq/',
            '/help/',
            '/help/viz/',
            '/history/',
            '/publications/',
            '/roadmap/',
            '/termsOfUse/',
            '/status/',
            '/brown/',
        ]
        for path in standard_paths:
            with self.subTest(path=path):
                resp = self.client.get(path)
                assert isinstance(resp, HttpResponse)
                self.assertEqual(resp.status_code, 200)

        for path in [
            '/side_stuff/brown_classic/',
            '/side_stuff/brown_classic/joe/',
        ]:
            with self.subTest(path=path):
                resp = self.client.get(path)
                assert isinstance(resp, HttpResponse)
                self.assertEqual(resp.status_code, 302)
                self.assertTrue(resp.headers.get('Location', '').startswith(reverse('search')))

    def test_display_and_visualizations(self) -> None:
        base_id = 'n1'
        paths = [
            '/display/',
            f'/display/{base_id}/',
            f'/display/{base_id}/publications/',
            f'/display/{base_id}/viz/',
            f'/display/{base_id}/viz/coauthor/',
            f'/display/{base_id}/viz/coauthor_treemap/',
            f'/display/{base_id}/viz/collab/',
            f'/display/{base_id}/viz/publications/',
            f'/display/{base_id}/viz/research/',
        ]
        for path in paths:
            with self.subTest(path=path):
                resp = self.client.get(path)
                assert isinstance(resp, HttpResponse)
                self.assertEqual(resp.status_code, 200)

    def test_display_json_format_param(self) -> None:
        resp = self.client.get('/display/abc/?format=json')
        assert isinstance(resp, HttpResponse)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get('Content-Type'), 'application/json')
        self.assertEqual(json.loads(resp.content), {'id': 'abc'})

    def test_reports(self) -> None:
        for path in ['/reports/subject-lib/', '/reports/subject-lib/abc/']:
            resp = self.client.get(path)
            assert isinstance(resp, HttpResponse)
            self.assertEqual(resp.status_code, 200)

    def test_search(self) -> None:
        for path in ['/search/', '/search/advanced/']:
            resp = self.client.get(path)
            assert isinstance(resp, HttpResponse)
            self.assertEqual(resp.status_code, 200)
        ## facets returns JSON
        resp = self.client.get('/search_facets/')
        assert isinstance(resp, HttpResponse)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get('Content-Type'), 'application/json')
        self.assertIn('facets', json.loads(resp.content))

    def test_legacy_people_organizations(self) -> None:
        for path in ['/people/', '/ous/']:
            resp = self.client.get(path)
            assert isinstance(resp, HttpResponse)
            self.assertEqual(resp.status_code, 200)

    def test_file_old_image_returns_404(self) -> None:
        resp = self.client.get('/file/1/foo.png/')
        assert isinstance(resp, HttpResponse)
        self.assertEqual(resp.status_code, 404)

    def test_individual_redirect(self) -> None:
        resp = self.client.get('/individual/n123/')
        assert isinstance(resp, HttpResponse)
        self.assertEqual(resp.status_code, 200)

    def test_individual_export_json_single(self) -> None:
        resp = self.client.get('/individual/n123.json/')
        assert isinstance(resp, HttpResponse)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get('Content-Type'), 'application/json')
        data = json.loads(resp.content)
        assert isinstance(data, dict)
        self.assertEqual(data.get('id'), 'n123')
        self.assertEqual(data.get('format'), 'json')

    def test_individual_export_json_double(self) -> None:
        resp = self.client.get('/individual/n123/n123.json/')
        assert isinstance(resp, HttpResponse)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get('Content-Type'), 'application/json')
        data = json.loads(resp.content)
        assert isinstance(data, dict)
        self.assertEqual(data.get('id'), 'n123')
        self.assertEqual(data.get('id2'), 'n123')
        self.assertEqual(data.get('format'), 'json')
