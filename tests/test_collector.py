import unittest
from datetime import date
from collector import Page, jobs, normalize, recent, render, collect, delu_job


class DigestTests(unittest.TestCase):
    def test_sitemap_discovery_filters_legal_urls(self):
        from collector import Fetcher
        from urllib.robotparser import RobotFileParser
        from unittest.mock import patch
        fetcher = Fetcher()
        robots = RobotFileParser()
        robots.parse(['User-agent: *', 'Allow: /', 'Sitemap: https://example.com/sitemap.xml'])
        fetcher.robots['https://example.com'] = robots
        xml = '<urlset><url><loc>https://example.com/job/jurist/1</loc></url><url><loc>https://example.com/job/accountant/2</loc></url></urlset>'
        with patch.object(fetcher, 'get', return_value=xml):
            self.assertEqual(fetcher.sitemap_candidates('https://example.com/'), ['https://example.com/job/jurist/1'])

    def test_delu_html_adapter(self):
        row = delu_job('''<h2 class="job-item-title">Jurisconsult</h2><a href="/company/bnm">BNM</a><div class="page-item-date">Publicat azi</div><div><div>Oraș:</div><div>Chișinău</div></div><div id="job-description"><p>Despre noi</p><strong>Cerințe</strong><ul><li>Studii juridice</li><li>4 ani experiență</li></ul></div>''', 'https://www.delucru.md/job/1', date(2026, 11, 2))
        self.assertEqual(row['employer'], 'BNM')
        self.assertEqual(row['date'], '2026-11-02')
        self.assertEqual(row['city'], 'Chișinău')
        self.assertTrue(row['requirements'].startswith('Cerințe'))
        self.assertNotIn('Despre noi', row['requirements'])

    def test_failed_smtp_does_not_mark_vacancies_delivered(self):
        import os
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from datetime import datetime
        from zoneinfo import ZoneInfo
        import collector
        row = dict(source='Example', employer='Company', title='Jurist', requirements='Legal studies', city='Chisinau', date=datetime.now(ZoneInfo('Europe/Chisinau')).date().isoformat(), expires='', url='https://example.com/job/1')
        report = dict(source='Example', pages=1, postings=1, errors=[], coverage='Test')
        original = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as directory:
                os.chdir(directory)
                with patch.object(collector, 'SOURCES', {'Example': 'https://example.com'}), patch.object(collector, 'collect', return_value=([row], report)), patch('sys.argv', ['collector.py', '--send']), patch.dict(os.environ, dict(SMTP_HOST='smtp.example.com', SMTP_USER='test', SMTP_PASSWORD='test-fixture', SMTP_FROM='test@example.com')), patch.object(collector, 'send', side_effect=RuntimeError('SMTP unavailable')):
                    with self.assertRaises(RuntimeError):
                        collector.main()
                self.assertFalse(Path('state/seen.json').exists())
                with patch.object(collector, 'SOURCES', {'Example': 'https://example.com'}), patch.object(collector, 'collect', return_value=([row], report)), patch('sys.argv', ['collector.py', '--send']), patch.dict(os.environ, dict(SMTP_HOST='smtp.example.com', SMTP_USER='test', SMTP_PASSWORD='test-fixture', SMTP_FROM='test@example.com')), patch.object(collector, 'send'):
                    collector.main()
                    self.assertTrue(Path('state/seen.json').exists())
                    collector.main()
                    self.assertIn('Найдено новых объявлений: 0', Path('output/digest.html').read_text())
        finally:
            os.chdir(original)

    def test_category_discovery(self):
        import os
        import tempfile
        pages = {
            'https://example.com/': '<a href="https://www.example.com/jobs/law">Juridic</a>',
            'https://www.example.com/jobs/law': '<a href="/job/jurist">Jurist</a>',
            'https://www.example.com/job/jurist': '<script type="application/ld+json">{"@type":"JobPosting","title":"Jurist","datePosted":"2026-11-02"}</script>',
        }
        class FakeFetcher:
            def get(self, url):
                return pages[url]
        original = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as directory:
                os.chdir(directory)
                rows, report = collect(FakeFetcher(), 'Example', 'https://example.com/')
        finally:
            os.chdir(original)
        self.assertEqual(report['pages'], 3)
        self.assertEqual(report['errors'], [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['title'], 'Jurist')

    def test_extract_filter_and_render(self):
        page = Page('''<a href="/job/1">Jurist</a><script type="application/ld+json">{"@graph":[{"@type":"JobPosting","title":"Jurist","hiringOrganization":{"name":"A & B"},"datePosted":"2026-11-02","qualifications":"<p>Studii juridice</p>","url":"/job/1"}]}</script>''')
        import json
        row = normalize(next(jobs(json.loads(page.scripts[0]))), 'Example', 'https://example.com/')
        self.assertEqual(row['url'], 'https://example.com/job/1')
        self.assertEqual(row['requirements'], 'Studii juridice')
        self.assertTrue(recent(row, date(2026, 11, 2)))
        self.assertIn('A &amp; B', render([row], []))
        self.assertEqual(page.links, [('/job/1', 'Jurist')])

    def test_old_missing_expired_and_irrelevant(self):
        self.assertIsNone(normalize({'title': 'Accountant'}, 'Example', 'https://example.com'))
        row = {'date': '2026-10-01', 'expires': ''}
        self.assertFalse(recent(row, date(2026, 11, 2)))
        row['date'] = ''
        self.assertFalse(recent(row, date(2026, 11, 2)))
        row.update(date='2026-11-01', expires='2026-11-01')
        self.assertFalse(recent(row, date(2026, 11, 2)))


if __name__ == '__main__':
    unittest.main()
