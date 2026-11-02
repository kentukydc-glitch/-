import json
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch
from collector import BrowserFetcher, Page, collect, delu_job, jobs, load_lucru_cache, normalize, recent, source_batches


class SourceTests(unittest.TestCase):
    def test_reading_mac_cache_does_not_refresh_its_collection_time(self):
        import os
        import tempfile
        import collector
        from datetime import datetime, timedelta, timezone
        original = os.getcwd()
        stamp = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        try:
            with tempfile.TemporaryDirectory() as directory:
                path, _ = self.mac_cache(directory, collected=stamp)
                os.chdir(directory)
                with patch.dict(os.environ, {'DIGEST_LUCRU_CACHE': str(path)}), patch.object(collector, 'collect', side_effect=AssertionError('Unexpected direct collection')), patch('sys.argv', ['collector.py', '--source', 'Lucru.md']):
                    collector.main()
                data = json.loads(Path('output/lucru-cache.json').read_text())
                self.assertEqual(data['collected_at'], stamp)
        finally:
            os.chdir(original)

    def mac_cache(self, directory, collected='2026-11-02T20:00:00+00:00', posted='2026-10-29'):
        row = dict(source='Lucru.md', employer='Clinic', title='Jurist', requirements='Studii juridice', city='Chișinău', date=posted, date_source='JobPosting.datePosted', expires='', url='https://www.lucru.md/ro/lucru/jurist/145168')
        report = dict(source='Lucru.md', verified=True, pages=2, postings=1, errors=[], coverage='Mac')
        data = dict(version=1, source='Lucru.md', collected_at=collected, vacancies=[row], report=report)
        path = Path(directory) / 'lucru-cache.json'
        path.write_text(json.dumps(data))
        return path, data

    def test_fresh_mac_cache_keeps_original_publication_date(self):
        import tempfile
        from datetime import datetime, timezone
        with tempfile.TemporaryDirectory() as directory:
            path, _ = self.mac_cache(directory, posted='2025-06-24')
            rows, report = load_lucru_cache(path, datetime(2026, 11, 2, 21, tzinfo=timezone.utc))
        self.assertEqual(rows[0]['date'], '2025-06-24')
        self.assertFalse(recent(rows[0], date(2026, 11, 2)))
        self.assertIn('Собрано на вашем Mac', report['coverage'])

    def test_stale_or_future_mac_cache_is_rejected(self):
        import tempfile
        from datetime import datetime, timezone
        with tempfile.TemporaryDirectory() as directory:
            for stamp in ('2026-10-30T20:00:00+00:00', '2026-11-03T20:00:00+00:00'):
                path, _ = self.mac_cache(directory, collected=stamp)
                with self.assertRaises(ValueError):
                    load_lucru_cache(path, datetime(2026, 11, 2, 21, tzinfo=timezone.utc))

    def test_unverified_or_wrong_domain_mac_cache_is_rejected(self):
        import tempfile
        from datetime import datetime, timezone
        now = datetime(2026, 11, 2, 21, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            path, data = self.mac_cache(directory)
            data['report']['verified'] = False
            path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                load_lucru_cache(path, now)
            data['report']['verified'] = True
            data['vacancies'][0]['url'] = 'https://other.example/job'
            path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                load_lucru_cache(path, now)

    def test_missing_mac_cache_does_not_block_other_collection(self):
        import collector
        report = dict(source='Lucru.md', verified=False, pages=1, postings=0, errors=['Denied'], coverage='Direct')
        with patch.object(collector, 'collect', return_value=([], report)) as mocked:
            batches = list(source_batches(object(), ['Lucru.md'], '/missing/lucru-cache.json'))
        mocked.assert_called_once()
        self.assertTrue(any('Mac' in error for error in batches[0][1]['errors']))

    def test_posting_timestamp_is_displayed_as_publication_date(self):
        row = normalize(dict(title='Jurist', datePosted='2026-10-29T12:22:01+02:00'), 'Lucru.md', 'https://www.lucru.md/ro/lucru/jurist/145168')
        self.assertEqual(row['date'], '2026-10-29')
        self.assertEqual(row['date_source'], 'JobPosting.datePosted')

    def test_source_selection_checks_only_lucru(self):
        import os
        import tempfile
        import collector
        original = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as directory:
                os.chdir(directory)
                report = dict(source='Lucru.md', pages=1, postings=0, errors=[], coverage='Fixture')
                with patch.object(collector, 'collect', return_value=([], report)) as mocked, patch('sys.argv', ['collector.py', '--source', 'Lucru.md']):
                    collector.main()
                self.assertEqual(mocked.call_count, 1)
                self.assertEqual(mocked.call_args.args[1], 'Lucru.md')
        finally:
            os.chdir(original)

    def test_mac_uses_separate_visible_browser_profile(self):
        import os
        import sys
        from types import SimpleNamespace
        manager, engine, context, page = MagicMock(), MagicMock(), MagicMock(), MagicMock()
        manager.start.return_value = engine
        engine.chromium.launch_persistent_context.return_value = context
        context.new_page.return_value = page
        page.url = 'https://www.lucru.md/ro/jobs-moldova'
        page.title.return_value = 'Vacancies'
        page.goto.return_value.status = 200
        page.content.return_value = '<html>Vacancies</html>'
        module = SimpleNamespace(sync_playwright=lambda: manager)
        fetcher = BrowserFetcher()
        with patch.dict(sys.modules, {'playwright.sync_api': module}), patch.dict(os.environ, dict(DIGEST_BROWSER_PROFILE='/tmp/test-lucru-profile', DIGEST_BROWSER_HEADLESS='false', DIGEST_BROWSER_WAIT_MS='0')), patch.object(fetcher, 'check_robots'):
            self.assertIn('Vacancies', fetcher.get(page.url))
            fetcher.close()
        engine.chromium.launch_persistent_context.assert_called_once_with('/tmp/test-lucru-profile', headless=False)
        engine.chromium.launch.assert_not_called()
        engine.stop.assert_called_once()

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
