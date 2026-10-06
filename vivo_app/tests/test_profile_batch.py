"""
Checks source citation variations and person-profile navigation without live services.
"""

from django.http import HttpRequest
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import get_script_prefix, set_script_prefix

from vivo_app.lib.profile_navigation import profile_search_return
from vivo_app.lib.recorded_responses import RecordedResponse, RequestKey
from vivo_app.lib.source_html import render_citation_html
from vivo_app.lib.source_pages import profile_panels, profile_sections, publication_html


def unused_source(key: RequestKey, mode: str) -> RecordedResponse:
    """
    Fails if a text-only profile comparison unexpectedly requests a source.

    Called by: ProfileBatchTests.test_institution_links_describe_their_searches(), test_empty_profile_panels_do_not_add_navigation_buttons()
    """
    raise AssertionError('A text-only profile should not request source data.')


def invented_profile(hidden: bool = False) -> dict[str, object]:
    """
    Supplies made-up profile content for initial rendering and browser checks.

    Called by: ProfileBatchTests.test_initial_profile_visibility_and_inactive_name(), private browser checks
    """
    return {
        'id': 'invented-profile',
        'name': 'Invented Researcher',
        'title': 'Example Professor',
        'thumbnail': '',
        'hidden': hidden,
        'sections': [
            {'id': 'Overview', 'label': 'Overview', 'html': '<h3>Overview</h3><p>Example overview.</p>'},
            {'id': 'Research', 'label': 'Research', 'html': '<h3>Research</h3><p>Example research.</p>'},
            {'id': 'Background', 'label': 'Background', 'html': '<h3>Background</h3><p>Example background.</p>'},
        ],
    }


