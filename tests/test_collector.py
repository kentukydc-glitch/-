import unittest
from datetime import date
from collector import Page, jobs, normalize, recent, render


class DigestTests(unittest.TestCase):
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
