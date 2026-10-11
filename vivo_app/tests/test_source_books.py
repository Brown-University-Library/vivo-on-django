"""
Checks homepage books from a saved database response without database access.
"""

import json
import sys
from unittest.mock import MagicMock, patch

from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import get_script_prefix, set_script_prefix

from vivo_app.lib.page_errors import PageDataError
from vivo_app.lib.source_books import BOOKS_KEY, BOOKS_QUERY, book_rows_response, homepage_books
from vivo_app.lib.source_requests import read_source
from vivo_app.lib.source_types import RequestKey, SourceResponse


@override_settings(BOOK_COVER_BASE_PATH='/book-images')
class SourceBookTests(TestCase):
    """Checks active book order, page grouping, and exact source selection."""

    def setUp(self) -> None:
        """
        Creates five made-up active database rows in publication order.
        """
        rows = [
            {
                'jacket_id': index,
                'firstname': 'Invented',
                'lastname': f'Author {index}',
                'shortID': f'invented-{index}',
                'title': f'Invented Book {index}',
                'pub_date': 2030 - index,
                'image': f'invented-{index}.jpg',
            }
            for index in range(5)
        ]
        self.response = SourceResponse(200, (('content-type', 'application/json'),), json.dumps(rows).encode())
        self.requested: list[RequestKey] = []

    def read(
        self,
        key: RequestKey,
    ) -> SourceResponse:
        """
        Supplies only the made-up active book query.

        Called by: test_repeated_reads_group_the_same_rows(), test_source_homepage_renders_source_books()
        """
        self.requested.append(key)
        if key != BOOKS_KEY:
            raise PageDataError('The requested source response is missing.')
        return self.response

    def test_repeated_reads_group_the_same_rows(self) -> None:
        """
        Checks repeated reads use the same query key and retain the final short page.
        """
        first = homepage_books(self.read)
        repeated = homepage_books(self.read)
        self.assertEqual(first['book_covers_paginated'], repeated['book_covers_paginated'])
        pages = repeated['book_covers_paginated']
        assert isinstance(pages, list)
        self.assertEqual([len(page) for page in pages], [4, 1])
        self.assertEqual(pages[0][0]['image_url'], '/book-images/invented-0.jpg')
        self.assertEqual(pages[0][0]['author_url'], '/display/invented-0')
        self.assertEqual(self.requested, [BOOKS_KEY, BOOKS_KEY])

    def test_book_links_keep_the_application_prefix_without_a_trailing_slash(self) -> None:
        """
        Checks author links reach the public display route beneath the application prefix.
        """
        previous_prefix = get_script_prefix()
        set_script_prefix('/mounted-app/')
        try:
            data = homepage_books(self.read)
            pages = data['book_covers_paginated']
            assert isinstance(pages, list)
            self.assertEqual(pages[0][0]['author_url'], '/mounted-app/display/invented-0')
        finally:
            set_script_prefix(previous_prefix)

    def test_source_homepage_renders_source_books(self) -> None:
        """
        Checks the normal homepage template reads the recorded row response.
        """
        with patch('vivo_app.lib.source_books.read_source', side_effect=self.read):
            response = self.client.get('/')
        assert isinstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invented Book 0')
        self.assertContains(response, '/book-images/invented-4.jpg')
        self.assertEqual(self.requested, [BOOKS_KEY])

    def test_invalid_or_missing_book_response_fails(self) -> None:
        """
        Checks an absent source response cannot produce a successful book page.
        """
        with self.assertRaisesRegex(PageDataError, 'source response is missing'):
            homepage_books(lambda key,: (_ for _ in ()).throw(PageDataError('source response is missing')))
        self.response = SourceResponse(200, (), b'{"wrong":"shape"}')
        with self.assertRaisesRegex(PageDataError, 'invalid'):
            homepage_books(self.read)
        with (
            override_settings(BOOK_COVER_BASE_PATH='//unintended-origin'),
            self.assertRaisesRegex(PageDataError, 'image source'),
        ):
            homepage_books(lambda key,: SourceResponse(200, (), b'[]'))

    def test_unusable_book_row_does_not_hide_other_covers(self) -> None:
        """
        Checks incomplete optional text and an unusable image leave valid covers visible.
        """
        rows = json.loads(self.response.body)
        rows[0]['firstname'] = None
        rows[0]['lastname'] = None
        rows[1]['image'] = None
        self.response = SourceResponse(200, (), json.dumps(rows).encode())
        result = homepage_books(self.read)
        pages = result['book_covers_paginated']
        if not isinstance(pages, list):
            self.fail('Book pages should be a list.')
        self.assertEqual(sum(len(page) for page in pages), 4)
        self.assertEqual(pages[0][0]['author_name'], '')

    def test_homepage_keeps_more_than_five_hundred_active_books(self) -> None:
        """
        Checks a growing book table remains available without an arbitrary row cutoff.
        """
        rows = json.loads(self.response.body)
        expanded = [dict(rows[0], jacket_id=index, shortID=f'invented-{index}') for index in range(501)]
        self.response = SourceResponse(200, (), json.dumps(expanded).encode())
        result = homepage_books(self.read)
        pages = result['book_covers_paginated']
        if not isinstance(pages, list):
            self.fail('Book pages should be a list.')
        self.assertEqual(len(pages), 126)
        self.assertEqual(len(pages[-1]), 1)

    def test_source_dispatch_accepts_only_the_book_query(self) -> None:
        """
        Checks the source reader rejects other database query names.
        """
        with patch('vivo_app.lib.source_books.book_rows_response', return_value=self.response) as books:
            self.assertEqual(read_source(BOOKS_KEY), self.response)
            with self.assertRaisesRegex(PageDataError, 'unsupported'):
                read_source(RequestKey('book_db', '/other'))
        books.assert_called_once_with()

    @override_settings(
        BOOK_COVER_DB_HOST='invented-host',
        BOOK_COVER_DB_NAME='invented-database',
        BOOK_COVER_DB_USER='invented-reader',
        BOOK_COVER_DB_PASSWORD='invented-password',
        BOOK_COVER_DB_PORT=3306,
    )
    def test_source_database_reads_only_active_ordered_rows(self) -> None:
        """
        Checks the database source runs one read-only active-books query.
        """
        driver = MagicMock()
        cursor = driver.connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [{'shortID': 'invented-a', 'active': 'y'}]
        with patch.dict(sys.modules, {'pymysql': driver}):
            response = book_rows_response()
        cursor.execute.assert_called_once_with(BOOKS_QUERY)
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(response.body), cursor.fetchall.return_value)
