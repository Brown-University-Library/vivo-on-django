"""
Reads active homepage books from a separate database or an exact saved response.
"""

import json
import re
from collections.abc import Callable
from urllib.parse import urlsplit

from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse

from vivo_app.lib.assets import get_random_background_relpath
from vivo_app.lib.prepared_data import PageDataError
from vivo_app.lib.recorded_responses import RecordedResponse, RequestKey
from vivo_app.lib.source_requests import read_source

BOOKS_KEY = RequestKey('book_db', '/book_covers/active')
BOOKS_QUERY = (
    'SELECT jacket_id, firstname, lastname, shortID, title, pub_date, image '
    "FROM book_covers WHERE active = 'y' ORDER BY pub_date DESC LIMIT 501"
)
BookReader = Callable[[RequestKey, str], RecordedResponse]


def book_rows_response() -> RecordedResponse:
    """
    Reads the active rows in Rails order using a separately configured account.

    Called by: source_requests.read_source()
    """
    if not all((settings.BOOK_COVER_DB_HOST, settings.BOOK_COVER_DB_NAME, settings.BOOK_COVER_DB_USER)):
        raise PageDataError('The homepage book database is not configured.')
    try:
        import pymysql
    except ImportError as exc:
        raise PageDataError('The homepage book database driver is not installed.') from exc
    try:
        with (
            pymysql.connect(
                host=settings.BOOK_COVER_DB_HOST,
                port=settings.BOOK_COVER_DB_PORT,
                user=settings.BOOK_COVER_DB_USER,
                password=settings.BOOK_COVER_DB_PASSWORD,
                database=settings.BOOK_COVER_DB_NAME,
                charset='utf8mb4',
                connect_timeout=5,
                read_timeout=5,
                write_timeout=5,
                cursorclass=pymysql.cursors.DictCursor,
            ) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(BOOKS_QUERY)
            rows = cursor.fetchall()
    except pymysql.MySQLError as exc:
        raise PageDataError('The homepage book database request failed.') from exc
    if len(rows) > 500:
        raise PageDataError('The homepage has more active books than the supported limit.')
    body = json.dumps(rows, ensure_ascii=False, default=str).encode('utf-8')
    return RecordedResponse(200, (('content-type', 'application/json'),), body)


def homepage_books(mode: str, reader: BookReader | None = None) -> dict[str, object]:
    """
    Builds four-cover pages from the same active rows in live and replay modes.

    Called by: page_data.get_home_data(), tests
    """
    if reader is None:
        reader = read_source
    response = reader(BOOKS_KEY, mode)
    try:
        rows: object = json.loads(response.body)
    except (ValueError, UnicodeError) as exc:
        raise PageDataError('The homepage book response is invalid.') from exc
    if not isinstance(rows, list) or len(rows) > 500:
        raise PageDataError('The homepage book response is invalid.')
    image_base = settings.BOOK_COVER_BASE_PATH.rstrip('/')
    parsed = urlsplit(image_base)
    valid_origin = parsed.scheme in {'http', 'https'} and bool(parsed.netloc)
    valid_local_path = image_base.startswith('/') and not image_base.startswith('//') and not parsed.netloc
    if not image_base or parsed.query or parsed.fragment or not (valid_origin or valid_local_path):
        raise PageDataError('The homepage book image source is not configured.')
    covers: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise PageDataError('The homepage book response contains an invalid row.')
        identifier, title, filename = row.get('shortID'), row.get('title'), row.get('image')
        first, last = row.get('firstname'), row.get('lastname')
        if (
            not isinstance(identifier, str)
            or re.fullmatch(r'[A-Za-z0-9_-]{1,80}', identifier) is None
            or not isinstance(title, str)
            or not isinstance(filename, str)
            or re.fullmatch(r'[A-Za-z0-9_.-]{1,180}', filename) is None
            or filename.startswith('.')
            or not isinstance(first, str)
            or not isinstance(last, str)
        ):
            raise PageDataError('The homepage book response contains an invalid row.')
        covers.append(
            {
                'author_url': reverse('display_show', args=[identifier]),
                'author_name': (first + ' ' + last).strip(),
                'title': title,
                'image_url': image_base + '/' + filename,
            }
        )
    pages = [covers[index : index + 4] for index in range(0, len(covers), 4)]
    return {'backgrounds': [static(get_random_background_relpath())], 'book_covers_paginated': pages}
