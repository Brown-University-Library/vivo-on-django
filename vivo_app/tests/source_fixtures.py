"""
Supplies made-up source responses for application rendering tests.
"""

import json

from vivo_app.lib.source_graph import visualization_key
from vivo_app.lib.source_requests import (
    document_key,
    image_key,
    member_details_key,
    member_key,
    profile_key,
    search_key,
    team_member_key,
)
from vivo_app.lib.source_types import RequestKey, SourceResponse


def solr_response(
    docs: list[dict[str, object]],
    count: int,
    facets: dict[str, object] | None = None,
    highlights: dict[str, object] | None = None,
) -> SourceResponse:
    """
    Makes a complete Solr response from invented documents.

    Called by: page_responses(), application tests
    """
    data: dict[str, object] = {'responseHeader': {'status': 0}, 'response': {'numFound': count, 'docs': docs}}
    if facets is not None:
        data['facet_counts'] = facets
    if highlights is not None:
        data['highlighting'] = highlights
    return SourceResponse(200, (('content-type', 'application/json'),), json.dumps(data).encode())


def page_responses() -> dict[RequestKey, SourceResponse]:
    """
    Creates response bytes for one invented search-to-profile journey.

    Called by: application rendering tests
    """
    person = {
        'id': 'http://vivo.brown.edu/individual/invented-a',
        'name': 'Invented Researcher',
        'title': 'Example Professor',
        'email': 'invented@example.invalid',
        'overview': '<p>Invented &amp; tested. <a href="https://example.invalid/lab">Example lab</a></p>',
        'affiliations': [{'uri': 'http://vivo.brown.edu/individual/org-example', 'name': 'Example Department'}],
        'research_areas': ['liver', 'Excretion', 'absorption'],
        'on_the_web': [{'url': 'https://example.invalid/person', 'text': 'Website'}],
        'contributor_to': [
            {
                'type': 'http://vivo.brown.edu/ontology/citation#Article',
                'title': 'Example publication',
                'authors': 'Researcher, Invented',
                'date': '2024-01-01',
                'published_in': 'Invented Journal',
                'doi': '10.0000/example',
                'pub_med_id': '12345678',
            }
        ],
        'education': [{'date': '2001', 'degree': 'PhD', 'school_name': 'Example University'}],
        'awards': '<ul><li>Example <a href="https://example.invalid/award">Award</a></li></ul>',
        'appointments': [{'name': 'Editor', 'org_name': 'Example Journal', 'start_date': '2020-01-01'}],
        'teacher_for': ['EXMP 1000 - Example Course'],
        'cv': [{'cv_link': 'http://example.invalid/docs/i/invented_cv.pdf?dt=1'}],
    }
    person_doc = {
        'id': person['id'],
        'record_type': ['PEOPLE'],
        'json_txt': [json.dumps(person)],
        'display_name_s': 'Invented Researcher',
        'show_visualizations_s': 'true',
        'thumbnail_file_path_s': '/file/n1234/portrait.jpg',
    }
    organization_doc = {
        'id': 'http://vivo.brown.edu/individual/org-example',
        'record_type': ['ORGANIZATION'],
        'thumbnail_file_path_s': '/file/n5678/logo.png',
        'json_txt': [
            json.dumps(
                {
                    'name': 'Example Department',
                    'overview': '<p><strong>Invented department</strong></p><script>unsafe()</script>',
                    'people': [
                        {
                            'faculty_uri': person['id'],
                            'label': 'Researcher, Invented',
                            'specific_position': 'Example Professor',
                            'general_position': 'http://vivoweb.org/ontology/core#FacultyPosition',
                        }
                    ],
                    'web_pages': [{'url': 'https://example.invalid/department', 'text': 'Department website'}],
                }
            )
        ],
    }
    facets: dict[str, object] = {
        'facet_fields': {
            'record_type': ['PEOPLE', 1],
            'affiliations': ['Example Department', 1],
            'research_areas': [],
            'published_in': ['Invented Journal', 1],
        }
    }
    highlights: dict[str, object] = {
        'vitroIndividual:http://vivo.brown.edu/individual/invented-a': {
            'short_id_s': ['<strong>Example</strong> <script>unsafe</script>']
        }
    }
    return {
        search_key('Example', 1, []): solr_response([person_doc], 1, facets, highlights),
        search_key('Example', 1, [('record_type', 'PEOPLE')]): solr_response([person_doc], 1, facets, highlights),
        search_key('Example', 1, [], -1): solr_response([person_doc], 1, facets, highlights),
        search_key('Example', 1, [('record_type', 'PEOPLE')], -1): solr_response([person_doc], 1, facets, highlights),
        search_key('none', 1, []): solr_response(
            [],
            0,
            {'facet_fields': {field: [] for field in ('record_type', 'affiliations', 'research_areas', 'published_in')}},
        ),
        search_key('none', 1, [], -1): solr_response(
            [],
            0,
            {'facet_fields': {field: [] for field in ('record_type', 'affiliations', 'research_areas', 'published_in')}},
        ),
        search_key('Example', 2, []): solr_response([person_doc], 21, facets),
        search_key('Example', 1, [('record_type', 'PEOPLE'), ('affiliations', 'Example Department')]): solr_response(
            [person_doc], 1, facets
        ),
        profile_key('invented-a'): solr_response([person_doc], 1),
        visualization_key('coauthors'): SourceResponse(
            200, (('content-type', 'application/json'),), json.dumps({person['id']: True}).encode()
        ),
        profile_key('org-example'): solr_response([organization_doc], 1),
        member_key(['invented-a']): solr_response([person_doc], 1),
        member_details_key(['invented-a']): solr_response([person_doc], 1),
        team_member_key(['invented-a']): solr_response([person_doc], 1),
        image_key('/profile-images/123/4/portrait.jpg'): SourceResponse(
            200, (('content-type', 'image/jpeg'),), b'invented-portrait'
        ),
        image_key('/profile-images/567/8/logo.png'): SourceResponse(200, (('content-type', 'image/png'),), b'invented-logo'),
        document_key('/docs/i/invented_cv.pdf', (('dt', '1'),)): SourceResponse(
            200, (('content-type', 'application/pdf'),), b'%PDF-1.7 invented document'
        ),
        document_key('/docs/i/invented_cv.pdf'): SourceResponse(
            301, (('content-type', 'text/html'), ('location', 'https://example.invalid/docs/i/invented_cv.pdf?dt=1')), b''
        ),
    }
