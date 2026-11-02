"""Weekly Moldova legal vacancies digest; Python 3.11+, no dependencies."""
import argparse
import hashlib
import html
import json
import os
import re
import smtplib
import ssl
import time
from datetime import datetime, timedelta
from email.message import EmailMessage
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
from zoneinfo import ZoneInfo

SOURCES = {
    'Lucru.md': 'https://www.lucru.md/ro/jobs-moldova',
    'Delucru.md': 'https://www.delucru.md/',
    'Jobber.md': 'https://jobber.md/en/',
    '999.md': 'https://999.md/ro/work',
    'Muncitorul.md': 'https://muncitorul.md/',
    'TopAngajatori.md': 'https://topangajatori.md/',
}
KEYWORDS = re.compile(r'юрист|юрисконсульт|адвокат|\bjurist\w*|consilier\s+juridic|\bavocat\w*|legal\s+counsel', re.I)
AGENT = 'LegalVacancyDigest/1.0'


class Page(HTMLParser):
    def __init__(self, body):
        super().__init__()
        self.links, self.scripts = [], []
        self.href, self.label, self.script = None, [], None
        self.feed(body)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a':
            self.href, self.label = attrs.get('href'), []
        if tag == 'script' and attrs.get('type', '').lower() == 'application/ld+json':
            self.script = []

    def handle_data(self, data):
        if self.href is not None:
            self.label.append(data)
        if self.script is not None:
            self.script.append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.href is not None:
            self.links.append((self.href, ' '.join(self.label)))
            self.href = None
        if tag == 'script' and self.script is not None:
            self.scripts.append(''.join(self.script))
            self.script = None


def plain(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', str(value or '')))).strip()


def jobs(value):
    if isinstance(value, list):
        for item in value:
            yield from jobs(item)
    elif isinstance(value, dict):
        kind = value.get('@type', [])
        if kind == 'JobPosting' or isinstance(kind, list) and 'JobPosting' in kind:
            yield value
        else:
            for item in value.values():
                yield from jobs(item)


def normalize(job, source, page_url):
    title = plain(job.get('title'))
    if not KEYWORDS.search(title):
        return None
    org = job.get('hiringOrganization', {})
    locations = job.get('jobLocation', [])
    if isinstance(locations, dict):
        locations = [locations]
    city = ', '.join(plain(loc.get('address', {}).get('addressLocality')) for loc in locations if isinstance(loc, dict) and isinstance(loc.get('address', {}), dict))
    url = urljoin(page_url, job.get('url') or page_url)
    parts = urlsplit(url)
    url = urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ''))
    return dict(source=source, employer=plain(org.get('name')) if isinstance(org, dict) else plain(org), title=title,
                requirements=plain(job.get('qualifications') or job.get('skills') or job.get('description'))[:700],
                city=city, date=plain(job.get('datePosted')), expires=plain(job.get('validThrough')), url=url)


class Fetcher:
    def __init__(self):
        self.robots = {}

    def raw(self, url):
        request = Request(url, headers={'User-Agent': AGENT})
        with urlopen(request, timeout=25) as response:
            # Reject unexpected cross-site redirects.
            if urlsplit(response.url).hostname.removeprefix('www.') != urlsplit(url).hostname.removeprefix('www.'):
                raise RuntimeError('Redirect to a different site')
            return response.read(4_000_000).decode('utf-8', errors='replace')

    def get(self, url):
        parts = urlsplit(url)
        origin = f'{parts.scheme}://{parts.netloc}'
        if origin not in self.robots:
            parser = RobotFileParser()
            try:
                parser.parse(self.raw(origin + '/robots.txt').splitlines())
            except Exception as exc:
                raise RuntimeError(f'Cannot verify robots.txt: {exc}') from exc
            self.robots[origin] = parser
        if not self.robots[origin].can_fetch(AGENT, url):
            raise RuntimeError('Disallowed by robots.txt')
        time.sleep(1)
        return self.raw(url)


def collect(fetcher, source, root):
    queue, visited, found, errors = [root], set(), [], []
    while queue and len(visited) < 35:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        try:
            body = fetcher.get(url)
            page = Page(body)
            if url == root:
                Path('output').mkdir(exist_ok=True)
                Path(f'output/{source}-links.json').write_text(json.dumps(page.links, ensure_ascii=False, indent=2))
                Path(f'output/{source}-sample.html').write_text(body[:200000])
            for script in page.scripts:
                try:
                    data = json.loads(script)
                except ValueError:
                    continue
                for job in jobs(data):
                    row = normalize(job, source, url)
                    if row:
                        found.append(row)
            for href, label in page.links:
                target = urljoin(url, href).split('#')[0]
                if (urlsplit(target).scheme == 'https' and
                        urlsplit(target).netloc == urlsplit(root).netloc and
                        KEYWORDS.search(label + ' ' + href) and target not in visited):
                    queue.append(target)
        except Exception as exc:
            errors.append(f'{url}: {type(exc).__name__}: {exc}')
    return found, dict(source=source, pages=len(visited), postings=len(found), errors=errors,
                       coverage='Limited: linked legal vacancies with JobPosting structured data only')


