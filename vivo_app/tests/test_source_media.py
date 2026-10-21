"""
Checks public file caching, freshness, missing files, and separate-worker coordination.
"""

import multiprocessing
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

from django.core.cache import cache
from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings

from vivo_app.lib.page_errors import PageDataError
from vivo_app.lib.source_media import cached_media, media_cache_key
from vivo_app.lib.source_requests import document_key, image_key
from vivo_app.lib.source_types import RequestKey, SourceResponse
from vivo_app.tests.test_source_documents import word_document_bytes


def media_worker(key: RequestKey, reader: Mock, destination: str) -> None:
    """
    Records a file read by a separate application worker.

    Called by: SourceMediaTests.test_workers_share_one_successful_fetch()
    """
    Path(destination).write_bytes(cached_media(key, reader).body)


class SourceMediaTests(SimpleTestCase):
    def setUp(self) -> None:
        """
        Checks caching with temporary storage and made-up source responses.
        """
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.enterContext(
            override_settings(
                MEDIA_CACHE_TIMEOUT_SECONDS=60,
                REPORT_CACHE_LOCK_DIR=self.directory.name + '/locks',
                CACHES={
                    'default': {
                        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
                        'LOCATION': self.directory.name + '/cache',
                    }
                },
            )
        )
        self.image = image_key('/profile-images/abc/portrait.jpg')
        self.document = document_key('/docs/i/invented_cv.pdf', (('dt', '1'),))
        self.image_response = SourceResponse(200, (('content-type', 'image/jpeg'),), b'Example image')
        self.pdf_response = SourceResponse(200, (('content-type', 'application/pdf'),), b'%PDF-1.7 Example CV')

    def get_file(self, path: str, method: str = 'GET', range_value: str = '') -> HttpResponse:
        """
        Requests a file and checks that Django returned a complete response.

        Called by: SourceMediaTests test methods
        """
        response = self.client.generic(method, path, HTTP_RANGE=range_value)
        assert isinstance(response, HttpResponse)
        return response

    def test_image_get_head_and_mount_share_cached_bytes(self) -> None:
        """
        Checks repeated image requests share one fetch, preserve HEAD length, and prevent extra browser caching.
        """
        with patch('vivo_app.views.read_source', return_value=self.image_response) as reader:
            for method, prefix in (('head', ''), ('get', ''), ('get', '/mounted')):
                response = getattr(self.client, method)('/source-images' + self.image.path, SCRIPT_NAME=prefix)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, b'' if method == 'head' else self.image_response.body)
                self.assertEqual(response['Content-Length'], str(len(self.image_response.body)))
                self.assertIn('no-store', response['Cache-Control'])
            reader.assert_called_once_with(self.image)

    def test_pdf_aliases_ranges_and_versions_use_the_correct_cached_file(self) -> None:
        """
        Checks original URLs, full downloads, HEAD, and ranges share bytes while a new version reads again.
        """
        with patch('vivo_app.views.read_source', return_value=self.pdf_response) as reader:
            for prefix in ('', '/source-documents'):
                response = self.get_file(prefix + self.document.path + '?dt=1', range_value='bytes=0-4')
                self.assertEqual(response.status_code, 206)
                self.assertEqual(response.content, b'%PDF-')
                self.assertEqual(response['Content-Range'], f'bytes 0-4/{len(self.pdf_response.body)}')
            self.assertEqual(self.get_file(self.document.path + '?dt=1', method='HEAD').content, b'')
            self.assertEqual(self.get_file(self.document.path + '?dt=1').content, self.pdf_response.body)
            reader.assert_called_once_with(self.document)
            reader.return_value = SourceResponse(200, (('content-type', 'application/pdf'),), b'%PDF-1.7 Updated CV')
            self.assertEqual(self.get_file(self.document.path + '?dt=2').content, b'%PDF-1.7 Updated CV')
            self.assertEqual(reader.call_count, 2)

    def test_invalid_cv_is_retried_and_a_corrected_pdf_is_cached(self) -> None:
        """
        Checks invalid CVs stay uncached, a corrected PDF appears on the next request, and valid bytes are reused.
        """
        invalid = SourceResponse(200, (('content-type', 'application/pdf'),), word_document_bytes())
        with (
            patch('vivo_app.views.read_source', side_effect=[invalid, invalid, self.pdf_response]) as reader,
            patch('django.utils.log.AdminEmailHandler.emit') as email,
        ):
            for _ in range(2):
                response = self.get_file(self.document.path + '?dt=1')
                self.assertContains(response, 'This CV is temporarily unavailable.', status_code=404)
                self.assertIsNone(cache.get(media_cache_key(self.document)))
            for _ in range(2):
                response = self.get_file(self.document.path + '?dt=1')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, self.pdf_response.body)
                self.assertEqual(response['Content-Type'], 'application/pdf')
            self.assertEqual(reader.call_count, 3)
            email.assert_not_called()

    def test_prior_word_cache_entries_cannot_bypass_pdf_validation(self) -> None:
        """
        Checks a successful Word entry written by the earlier implementation is never returned.
        """
        word_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        with patch('vivo_app.lib.source_media.MEDIA_VERSION', 1):
            previous_key = media_cache_key(self.document)
        cache.set(previous_key, SourceResponse(200, (('content-type', word_type),), word_document_bytes()))
        with patch('vivo_app.views.read_source', return_value=self.pdf_response) as reader:
            response = self.get_file(self.document.path + '?dt=1')
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(response.content, self.pdf_response.body)
        reader.assert_called_once_with(self.document)

    def test_document_source_failure_remains_503_with_error_email(self) -> None:
        """
        Checks genuine source failures retain their error response and administrator notification.
        """
        with (
            patch('vivo_app.views.read_source', side_effect=PageDataError('Example connection failure.')),
            patch('django.utils.log.AdminEmailHandler.emit') as email,
        ):
            response = self.get_file(self.document.path + '?dt=1')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b'This CV is temporarily unavailable.', response.content)
        self.assertIsNone(cache.get(media_cache_key(self.document)))
        email.assert_called_once()

    def test_fixed_expiry_shows_replaced_files_without_extension_by_hits(self) -> None:
        """
        Checks both file kinds refresh after sixty seconds even when readers keep requesting them.
        """
        for key, original in ((self.image, self.image_response), (self.document, self.pdf_response)):
            reader = Mock(return_value=original)
            with patch('time.time', return_value=100) as clock:
                self.assertEqual(cached_media(key, reader).body, original.body)
                updated = SourceResponse(200, original.headers, original.body + b' Updated')
                reader.return_value = updated
                clock.return_value = 159
                self.assertEqual(cached_media(key, reader).body, original.body)
                clock.return_value = 161
                self.assertEqual(cached_media(key, reader).body, updated.body)
            self.assertEqual(reader.call_count, 2)

    def test_zero_disables_cache_and_locks(self) -> None:
        """
        Checks disabling media caching always reads the source without touching cache storage or locks.
        """
        reader = Mock(return_value=self.image_response)
        with (
            override_settings(MEDIA_CACHE_TIMEOUT_SECONDS=0),
            patch('vivo_app.lib.source_media.cache') as backend,
            patch('vivo_app.lib.source_media.generation_lock') as lock,
        ):
            cached_media(self.image, reader)
            cached_media(self.image, reader)
            backend.get.assert_not_called()
            backend.set.assert_not_called()
            lock.assert_not_called()
        self.assertEqual(reader.call_count, 2)

    def test_missing_files_return_404_and_become_visible_on_next_request(self) -> None:
        """
        Checks absent files do not send server-error email or hide a later upload behind a cached miss.
        """
        for key, found, prefix in (
            (self.image, self.image_response, '/source-images'),
            (self.document, self.pdf_response, '/source-documents'),
        ):
            with (
                patch(
                    'vivo_app.views.read_source', side_effect=[SourceResponse(404, (), b'Example source error'), found]
                ) as reader,
                patch('django.utils.log.AdminEmailHandler.emit') as email,
            ):
                path = prefix + key.path + ('?dt=1' if key.query else '')
                missing = self.get_file(path)
                self.assertEqual(missing.status_code, 404)
                self.assertNotIn(b'Example source error', missing.content)
                self.assertIn('no-store', missing['Cache-Control'])
                self.assertEqual(self.get_file(path).content, found.body)
                self.assertEqual(reader.call_count, 2)
                email.assert_not_called()

    def test_invalid_files_and_transient_failures_are_not_cached(self) -> None:
        """
        Checks a bad response or unavailable source cannot delay recovery after a later successful response.
        """
        for key, found in ((self.image, self.image_response), (self.document, self.pdf_response)):
            for failure in (
                PageDataError('Example connection failure.'),
                SourceResponse(503, (), b'Example outage'),
                SourceResponse(200, (('content-type', 'text/html'),), b'Example login page'),
            ):
                cache.clear()
                reader = Mock(side_effect=[failure, found])
                with self.assertRaises(PageDataError):
                    cached_media(key, reader)
                self.assertIsNone(cache.get(media_cache_key(key)))
                self.assertEqual(cached_media(key, reader).body, found.body)

    def test_redirects_are_not_cached_and_stay_local(self) -> None:
        """
        Checks a document's latest-version redirect is read each time and rewritten locally.
        """
        response = SourceResponse(302, (('location', 'https://source.invalid/docs/i/invented_cv.pdf?dt=2'),), b'')
        with patch('vivo_app.views.read_source', return_value=response) as reader:
            for _ in range(2):
                result = self.get_file('/source-documents/docs/i/invented_cv.pdf')
                self.assertEqual(result.status_code, 302)
                self.assertEqual(result['Location'], '/source-documents/docs/i/invented_cv.pdf?dt=2')
            self.assertEqual(reader.call_count, 2)

    def test_invalid_redirect_target_is_rejected(self) -> None:
        """
        Checks source redirects cannot send a visitor to an unrelated site.
        """
        response = SourceResponse(302, (('location', 'https://unrelated.invalid/docs/i/invented_cv.pdf'),), b'')
        with patch('vivo_app.views.read_source', return_value=response):
            self.assertEqual(self.get_file(self.document.path).status_code, 503)

    def test_cache_keys_separate_sources_versions_and_settings(self) -> None:
        """
        Checks filenames, source addresses, document versions, and lifetimes cannot share cached content.
        """
        original = media_cache_key(self.document)
        self.assertNotEqual(original, media_cache_key(self.image))
        self.assertNotEqual(original, media_cache_key(document_key('/docs/i/other_cv.pdf', self.document.query)))
        self.assertNotEqual(original, media_cache_key(document_key(self.document.path, (('dt', '2'),))))
        for change in ({'DOCUMENTS_URL': 'https://changed.invalid'}, {'MEDIA_CACHE_TIMEOUT_SECONDS': 30}):
            with override_settings(**change):
                self.assertNotEqual(original, media_cache_key(self.document))
        with patch('vivo_app.lib.source_media.MEDIA_VERSION', 3):
            self.assertNotEqual(original, media_cache_key(self.document))
        for value in ('source.invalid', 'invented_cv'):
            self.assertNotIn(value, original)

    def test_failed_refresh_does_not_return_expired_content(self) -> None:
        """
        Checks a source failure after expiry keeps the unavailable response and allows the next attempt.
        """
        reader = Mock(side_effect=[self.image_response, PageDataError('Example outage'), self.image_response])
        with patch('time.time', return_value=100):
            cached_media(self.image, reader)
        with patch('time.time', return_value=161):
            with self.assertRaises(PageDataError):
                cached_media(self.image, reader)
            self.assertEqual(cached_media(self.image, reader), self.image_response)

    def test_storage_failure_returns_503(self) -> None:
        """
        Checks cache storage failures use the controlled media error response.
        """
        with patch('vivo_app.lib.source_media.cache.get', side_effect=OSError('Example cache failure')):
            result = self.get_file('/source-images' + self.image.path)
        self.assertEqual(result.status_code, 503)

    def slow_read(self, key: RequestKey) -> SourceResponse:
        """
        Records a slow source read in a file visible to separate workers.

        Called by: test_workers_share_one_successful_fetch()
        """
        with (Path(self.directory.name) / 'reads').open('a') as output:
            output.write(key.service + '\n')
        time.sleep(0.1)
        return self.image_response

    def test_workers_share_one_successful_fetch(self) -> None:
        """
        Checks concurrent workers fetch the same successful image only once.
        """
        context = multiprocessing.get_context('fork')
        reader = Mock(side_effect=self.slow_read)
        workers = [
            context.Process(target=media_worker, args=(self.image, reader, self.directory.name + f'/done-{n}'))
            for n in range(3)
        ]
        try:
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join(timeout=10)
                self.assertEqual(worker.exitcode, 0)
        finally:
            for worker in workers:
                if worker.is_alive():
                    worker.terminate()
                    worker.join()
        self.assertEqual((Path(self.directory.name) / 'reads').read_text(), 'images\n')
        for n in range(3):
            self.assertEqual((Path(self.directory.name) / f'done-{n}').read_bytes(), self.image_response.body)
