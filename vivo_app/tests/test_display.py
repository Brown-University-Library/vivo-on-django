from unittest.mock import patch

from django.test import TestCase

from vivo_app.lib import display as display_lib


class DisplayShowTests(TestCase):
    def test_display_json_people_type(self):
        resp = self.client.get('/display/n1/?format=json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get('Content-Type'), 'application/json')
        body = resp.json()
        self.assertEqual(body.get('id'), 'n1')
        self.assertEqual(body.get('type'), 'PEOPLE')
        self.assertIn('presenter', body)
        self.assertIn('faculty', body['presenter'])

    def test_display_html_people_type(self):
        resp = self.client.get('/display/n42/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/html', resp.headers.get('Content-Type', ''))
        self.assertContains(resp, 'Mock Person n42')
        self.assertContains(resp, 'VIVO ID: n42')

    def test_display_json_organization_type(self):
        resp = self.client.get('/display/org123/?format=json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get('Content-Type'), 'application/json')
        body = resp.json()
        self.assertEqual(body.get('id'), 'org123')
        self.assertEqual(body.get('type'), 'ORGANIZATION')
        self.assertIn('presenter', body)
        self.assertIn('organization', body['presenter'])

    def test_display_html_unknown_type(self):
        resp = self.client.get('/display/x999/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/html', resp.headers.get('Content-Type', ''))
        self.assertContains(resp, 'Item ID: x999')

    def test_display_people_panels_render(self):
        resp = self.client.get('/display/n42/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'text/html', resp.headers.get('Content-Type', '').encode())
        # Panels present
        self.assertIn(b'id="people-left-panel"', resp.content)
        self.assertIn(b'id="people-right-panel"', resp.content)
        # Left panel buttons (default flags: publications & details true; others false)
        self.assertIn(b'id="tabOverviewBtn"', resp.content)
        self.assertIn(b'id="tabPublicationsBtn"', resp.content)
        self.assertIn(b'id="tabAllBtn"', resp.content)
        self.assertNotIn(b'id="tabResearchBtn"', resp.content)
        self.assertNotIn(b'id="tabBackgroundBtn"', resp.content)
        self.assertNotIn(b'id="tabAffiliationsBtn"', resp.content)
        self.assertNotIn(b'id="tabTeachingBtn"', resp.content)
        # Right panel placeholders always present
        self.assertIn(b'id="tabOverview"', resp.content)
        self.assertIn(b'id="tabPublications"', resp.content)
        self.assertIn(b'id="tabResearch"', resp.content)
        self.assertIn(b'id="tabBackground"', resp.content)
        self.assertIn(b'id="tabAffiliations"', resp.content)
        self.assertIn(b'id="tabTeaching"', resp.content)

    def test_display_people_tab_buttons_all_off(self):
        """All flags off => only Overview button visible (no Publications/All)."""

        def _ctx(entity_id, entity_type, request):
            ctx = display_lib.build_display_context(entity_id, entity_type, request)
            pres = ctx.get('presenter', {})
            pres['has_publications'] = False
            pres['has_research'] = False
            pres['has_background'] = False
            pres['has_affiliations'] = False
            pres['has_teaching'] = False
            pres['has_details'] = False
            pres['edit_mode'] = False
            ctx['presenter'] = pres
            return ctx

        with patch('vivo_app.views.build_display_context', side_effect=_ctx):
            resp = self.client.get('/display/n7/')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'id="tabOverviewBtn"', resp.content)
            self.assertNotIn(b'id="tabPublicationsBtn"', resp.content)
            self.assertNotIn(b'id="tabResearchBtn"', resp.content)
            self.assertNotIn(b'id="tabBackgroundBtn"', resp.content)
            self.assertNotIn(b'id="tabAffiliationsBtn"', resp.content)
            self.assertNotIn(b'id="tabTeachingBtn"', resp.content)
            self.assertNotIn(b'id="tabAllBtn"', resp.content)

    def test_display_people_tab_buttons_edit_mode_shows_all(self):
        """Edit mode shows all buttons regardless of flags."""

        def _ctx(entity_id, entity_type, request):
            ctx = display_lib.build_display_context(entity_id, entity_type, request)
            pres = ctx.get('presenter', {})
            pres['edit_mode'] = True
            # Ensure flags false to confirm edit_mode gating
            pres['has_publications'] = False
            pres['has_research'] = False
            pres['has_background'] = False
            pres['has_affiliations'] = False
            pres['has_teaching'] = False
            pres['has_details'] = False
            ctx['presenter'] = pres
            return ctx

        with patch('vivo_app.views.build_display_context', side_effect=_ctx):
            resp = self.client.get('/display/n8/')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'id="tabOverviewBtn"', resp.content)
            self.assertIn(b'id="tabPublicationsBtn"', resp.content)
            self.assertIn(b'id="tabResearchBtn"', resp.content)
            self.assertIn(b'id="tabBackgroundBtn"', resp.content)
            self.assertIn(b'id="tabAffiliationsBtn"', resp.content)
            self.assertIn(b'id="tabTeachingBtn"', resp.content)
            self.assertIn(b'id="tabAllBtn"', resp.content)