def recent(row, today):
    try:
        posted = datetime.fromisoformat(row['date'].replace('Z', '+00:00')).date()
        if not today - timedelta(days=7) <= posted <= today:
            return False
        if row['expires'] and datetime.fromisoformat(row['expires'].replace('Z', '+00:00')).date() < today:
            return False
        return True
    except (ValueError, TypeError):
        return False


def render(rows, reports):
    fields = [('source', 'Сайт'), ('employer', 'Кто ищет'), ('title', 'Кого ищут'), ('requirements', 'Требования / описание'), ('city', 'Город'), ('date', 'Дата')]
    output = '<meta charset="utf-8"><h2>Новые вакансии юриста за 7 дней</h2>'
    output += '<table border="1" cellpadding="6"><tr>' + ''.join(f'<th>{label}</th>' for _, label in fields) + '<th>Ссылка</th></tr>'
    for row in rows:
        output += '<tr>' + ''.join('<td>' + html.escape(row[key]) + '</td>' for key, _ in fields)
        output += '<td><a href="' + html.escape(row['url'], quote=True) + '">Открыть</a></td></tr>'
    output += '</table><p>Найдено новых объявлений: ' + str(len(rows)) + '.</p>'
    output += '<p>Требования приведены выдержкой из объявления. Объявления без даты не включаются. Полнота охвата не гарантируется.</p><h3>Проверка источников</h3><ul>'
    for report in reports:
        output += '<li>' + html.escape(f"{report['source']}: страниц {report['pages']}, вакансий {report['postings']}, ошибок {len(report['errors'])}. {report['coverage']}")
        for error in report['errors'][:3]:
            output += '<pre>' + html.escape(error) + '</pre>'
        output += '</li>'
    return output + '</ul>'


def send(body):
    message = EmailMessage()
    message['Subject'] = 'Новые вакансии юриста — еженедельная подборка'
    message['From'] = os.environ['SMTP_FROM']
    message['To'] = os.environ.get('DIGEST_TO', 'kentukydc@gmail.com')
    message.set_content('Откройте HTML-версию письма: таблица вакансий и состояние источников.')
    message.add_alternative(body, subtype='html')
    host, port = os.environ['SMTP_HOST'], int(os.environ.get('SMTP_PORT') or '465')
    context = ssl.create_default_context()
    if port == 465:
        connection = smtplib.SMTP_SSL(host, port, context=context, timeout=30)
    else:
        connection = smtplib.SMTP(host, port, timeout=30)
        connection.ehlo()
        connection.starttls(context=context)
        connection.ehlo()
    with connection as smtp:
        smtp.login(os.environ['SMTP_USER'], os.environ['SMTP_PASSWORD'])
        smtp.send_message(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--send', action='store_true')
    parser.add_argument('--scheduled', action='store_true')
    args = parser.parse_args()
    now = datetime.now(ZoneInfo('Europe/Chisinau'))
    # Two UTC schedules cover DST; only the local 09:00 invocation runs.
    if args.scheduled and (now.weekday() != 0 or now.hour != 9):
        return
    state_path = Path('state/seen.json')
    seen = json.loads(state_path.read_text()) if state_path.exists() else {}
    rows, reports = [], []
    fetcher = Fetcher()
    for source, root in SOURCES.items():
        found, report = collect(fetcher, source, root)
        reports.append(report)
        for row in found:
            key = hashlib.sha256(row['url'].encode()).hexdigest()
            if key not in seen and recent(row, now.date()):
                rows.append(row)
                seen[key] = now.isoformat()
    Path('output').mkdir(exist_ok=True)
    body = render(rows, reports)
    Path('output/digest.html').write_text(body)
    Path('output/report.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2))
    print(json.dumps(dict(new=len(rows), sources=reports), ensure_ascii=False))
    if args.send:
        send(body)
        # Commit deduplication state only after SMTP accepts the message.
        state_path.parent.mkdir(exist_ok=True)
        state_path.write_text(json.dumps(seen, indent=2))
    if all(report['errors'] for report in reports):
        raise SystemExit('Every source reported errors; inspect output/report.json')


if __name__ == '__main__':
    main()
