import json
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch
from collector import BrowserFetcher, Page, collect, jobs, muncitorul_jobs, normalize, recent


class SourceTests(unittest.TestCase):
    def test_muncitorul_filters_roles_and_labels_missing_dates(self):
        body = '<div class="lista__item"><h3>Agent vânzări</h3></div><div class="lista__item"><h3>Jurist</h3><p>Despre noi</p><h3>Cerințe:</h3><p>Studii juridice; 2 ani experiență</p></div>'
        rows, count = muncitorul_jobs(body, 'https://muncitorul.md/ro/posturi_vacante', date(2026, 11, 2))
        self.assertEqual(count, 2)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['date_basis'], 'first_seen')
        self.assertEqual(rows[0]['date'], '2026-11-02')
        self.assertTrue(rows[0]['requirements'].startswith('Cerințe'))

    def test_empty_muncitorul_legal_results_are_verified(self):
        class Fake:
            def get(self, url):
                return '<div class="lista__item"><h3>Agent vânzări</h3></div>'
        rows, report = collect(Fake(), 'Muncitorul.md', 'https://muncitorul.md/ro/posturi_vacante')
        self.assertEqual(rows, [])
        self.assertTrue(report['verified'])
        self.assertEqual(report['errors'], [])

    def test_jobber_english_roles_requirements_and_age(self):
        job = {'@type': 'JobPosting', 'title': 'Insolvency Lawyer', 'hiringOrganization': {'name': 'PFB Collection'}, 'datePosted': '2026-10-24T00:00:00', 'description': '<p>Responsibilities: recover debts</p><p>Requirements</p><p>Insolvency experience; Romanian and Russian</p>'}
        row = normalize(job, 'Jobber.md', 'https://jobber.md/en/job/jurisprudence-chisinau-pfb-collection-insolvency-lawyer/12237/')
        self.assertEqual(row['employer'], 'PFB Collection')
        self.assertTrue(row['requirements'].startswith('Requirements'))
        self.assertFalse(recent(row, date(2026, 11, 2)))
        self.assertTrue(recent(row, date(2026, 10, 25)))
        self.assertIsNone(normalize({'title': 'Manager in Turism'}, 'Jobber.md', 'https://jobber.md'))

    def test_browser_returns_rendered_content_and_closes_page(self):
        fetcher = BrowserFetcher()
        page = MagicMock()
        page.url = 'https://jobber.md/en/jobs/?query=jurist'
        page.title.return_value = 'Job vacancies'
        page.content.return_value = '<a href="/en/job/jurist/1/">Jurist</a>'
        page.goto.return_value.status = 200
        fetcher.browser = MagicMock()
        fetcher.browser.new_page.return_value = page
        with patch.object(fetcher, 'check_robots'):
            body = fetcher.get(page.url)
        self.assertIn('Jurist', body)
        page.wait_for_timeout.assert_called_once()
        page.close.assert_called_once()

    def test_browser_access_denial_is_reported(self):
        fetcher = BrowserFetcher()
        page = MagicMock()
        page.url = 'https://www.lucru.md/ro/jobs-moldova'
        page.title.return_value = '403 Forbidden'
        page.goto.return_value.status = 202
        fetcher.browser = MagicMock()
        fetcher.browser.new_page.return_value = page
        with patch.object(fetcher, 'check_robots'):
            with self.assertRaisesRegex(RuntimeError, 'denied'):
                fetcher.get(page.url)
        page.close.assert_called_once()
