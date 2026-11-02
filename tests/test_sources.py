import json
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch
from collector import BrowserFetcher, Page, collect, delu_job, jobs, normalize, recent


class SourceTests(unittest.TestCase):
    def test_weekly_gate_rejects_dates_without_publication_provenance(self):
        row = dict(date='2026-11-02', expires='')
        self.assertFalse(recent(row, date(2026, 11, 2)))
        row['date_source'] = 'updated_at'
        self.assertFalse(recent(row, date(2026, 11, 2)))
        row['date_source'] = 'JobPosting.datePosted'
        self.assertTrue(recent(row, date(2026, 11, 2)))

    def test_publication_date_survives_literal_newlines_in_source_jsonld(self):
        body = '<h2 class="job-item-title">Юрист</h2><script type="application/ld+json">{"@type":"JobPosting","title":"Юрист","description":"Фирме требуется юрист\nВ Кишиневе","datePosted":"2026-07-20"}</script>'
        row = delu_job(body, 'https://www.delucru.md/job/112801')
        self.assertEqual(row['date'], '2026-07-20')

    def test_promotion_today_does_not_replace_original_posting_date(self):
        body = '<h2 class="job-item-title">Юрист</h2><div class="page-item-date">Publicat azi</div><script type="application/ld+json">{"@type":"JobPosting","title":"Юрист","datePosted":"2026-07-20"}</script>'
        row = delu_job(body, 'https://www.delucru.md/job/112801', date(2026, 11, 2))
        self.assertEqual(row['date'], '2026-07-20')
        self.assertEqual(row['displayed_date'], '2026-11-02')
        self.assertFalse(recent(row, date(2026, 11, 2)))

    def test_missing_posting_date_is_not_inferred_from_yesterday(self):
        row = delu_job('<h2 class="job-item-title">Jurist</h2><div class="page-item-date">Publicat Ieri</div>', 'https://www.delucru.md/job/114007', date(2026, 11, 2))
        self.assertEqual(row['date'], '')
        self.assertEqual(row['displayed_date'], '2026-11-01')
        self.assertFalse(recent(row, date(2026, 11, 2)))

    def test_conflicting_posting_metadata_is_not_guessed(self):
        body = '<h2 class="job-item-title">Jurist</h2><script type="application/ld+json">[{"@type":"JobPosting","title":"Jurist","datePosted":"2026-07-20"},{"@type":"JobPosting","title":"Jurist","datePosted":"2026-11-02"}]</script>'
        row = delu_job(body, 'https://www.delucru.md/job/1')
        self.assertEqual(row['date'], '')
        self.assertEqual(row['date_source'], 'conflicting')

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