@override_settings(ALLOWED_HOSTS=['testserver'])
class ProfileBatchTests(SimpleTestCase):
    """Checks citation formatting and the current request's profile navigation."""

    def test_citation_separators_match_public_source_rules(self) -> None:
        """
        Checks citation details already ending in punctuation do not gain repeated separators.
        """
        cases: list[tuple[dict[str, object], str]] = [
            ({'title': 'Example', 'pages': '10-20.'}, '"Example." pp. 10-20.'),
            (
                {
                    'type': 'http://vivo.brown.edu/ontology/citation#BookSection',
                    'title': 'Chapter',
                    'book': 'Collection',
                    'pages': '10-20.',
                },
                '"Chapter." <i>Collection</i>, pp. 10-20.',
            ),
            ({'title': 'Example', 'volume': '4,', 'issue': '2'}, '"Example." vol. 4, no. 2.'),
            ({'title': 'Example', 'issue': '2,', 'date': '2020'}, '"Example." no. 2, 2020.'),
            (
                {
                    'type': 'http://vivo.brown.edu/ontology/citation#BookSection',
                    'title': 'Chapter',
                    'editors': 'A. Editor,',
                    'publisher_label': 'Example Press',
                },
                '"Chapter.", edited by A. Editor, Example Press.',
            ),
            (
                {
                    'type': 'http://vivo.brown.edu/ontology/citation#Book',
                    'title': 'Example Book',
                    'publisher_label': 'Example Press,',
                    'date': '2020',
                },
                '<i>Example Book</i>. Example Press, 2020.',
            ),
            (
                {
                    'type': 'http://vivo.brown.edu/ontology/citation#Book',
                    'title': 'Example Book',
                    'location_label': 'Example City,',
                    'publisher_label': 'Example Press',
                },
                '<i>Example Book</i>. Example City, Example Press.',
            ),
        ]
        for record, expected in cases:
            with self.subTest(record=record):
                self.assertEqual(publication_html(record), expected + ' <div class="no-orphans"></div>')

    def test_source_title_and_author_punctuation_is_preserved(self) -> None:
        """
        Checks nested quotes, author ellipses, title periods, and book quotes remain visible.
        """
        cases: list[tuple[dict[str, object], str]] = [
            (
                {
                    'type': 'http://vivo.brown.edu/ontology/citation#BookSection',
                    'title': '““Nested title””',
                    'book': 'Collection',
                },
                '"“Nested title””." <i>Collection</i>.',
            ),
            ({'authors': 'A. Writer...', 'title': 'Example'}, '<span class="listDateTime">A. Writer... </span>"Example.".'),
            ({'title': 'Example...'}, '"Example...".'),
            ({'title': '“Example”'}, '"Example”.".'),
            (
                {'type': 'http://vivo.brown.edu/ontology/citation#Book', 'title': '"Quoted book"'},
                '<i>"Quoted book"</i>.',
            ),
        ]
        for record, expected in cases:
            with self.subTest(record=record):
                self.assertEqual(publication_html(record), expected + ' <div class="no-orphans"></div>')

    def test_scientific_title_formatting_and_entities_render_as_text(self) -> None:
        """
        Checks italic terms, chemical subscripts, exponents, and encoded characters render once.
        """
        cases = [
            ('An <i>invented species</i>', 'An <i>invented species</i>'),
            ('H<sub>2</sub>O', 'H<sub>2</sub>O'),
            ('x<sup>2</sup>', 'x<sup>2</sup>'),
            ('A &amp; B', 'A &amp; B'),
            ('Writer&#39;s work', 'Writer&#x27;s work'),
        ]
        for title, expected in cases:
            with self.subTest(title=title):
                markup = publication_html({'title': title})
                self.assertIn(expected, markup)
        self.assertEqual(render_citation_html('<div>A <i>term</i></div>'), 'A <i>term</i>')
        self.assertEqual(render_citation_html('<a href="https://example.invalid">Title</a>'), 'Title')

    def test_numeric_metadata_and_blank_journal_fallback(self) -> None:
        """
        Checks numeric volume, issue, and page data stays visible and a blank journal uses the venue.
        """
        cases: list[tuple[dict[str, object], str]] = [
            ({'volume': 4}, 'vol. 4.'),
            ({'issue': 2}, 'no. 2.'),
            ({'pages': 15}, 'pp. 15.'),
            ({'published_in': '  ', 'venue': 'Example Journal'}, '<i>Example Journal</i>.'),
            ({'published_in': 'Example Journal ', 'date': '2020'}, '<i>Example Journal </i>, 2020.'),
        ]
        for record, expected in cases:
            with self.subTest(record=record):
                self.assertEqual(publication_html(record), expected + ' <div class="no-orphans"></div>')
        self.assertEqual(publication_html({'volume': True, 'issue': {}, 'pages': []}), '. <div class="no-orphans"></div>')

    def test_padded_citation_links_reach_the_intended_destination(self) -> None:
        """
        Checks surrounding source whitespace is absent from DOI, PubMed, and website links.
        """
        cases = [
            ('doi', ' 10.0000/example ', 'https://doi.org/10.0000/example'),
            ('pub_med_id', ' PMC12345 ', 'http://www.ncbi.nlm.nih.gov/pubmed/?term=PMC12345'),
            ('url', ' https://example.invalid/item ', 'https://example.invalid/item'),
        ]
        for field, value, expected in cases:
            with self.subTest(field=field):
                self.assertIn('href="' + expected + '"', publication_html({field: value}))

    def test_chapter_collection_spacing_and_inline_text_is_preserved(self) -> None:
        """
        Checks chapter collection spacing matches the source and empty collections stay absent.
        """
        cases = [
            ('Collection ', '"Chapter." <i>Collection </i>, 2020.'),
            (' Collection ', '"Chapter." <i> Collection </i>, 2020.'),
            ('A &amp; <b>Collection</b> ', '"Chapter." <i>A &amp; <b>Collection</b> </i>, 2020.'),
            ('   ', '"Chapter.", 2020.'),
        ]
        for book, expected in cases:
            with self.subTest(book=book):
                self.assertEqual(
                    publication_html(
                        {
                            'type': 'http://vivo.brown.edu/ontology/citation#BookSection',
                            'title': 'Chapter',
                            'book': book,
                            'date': '2020',
                        }
                    ),
                    expected + ' <div class="no-orphans"></div>',
                )

    def test_empty_profile_panels_do_not_add_navigation_buttons(self) -> None:
        """
        Checks sparse profiles keep empty panels, conditional buttons, and the original panel order.
        """
        cases: list[dict[str, object]] = [{}, {'research_overview': 'Example research.'}]
        for content in cases:
            with self.subTest(content=content):
                sections = profile_sections(content, 'live', unused_source, 0, '')
                panels = profile_panels(sections)
                profile = {'sections': sections, 'panels': panels}
                html = render_to_string('display/profile_data.html', {'profile': profile})
                for name in ('Background', 'Affiliations', 'Teaching'):
                    self.assertIn('id="tab' + name + '"', html)
                    self.assertNotIn('id="tab' + name + 'Btn"', html)
                self.assertNotIn('id="tabPublications"', html)
                self.assertEqual('id="tabAllBtn"' in html, bool(content))
                self.assertEqual(
                    [panel['id'] for panel in panels],
                    ['Overview'] + (['Research'] if content else []) + ['Background', 'Affiliations', 'Teaching'],
                )
        populated = invented_profile()['sections']
        assert isinstance(populated, list)
        panels = profile_panels(populated)
        self.assertEqual(panels[:3], populated)

    def test_direct_profile_does_not_reuse_a_stale_search(self) -> None:
        """
        Checks direct and unrelated-referrer visits return to the default search.
        """
        factory = RequestFactory()
        for referer in [
            '',
            'http://testserver/about',
            'https://example.invalid/search?q=Old',
            'http://testserver/searching?q=Old',
            'http://testserver/search?q=Old\n',
        ]:
            with self.subTest(referer=referer):
                request = factory.get('/display/invented-profile', HTTP_REFERER=referer)
                self.assertEqual(profile_search_return(request), '/search')

    def test_profile_revisits_the_actual_search_history_entry(self) -> None:
        """
        Checks actual search entries use browser history, retaining filters, pagination and Forward navigation.
        """
        factory = RequestFactory()
        query = '?q=Example&fq=record_type%7CPEOPLE&fq=affiliations%7CExample&page=2'
        request = factory.get('/display/invented-profile', HTTP_REFERER='http://testserver/search/' + query)
        self.assertEqual(profile_search_return(request), 'javascript: history.go(-1)')
        prefix = get_script_prefix()
        set_script_prefix('/mounted-app')
        try:
            mounted: HttpRequest = factory.get(
                '/display/invented-profile',
                HTTP_REFERER='http://testserver/mounted-app/search' + query,
                SCRIPT_NAME='/mounted-app',
            )
            self.assertEqual(profile_search_return(mounted), 'javascript: history.go(-1)')
        finally:
            set_script_prefix(prefix)

    def test_institution_links_describe_their_searches(self) -> None:
        """
        Checks education and appointment institutions describe the linked search action.
        """
        sections = profile_sections(
            {
                'education': [{'date': '2020', 'school_name': 'Example School'}],
                'appointments': [{'name': 'Example Role', 'org_name': 'Example Institution'}],
            },
            'live',
            unused_source,
            0,
            '',
        )
        html = ''.join(section['html'] for section in sections)
        self.assertIn('title="Find researchers that also graduated from this institution"', html)
        self.assertIn('title="Find other researchers at Brown with a relationship to this institution"', html)

    def test_initial_profile_visibility_and_inactive_name(self) -> None:
        """
        Checks both name layouts show inactive status and only Overview starts visible.
        """
        html = render_to_string(
            'display/profile_data.html', {'profile': invented_profile(True), 'back_to_search': '/search'}
        )
        self.assertEqual(html.count('Invented Researcher [Inactive]'), 2)
        self.assertIn('id="tabResearch" class="tabFinder panel panel-default" style="display:none" aria-hidden="true"', html)
        self.assertIn('aria-controls="tabOverview" aria-current="true"', html)
        self.assertNotIn('id="tabOverview" class="tabFinder" style="display:none"', html)
