"""Regression tests for static home-derived pages."""

from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import get_script_prefix, reverse, set_script_prefix


class StaticPageTests(TestCase):
    """Ensure key static pages render expected content and shared search box."""

    def test_static_pages_render_with_shared_search_box(self) -> None:
        pages = [
            (reverse('about'), 'About Researchers@Brown'),
            (reverse('help'), 'Researchers@Brown Help'),
            (reverse('faq'), 'Frequently Asked Questions'),
            (reverse('history'), 'VIVO History and Implementation'),
            (reverse('publications'), 'Managing Your Publications'),
            (reverse('roadmap'), 'Improvements and Roadmap'),
            (reverse('terms'), 'Terms of Use'),
            (reverse('help_viz'), 'Visualize it!'),
            (reverse('brown'), 'Brown University'),
        ]
        for url, heading in pages:
            with self.subTest(url=url):
                response = self.client.get(url)
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, heading)
                self.assertContains(response, 'id="sticky-nav"')

    def test_information_pages_keep_public_paths_and_slash_aliases(self) -> None:
        """
        Checks public information paths render directly and older slash links still work.
        """
        for name in ('about', 'help', 'faq', 'history', 'publications', 'roadmap', 'terms', 'help_viz'):
            url = reverse(name)
            route = {'terms': 'termsOfUse', 'help_viz': 'help/viz'}.get(name, name)
            self.assertEqual(url, '/' + route)
            for path in (url, url + '/'):
                with self.subTest(path=path):
                    response = self.client.get(path)
                    assert isinstance(response, HttpResponse)
                    self.assertEqual(response.status_code, 200)
                    self.assertTemplateUsed(response, 'home/' + name + '.html')
                    self.assertContains(response, '/css/public.css?v=')

    def test_information_page_links_keep_the_application_prefix(self) -> None:
        """
        Checks information-page links remain within a mounted application.
        """
        previous = get_script_prefix()
        set_script_prefix('/mounted-app/')
        try:
            response = self.client.get('/about', SCRIPT_NAME='/mounted-app')
            assert isinstance(response, HttpResponse)
            self.assertContains(response, 'href="/mounted-app/faq#who"')
            self.assertContains(response, 'href="/mounted-app/help"')
            response = self.client.get('/roadmap', SCRIPT_NAME='/mounted-app')
            assert isinstance(response, HttpResponse)
            self.assertContains(response, 'href="/mounted-app/help/viz"')
        finally:
            set_script_prefix(previous)

    @override_settings(
        SOLR_URL='https://source.invalid/solr',
        UPSTREAM_RECORDING_MANIFEST='unused-recordings.json',
        TURNSTILE_ENABLED=False,
    )
    def test_information_pages_render_in_source_modes(self) -> None:
        """
        Checks static information renders without source requests while unconverted pages stay unavailable.
        """
        for mode in ('live', 'replay', 'prepared'):
            with self.subTest(mode=mode), override_settings(PAGE_DATA_MODE=mode):
                for name, heading in (
                    ('about', 'About Researchers@Brown'),
                    ('help', 'Researchers@Brown Help'),
                    ('faq', 'Frequently Asked Questions'),
                    ('history', 'VIVO History and Implementation'),
                    ('publications', 'Managing Your Publications'),
                    ('roadmap', 'Improvements and Roadmap'),
                    ('terms', 'Terms of Use'),
                    ('help_viz', 'Visualize it!'),
                ):
                    route = {'terms': 'termsOfUse', 'help_viz': 'help/viz'}.get(name, name)
                    for path in ('/' + route, '/' + route + '/'):
                        response = self.client.get(path)
                        assert isinstance(response, HttpResponse)
                        self.assertEqual(response.status_code, 200)
                        self.assertTemplateUsed(response, 'home/' + name + '.html')
                        self.assertContains(response, heading)
                        self.assertContains(response, '/css/public.css?v=')
                response = self.client.get('/brown/')
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, 503)

    def test_brown_classic_redirects_to_search(self) -> None:
        response = self.client.get(reverse('brown_classic'), {'name': 'Jane_Doe'})
        assert isinstance(response, HttpResponse)
        expected_location: str = f'{reverse("search")}?q=Jane+Doe'
        self.assertRedirects(response, expected_location, fetch_redirect_response=False)

    def test_brown_classic_named_path_redirects(self) -> None:
        response = self.client.get(reverse('brown_classic_named', args=['John_Doe']))
        assert isinstance(response, HttpResponse)
        expected_location: str = f'{reverse("search")}?q=John+Doe'
        self.assertRedirects(response, expected_location, fetch_redirect_response=False)
