"""
Checks organization charts with made-up Solr responses and no network access.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase, override_settings

from vivo_app.lib.page_errors import PageDataError
from vivo_app.lib.source_org_charts import publication_history_csv, publication_history_data, research_areas_data
from vivo_app.lib.source_requests import chart_member_key, profile_key
from vivo_app.lib.source_types import RequestKey, SourceResponse


class OrganizationChartTests(TestCase):
    """Checks the chart data, routes, and matching source requests."""

    def setUp(self) -> None:
        """
        Creates a small organization and three made-up researchers.
        """
        prefix = 'http://vivo.brown.edu/individual/'
        organization: dict[str, object] = {
            'id': prefix + 'org-example',
            'record_type': 'ORGANIZATION',
            'json_txt': json.dumps(
                {
                    'name': 'Example Organization',
                    'people': [
                        {'faculty_uri': prefix + person_id} for person_id in ('invented-a', 'invented-b', 'invented-c')
                    ],
                }
            ),
        }
        people = [
            (
                'invented-a',
                {
                    'name': 'Invented A',
                    'title': 'Professor',
                    'research_areas': ['Area A', 'Area B'],
                    'contributor_to': [{'date': '2020-01-01'}, {'date': '2020-04-01'}, {'date': '2021-01-01'}],
                },
            ),
            (
                'invented-b',
                {
                    'name': 'Invented B',
                    'title': 'Lecturer',
                    'research_areas': ['Area A'],
                    'contributor_to': [{'date': '1899-01-01'}, {'date': '2020-01-01'}, {'date': '2999-01-01'}],
                },
            ),
            (
                'invented-c',
                {
                    'name': 'Invented C',
                    'title': 'Researcher',
                    'research_areas': ['Area C'],
                    'contributor_to': [{'date': '2999-01-01'}],
                },
            ),
        ]
        member_docs: list[dict[str, object]] = [
            {'id': prefix + identifier, 'record_type': 'PEOPLE', 'json_txt': json.dumps(person)}
            for identifier, person in people
        ]
        self.responses = {
            profile_key('org-example'): self.response([organization]),
            chart_member_key(['invented-a', 'invented-b', 'invented-c']): self.response(member_docs),
        }
        self.requested: list[RequestKey] = []

    def response(self, docs: list[dict[str, object]]) -> SourceResponse:
        """
        Wraps made-up records in the expected Solr response.

        Called by: setUp()
        """
        body = {'responseHeader': {'status': 0}, 'response': {'numFound': len(docs), 'docs': docs}}
        return SourceResponse(200, (('content-type', 'application/json'),), json.dumps(body).encode())

    def read(
        self,
        key: RequestKey,
    ) -> SourceResponse:
        """
        Reads only the exact made-up request keys.

        Called by: test_chart_data_and_repeated_reads(), test_chart_routes(), test_missing_source_response_fails()
        """
        self.requested.append(key)
        if key not in self.responses:
            raise PageDataError('The requested source response is missing.')
        return self.responses[key]

    def test_chart_data_and_repeated_reads(self) -> None:
        """
        Checks public chart shapes and repeatable source request keys.
        """
        name, publications = publication_history_data('org-example', self.read)
        first_keys = list(self.requested)
        self.requested.clear()
        _, repeated = publication_history_data('org-example', self.read)
        self.assertEqual(name, 'Example Organization')
        self.assertEqual(publications, repeated)
        self.assertEqual(first_keys, list(self.requested))
        self.assertEqual(publications['years'], ['2020', '2021'])
        self.assertEqual(publications['columns'], ['invented-a', 'invented-b'])
        matrix = publications['matrix']
        assert isinstance(matrix, list)
        self.assertEqual([row['total'] for row in matrix if isinstance(row, dict)], [3, 1])
        self.assertEqual(
            publication_history_csv(publications), 'year,year_total,invented-a,invented-b\n2020,3,2,1\n2021,1,1,0'
        )
        _, research = research_areas_data('org-example', self.read)
        nodes = research['nodes']
        links = research['links']
        assert isinstance(nodes, list) and isinstance(nodes[1], list)
        assert isinstance(links, list)
        self.assertEqual([node['nodeName'] for node in nodes[1] if isinstance(node, dict)], ['Area A'])
        self.assertEqual(len(links), 2)

    def test_large_organization_keeps_every_member_in_small_source_requests(self) -> None:
        """
        Checks an organization above five hundred members produces complete charts using twenty-member requests.
        """
        prefix = 'http://vivo.brown.edu/individual/'
        identifiers = [f'invented-{index:04}' for index in range(793)]
        self.responses[profile_key('org-example')] = self.response(
            [
                {
                    'id': prefix + 'org-example',
                    'record_type': 'ORGANIZATION',
                    'json_txt': json.dumps(
                        {
                            'name': 'Example Organization',
                            'people': [{'faculty_uri': prefix + identifier} for identifier in identifiers],
                        }
                    ),
                }
            ]
        )
        batches = [identifiers[start : start + 20] for start in range(0, len(identifiers), 20)]
        for batch in batches:
            self.responses[chart_member_key(batch)] = self.response(
                [
                    {
                        'id': prefix + identifier,
                        'record_type': 'PEOPLE',
                        'json_txt': json.dumps(
                            {
                                'name': identifier,
                                'contributor_to': [{'date': '2020-01-01'}],
                                'research_areas': ['Shared area'],
                            }
                        ),
                    }
                    for identifier in batch
                ]
            )
        with patch('vivo_app.lib.source_org_charts.time.sleep'):
            _, publications = publication_history_data('org-example', self.read)
            _, research = research_areas_data('org-example', self.read)
        self.assertEqual(publications['columns'], identifiers)
        self.assertEqual(publications['matrix'], [{'year': 2020, 'total': 793, **dict.fromkeys(identifiers, 1)}])
        groups = research['nodes']
        links = research['links']
        assert isinstance(groups, list)
        assert isinstance(links, list)
        self.assertEqual([node['nodeName'] for node in groups[0]], identifiers)
        self.assertEqual(len(links), 793)
        self.assertEqual(
            self.requested,
            [profile_key('org-example'), *(chart_member_key(batch) for batch in batches)] * 2,
        )

    def test_missing_organization_returns_404_for_all_chart_formats(self) -> None:
        """
        Checks an exact empty organization lookup returns not found without administrator error email.
        """
        self.responses[profile_key('org-example')] = self.response([])
        with (
            patch('vivo_app.lib.source_org_charts.read_source', side_effect=self.read),
            patch('django.utils.log.AdminEmailHandler.emit') as email,
        ):
            for suffix in ('publications', 'publications.json', 'publications.csv', 'research', 'research.json'):
                with self.subTest(suffix=suffix):
                    response = self.client.get('/display/org-example/viz/' + suffix)
                    assert isinstance(response, HttpResponse)
                    self.assertEqual(response.status_code, 404)
            email.assert_not_called()

    def test_inconsistent_or_unrelated_organization_lookup_remains_an_error(self) -> None:
        """
        Checks wrong IDs, unsupported record types, and inconsistent result counts are not treated as missing.
        """
        original = json.loads(self.responses[profile_key('org-example')].body)
        for changes in (
            {'id': 'http://vivo.brown.edu/individual/org-other'},
            {'record_type': 'PEOPLE'},
            {'record_type': 'UNCATEGORIZED'},
            {'json_txt': 'invalid'},
        ):
            doc = {**original['response']['docs'][0], **changes}
            self.responses[profile_key('org-example')] = self.response([doc])
            with self.subTest(changes=changes), self.assertRaises(PageDataError):
                research_areas_data('org-example', self.read)
        original['response']['docs'] = []
        self.responses[profile_key('org-example')] = SourceResponse(200, (), json.dumps(original).encode())
        with self.assertRaises(PageDataError):
            research_areas_data('org-example', self.read)

    def test_publication_csv_follows_its_header_column_order(self) -> None:
        """
        Checks CSV rows follow the named columns even when source keys are reordered.
        """
        chart = {
            'columns': ['invented-a', 'invented-b'],
            'matrix': [{'invented-b': 2, 'total': 3, 'year': 2020, 'invented-a': 1}],
        }
        self.assertEqual(publication_history_csv(chart), 'year,year_total,invented-a,invented-b\n2020,3,1,2')

    def test_research_chart_omits_blank_area_names(self) -> None:
        """
        Checks two empty research-area values cannot become a shared chart node.
        """
        key = chart_member_key(['invented-a', 'invented-b', 'invented-c'])
        source = json.loads(self.responses[key].body)
        for doc in source['response']['docs'][:2]:
            person = json.loads(doc['json_txt'])
            person['research_areas'].append('')
            doc['json_txt'] = json.dumps(person)
        self.responses[key] = self.response(source['response']['docs'])
        _, result = research_areas_data('org-example', self.read)
        groups = result['nodes']
        if not isinstance(groups, list) or not isinstance(groups[1], list):
            self.fail('Research chart nodes should contain an area list.')
        self.assertEqual([node['nodeName'] for node in groups[1]], ['Area A'])

    def test_research_chart_reverses_equal_count_area_order(self) -> None:
        """
        Checks descending counts reverse first appearance when research areas tie.
        """
        key = chart_member_key(['invented-a', 'invented-b', 'invented-c'])
        source = json.loads(self.responses[key].body)
        for index, doc in enumerate(source['response']['docs']):
            person = json.loads(doc['json_txt'])
            person['research_areas'] = ['Area A', 'Area B', 'Area C'] if index < 2 else ['Area C']
            doc['json_txt'] = json.dumps(person)
        self.responses[key] = self.response(source['response']['docs'])
        _, chart = research_areas_data('org-example', self.read)
        groups = chart['nodes']
        if not isinstance(groups, list) or not isinstance(groups[1], list):
            self.fail('Research chart nodes should contain an area list.')
        self.assertEqual([node['nodeName'] for node in groups[1]], ['Area C', 'Area B', 'Area A'])
        self.assertEqual([node['nodeValue'] for node in groups[1]], [3, 2, 2])
        self.assertEqual(
            chart['links'],
            [
                {'source': 1, 'target': 6, 'value': 1},
                {'source': 1, 'target': 5, 'value': 1},
                {'source': 1, 'target': 4, 'value': 1},
                {'source': 2, 'target': 6, 'value': 1},
                {'source': 2, 'target': 5, 'value': 1},
                {'source': 2, 'target': 4, 'value': 1},
                {'source': 3, 'target': 4, 'value': 1},
            ],
        )

    def test_chart_skips_listed_member_missing_from_solr(self) -> None:
        """Uses available members when a listed person has no Solr record."""
        key = chart_member_key(['invented-a', 'invented-b', 'invented-c'])
        response = json.loads(self.responses[key].body)
        response['response']['docs'] = response['response']['docs'][:2]
        response['response']['numFound'] = 2
        self.responses[key] = SourceResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        _, chart = publication_history_data('org-example', self.read)
        self.assertEqual(chart['columns'], ['invented-a', 'invented-b'])

    def test_charts_include_available_data_for_uncategorized_members(self) -> None:
        """
        Checks listed uncategorized members contribute their available publications and research areas.
        """
        key = chart_member_key(['invented-a', 'invented-b', 'invented-c'])
        docs = json.loads(self.responses[key].body)['response']['docs']
        for record_type in ('UNCATEGORIZED', ['UNCATEGORIZED']):
            with self.subTest(record_type=record_type):
                docs[0]['record_type'] = record_type
                self.responses[key] = self.response(docs)
                _, publications = publication_history_data('org-example', self.read)
                self.assertEqual(publications['columns'], ['invented-a', 'invented-b'])
                self.assertEqual(
                    publication_history_csv(publications),
                    'year,year_total,invented-a,invented-b\n2020,3,2,1\n2021,1,1,0',
                )
                _, research = research_areas_data('org-example', self.read)
                groups = research['nodes']
                assert isinstance(groups, list)
                self.assertEqual([node['nodeName'] for node in groups[0]], ['invented-a', 'invented-b', 'invented-c'])
                self.assertEqual(groups[0][0]['display'], 'Invented A')
                self.assertEqual(groups[1][0]['nodeName'], 'Area A')
                self.assertEqual(
                    research['links'], [{'source': 1, 'target': 4, 'value': 1}, {'source': 2, 'target': 4, 'value': 1}]
                )

    def test_uncategorized_members_without_chart_fields_keep_other_members_data(self) -> None:
        """
        Checks absent optional fields retain the named research member without inventing publications or research areas.
        """
        key = chart_member_key(['invented-a', 'invented-b', 'invented-c'])
        docs = json.loads(self.responses[key].body)['response']['docs']
        docs[2].update(record_type='UNCATEGORIZED', json_txt='{}', display_name_s=['Invented C'])
        self.responses[key] = self.response(docs)
        _, publications = publication_history_data('org-example', self.read)
        self.assertEqual(publications['columns'], ['invented-a', 'invented-b'])
        _, research = research_areas_data('org-example', self.read)
        groups = research['nodes']
        assert isinstance(groups, list)
        self.assertEqual(groups[0][2]['nodeName'], 'invented-c')
        self.assertEqual(groups[0][2]['display'], 'Invented C')
        self.assertEqual(groups[0][2]['areas'], '')
        links = research['links']
        assert isinstance(links, list)
        self.assertEqual(len(links), 2)

    def test_uncategorized_member_without_record_data_keeps_other_members_data(self) -> None:
        """
        Checks an absent record field keeps a listed uncategorized member without inventing chart contributions.
        """
        key = chart_member_key(['invented-a', 'invented-b', 'invented-c'])
        docs = json.loads(self.responses[key].body)['response']['docs']
        del docs[0]['json_txt']
        docs[0]['display_name_s'] = ['Invented A']
        for record_type in ('UNCATEGORIZED', ['UNCATEGORIZED']):
            with self.subTest(record_type=record_type):
                docs[0]['record_type'] = record_type
                self.responses[key] = self.response(docs)
                _, publications = publication_history_data('org-example', self.read)
                self.assertEqual(publications['columns'], ['invented-b'])
                self.assertEqual(publication_history_csv(publications), 'year,year_total,invented-b\n2020,1,1')
                _, research = research_areas_data('org-example', self.read)
                groups = research['nodes']
                assert isinstance(groups, list)
                self.assertEqual([node['nodeName'] for node in groups[0]], ['invented-a', 'invented-b', 'invented-c'])
                self.assertEqual(groups[0][0]['display'], 'Invented A')
                self.assertEqual(groups[0][0]['areas'], '')
                self.assertEqual(groups[0][0]['nodeValue'], 0.9)
                self.assertEqual(research['links'], [])

    def test_absent_record_data_still_requires_an_expected_uncategorized_member(self) -> None:
        """
        Checks missing record data does not excuse ordinary people, unsupported types, unrelated IDs, or duplicate members.
        """
        key = chart_member_key(['invented-a', 'invented-b', 'invented-c'])
        original = json.loads(self.responses[key].body)['response']['docs']
        member = {key: value for key, value in original[1].items() if key != 'json_txt'}
        for builder in (publication_history_data, research_areas_data):
            for changes in (
                {'record_type': 'PEOPLE'},
                {'record_type': 'ORGANIZATION'},
                {'record_type': 'UNCATEGORIZED', 'id': 'http://vivo.brown.edu/individual/invented-other'},
                {'record_type': 'UNCATEGORIZED', 'id': original[0]['id']},
            ):
                with self.subTest(builder=builder.__name__, changes=changes):
                    self.responses[key] = self.response([original[0], {**member, **changes}, original[2]])
                    with self.assertRaises(PageDataError):
                        builder('org-example', self.read)
            duplicate = {**member, 'record_type': 'UNCATEGORIZED'}
            self.responses[key] = self.response([duplicate, duplicate])
            with self.subTest(builder=builder.__name__, duplicate=True), self.assertRaises(PageDataError):
                builder('org-example', self.read)

    def test_charts_reject_unexpected_duplicate_or_malformed_members(self) -> None:
        """
        Checks accepting uncategorized members preserves ID, type, duplicate, and record-content checks in both charts.
        """
        key = chart_member_key(['invented-a', 'invented-b', 'invented-c'])
        original = json.loads(self.responses[key].body)['response']['docs']
        for builder in (publication_history_data, research_areas_data):
            for record_type in ('PEOPLE', 'UNCATEGORIZED'):
                for changes in (
                    {'id': 'http://vivo.brown.edu/individual/invented-other'},
                    {'id': original[0]['id']},
                    {'record_type': 'ORGANIZATION'},
                    {'record_type': ''},
                    {'json_txt': 'invalid'},
                    {'json_txt': '[]'},
                    {'json_txt': None},
                    {'json_txt': ''},
                    {'json_txt': []},
                    {'json_txt': ['']},
                    {'json_txt': 'null'},
                ):
                    with self.subTest(builder=builder.__name__, record_type=record_type, changes=changes):
                        doc = {**original[1], 'record_type': record_type, **changes}
                        self.responses[key] = self.response([original[0], doc, original[2]])
                        with self.assertRaises(PageDataError):
                            builder('org-example', self.read)
                with self.subTest(builder=builder.__name__, record_type=record_type, duplicate_first=True):
                    doc = {**original[0], 'record_type': record_type}
                    self.responses[key] = self.response([doc, *original])
                    with self.assertRaises(PageDataError):
                        builder('org-example', self.read)

    def test_uncategorized_member_charts_share_cache_and_show_updated_data_after_expiry(self) -> None:
        """
        Checks all chart formats work without error email and repeated visits cannot delay a member's updated data.
        """
        key = chart_member_key(['invented-a', 'invented-b', 'invented-c'])
        docs = json.loads(self.responses[key].body)['response']['docs']
        updated = list(docs)
        docs[0] = {
            'id': docs[0]['id'],
            'record_type': ['UNCATEGORIZED'],
            'display_name_s': 'Invented A',
        }
        self.responses[key] = self.response(docs)
        with (
            TemporaryDirectory() as directory,
            override_settings(
                CHART_CACHE_TIMEOUT_SECONDS=60,
                REPORT_CACHE_LOCK_DIR=directory + '/locks',
                CACHES={
                    'default': {
                        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
                        'LOCATION': directory + '/cache',
                    }
                },
            ),
            patch('vivo_app.lib.source_org_charts.read_source', side_effect=self.read),
            patch('django.utils.log.AdminEmailHandler.emit') as email,
            patch('time.time', return_value=100) as clock,
        ):
            for suffix in ('publications', 'publications.json', 'publications.csv', 'research', 'research.json'):
                with self.subTest(suffix=suffix):
                    response = self.client.get('/display/org-example/viz/' + suffix)
                    assert isinstance(response, HttpResponse)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn('no-store', response['Cache-Control'])
                    if suffix in ('publications', 'research'):
                        self.assertContains(response, 'Example Organization')
                    elif suffix == 'publications.csv':
                        self.assertEqual(response.content.decode(), 'year,year_total,invented-b\n2020,1,1')
            self.assertEqual(self.requested, [profile_key('org-example'), key] * 2)
            self.responses[key] = self.response(updated)
            clock.return_value = 159
            response = self.client.get('/display/org-example/viz/publications.json')
            assert isinstance(response, HttpResponse)
            self.assertEqual(json.loads(response.content)['columns'], ['invented-b'])
            response = self.client.get('/display/org-example/viz/research.json')
            assert isinstance(response, HttpResponse)
            self.assertEqual(json.loads(response.content)['links'], [])
            self.assertEqual(len(self.requested), 4)
            clock.return_value = 161
            response = self.client.get('/display/org-example/viz/publications.json')
            assert isinstance(response, HttpResponse)
            self.assertEqual(json.loads(response.content)['columns'], ['invented-a', 'invented-b'])
            response = self.client.get('/display/org-example/viz/research.json')
            assert isinstance(response, HttpResponse)
            self.assertEqual(len(json.loads(response.content)['links']), 2)
            self.assertEqual(self.requested, [profile_key('org-example'), key] * 4)
            email.assert_not_called()

    def test_malformed_member_data_is_retried_after_brief_delay(self) -> None:
        """
        Checks damaged member content fails every chart format and corrected content appears after the fixed retry delay.
        """
        key = chart_member_key(['invented-a', 'invented-b', 'invented-c'])
        original = self.responses[key]
        docs = json.loads(original.body)['response']['docs']
        docs[0].update(record_type='UNCATEGORIZED', json_txt='{"name": "Incomplete')
        self.responses[key] = self.response(docs)
        suffixes = ('publications', 'publications.json', 'publications.csv', 'research', 'research.json')
        with (
            TemporaryDirectory() as directory,
            override_settings(
                CHART_CACHE_TIMEOUT_SECONDS=60,
                REPORT_CACHE_LOCK_DIR=directory + '/locks',
                CACHES={
                    'default': {
                        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
                        'LOCATION': directory + '/cache',
                    }
                },
            ),
            patch('vivo_app.lib.source_org_charts.read_source', side_effect=self.read),
            patch('django.utils.log.AdminEmailHandler.emit') as email,
            patch('time.time', return_value=100) as clock,
        ):
            for suffix in suffixes:
                with self.subTest(suffix=suffix):
                    response = self.client.get('/display/org-example/viz/' + suffix)
                    assert isinstance(response, HttpResponse)
                    self.assertEqual(response.status_code, 503)
                    self.assertIn('no-store', response['Cache-Control'])
                    self.assertNotIn(b'Incomplete', response.content)
            email.assert_not_called()
            self.assertEqual(self.requested, [profile_key('org-example'), key] * 2)
            self.responses[key] = original
            clock.return_value = 109
            for suffix in suffixes:
                response = self.client.get('/display/org-example/viz/' + suffix)
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response['Retry-After'], '1')
            self.assertEqual(self.requested, [profile_key('org-example'), key] * 2)
            clock.return_value = 110
            for suffix in suffixes:
                response = self.client.get('/display/org-example/viz/' + suffix)
                assert isinstance(response, HttpResponse)
                self.assertEqual(response.status_code, 200)
            email.assert_not_called()
            self.assertEqual(self.requested, [profile_key('org-example'), key] * 4)

    def test_team_chart_uses_solr_member_order(self) -> None:
        """Keeps the order in which the source returns team faculty records."""
        source = json.loads(self.responses[chart_member_key(['invented-a', 'invented-b', 'invented-c'])].body)
        docs = source['response']['docs'][:2]
        self.responses[chart_member_key(['invented-a', 'invented-b'])] = self.response(list(reversed(docs)))
        with TemporaryDirectory() as directory:
            manifest = Path(directory) / 'teams.json'
            manifest.write_text(
                json.dumps(
                    {'teams': {'team-example': {'name': 'Invented Team', 'member_ids': ['invented-a', 'invented-b']}}}
                )
            )
            with override_settings(TEAM_SOURCE_MANIFEST=str(manifest)):
                _, chart = publication_history_data('team-example', self.read)
        self.assertEqual(chart['columns'], ['invented-b', 'invented-a'])

    def test_organization_charts_keep_sorted_twenty_member_batches(self) -> None:
        """
        Checks sorted member batches preserve returned order in both chart formats.
        """
        prefix = 'http://vivo.brown.edu/individual/'
        identifiers = [f'invented-{index:02}' for index in range(24)]
        people = [
            {'faculty_uri': prefix + identifier, 'label': f'{"a" if index % 2 else "A"}{index:02}'}
            for index, identifier in enumerate(identifiers)
        ]
        self.responses[profile_key('org-example')] = self.response(
            [
                {
                    'id': prefix + 'org-example',
                    'record_type': 'ORGANIZATION',
                    'json_txt': json.dumps({'name': 'Example Organization', 'people': [*reversed(people), people[0]]}),
                }
            ]
        )
        expected: list[str] = []
        for start in (0, 20):
            batch = identifiers[start : start + 20]
            returned = list(reversed(batch))
            expected.extend(returned)
            self.responses[chart_member_key(batch)] = self.response(
                [
                    {
                        'id': prefix + identifier,
                        'record_type': 'PEOPLE',
                        'json_txt': json.dumps(
                            {
                                'name': identifier,
                                'title': 'Professor',
                                'contributor_to': [{'date': '2020-01-01'}],
                                'research_areas': ['Shared area'],
                            }
                        ),
                    }
                    for identifier in returned
                ]
            )
        _, publications = publication_history_data('org-example', self.read)
        _, research = research_areas_data('org-example', self.read)
        self.assertEqual(publications['columns'], expected)
        self.assertEqual(publication_history_csv(publications).splitlines()[0], 'year,year_total,' + ','.join(expected))
        groups = research['nodes']
        if not isinstance(groups, list) or not isinstance(groups[0], list):
            self.fail('Research chart nodes should contain a researcher list.')
        self.assertEqual([node['nodeName'] for node in groups[0]], expected)
        self.assertEqual(
            [key for key in self.requested if key.service == 'solr' and key != profile_key('org-example')],
            [chart_member_key(identifiers[:20]), chart_member_key(identifiers[20:])] * 2,
        )

    def test_chart_reads_publication_year_after_leading_space(self) -> None:
        """Counts the year accepted by the public publication parser."""
        key = chart_member_key(['invented-a', 'invented-b', 'invented-c'])
        response = json.loads(self.responses[key].body)
        first = json.loads(response['response']['docs'][0]['json_txt'])
        first['contributor_to'].append({'date': ' 2022-01-01'})
        response['response']['docs'][0]['json_txt'] = json.dumps(first)
        self.responses[key] = SourceResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        _, chart = publication_history_data('org-example', self.read)
        years = chart['years']
        if not isinstance(years, list):
            self.fail('Chart years should be a list.')
        self.assertIn('2022', years)

    def test_research_chart_keeps_other_members_when_one_area_list_is_invalid(self) -> None:
        """
        Checks malformed optional research areas do not hide the organization chart.
        """
        key = chart_member_key(['invented-a', 'invented-b', 'invented-c'])
        response = json.loads(self.responses[key].body)
        first = json.loads(response['response']['docs'][0]['json_txt'])
        first['research_areas'] = 'unreadable list'
        response['response']['docs'][0]['json_txt'] = json.dumps(first)
        self.responses[key] = SourceResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        _, chart = research_areas_data('org-example', self.read)
        nodes = chart['nodes']
        if not isinstance(nodes, list):
            self.fail('Research chart nodes should be a list.')
        self.assertEqual(len(nodes[0]), 3)
        self.assertEqual(nodes[1], [])

    def test_publication_chart_keeps_other_members_when_one_list_is_invalid(self) -> None:
        """
        Checks invalid optional publications do not hide other member counts.
        """
        key = chart_member_key(['invented-a', 'invented-b', 'invented-c'])
        response = json.loads(self.responses[key].body)
        first = json.loads(response['response']['docs'][0]['json_txt'])
        first['contributor_to'].append('invalid row')
        response['response']['docs'][0]['json_txt'] = json.dumps(first)
        self.responses[key] = SourceResponse(200, (('content-type', 'application/json'),), json.dumps(response).encode())
        _, chart = publication_history_data('org-example', self.read)
        self.assertEqual(chart['columns'], ['invented-b'])

    def test_chart_routes(self) -> None:
        """
        Checks the pages and public JSON and CSV paths use the same source records.
        """
        with patch('vivo_app.lib.source_org_charts.read_source', side_effect=self.read):
            page = self.client.get('/display/org-example/viz/publications')
            json_response = self.client.get('/display/org-example/viz/publications.json')
            csv_response = self.client.get('/display/org-example/viz/publications.csv')
            research_page = self.client.get('/display/org-example/viz/research')
            research_json = self.client.get('/display/org-example/viz/research.json')
        self.assertContains(page, 'Example Organization')
        self.assertContains(page, 'Last 10 years')
        assert isinstance(json_response, HttpResponse)
        assert isinstance(csv_response, HttpResponse)
        assert isinstance(research_json, HttpResponse)
        self.assertEqual(json.loads(json_response.content)['years'], ['2020', '2021'])
        self.assertEqual(csv_response['Content-Type'], 'text/csv')
        self.assertEqual(
            csv_response['Content-Disposition'], 'attachment; filename="org-example.csv"; filename*=UTF-8\'\'org-example.csv'
        )
        self.assertContains(research_page, 'research areas and how common')
        self.assertContains(research_page, '/display/org-example/viz/collab.json')
        self.assertEqual(len(json.loads(research_json.content)['links']), 2)

    def test_missing_source_response_fails(self) -> None:
        """
        Checks a missing member batch cannot be replaced with unrelated records.
        """
        self.responses.pop(chart_member_key(['invented-a', 'invented-b', 'invented-c']))
        with self.assertRaisesRegex(PageDataError, 'source response is missing'):
            publication_history_data('org-example', self.read)

    def test_publication_json_preserves_compact_utf8_and_reference_escaping(self) -> None:
        """
        Checks chart JSON retains literal Unicode, compact punctuation and escaped HTML.
        """
        chart: dict[str, object] = {
            'matrix': [{'year': 2020, 'total': 1, 'invented-a': 1}],
            'years': ['2020'],
            'columns': ['invented-a'],
            'nodes': [{'faculty_id': 'invented-a', 'name': 'Invented É <A>&', 'group': 'Professor'}],
        }
        with patch('vivo_app.views.publication_history_data', return_value=('Example Organization', chart)):
            response = self.client.get('/display/org-example/viz/publications.json')
        assert isinstance(response, HttpResponse)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEqual(json.loads(response.content), chart)
        self.assertEqual(
            response.content.decode('utf-8'),
            '{"matrix":[{"year":2020,"total":1,"invented-a":1}],"years":["2020"],"columns":["invented-a"],'
            '"nodes":[{"faculty_id":"invented-a","name":"Invented É \\u003cA\\u003e\\u0026","group":"Professor"}]}',
        )

    def test_publication_json_retains_unavailable_source_response(self) -> None:
        """
        Checks a missing chart source keeps its existing unavailable response.
        """
        with patch('vivo_app.views.publication_history_data', side_effect=PageDataError('The chart is unavailable.')):
            response = self.client.get('/display/org-example/viz/publications.json')
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 503)
        self.assertContains(response, 'Page data unavailable:', status_code=503)

    def test_research_json_preserves_compact_utf8_and_reference_escaping(self) -> None:
        """
        Checks research JSON retains Unicode, escaped HTML and ordered numeric links.
        """
        chart: dict[str, object] = {
            'nodes': [[{'id': 0, 'display': 'Invented É <A>&'}], [{'id': 1, 'nodeName': 'Area A'}]],
            'links': [{'source': 0, 'target': 1, 'value': 1}],
        }
        with patch('vivo_app.views.research_areas_data', return_value=('Example Organization', chart)):
            response = self.client.get('/display/org-example/viz/research.json')
        assert isinstance(response, HttpResponse)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEqual(json.loads(response.content), chart)
        self.assertEqual(
            response.content.decode('utf-8'),
            '{"nodes":[[{"id":0,"display":"Invented É \\u003cA\\u003e\\u0026"}],[{"id":1,"nodeName":"Area A"}]],'
            '"links":[{"source":0,"target":1,"value":1}]}',
        )

    def test_research_json_retains_unavailable_source_response(self) -> None:
        """
        Checks unavailable research data keeps its existing status and explanation.
        """
        with patch('vivo_app.views.research_areas_data', side_effect=PageDataError('The chart is unavailable.')):
            response = self.client.get('/display/org-example/viz/research.json')
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 503)
        self.assertContains(response, 'Page data unavailable:', status_code=503)
