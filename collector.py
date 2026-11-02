"""Weekly Moldova legal vacancies digest; Python 3.11+, Playwright for JavaScript sources."""
import argparse
import csv
import hashlib
import html
import json
import os
import re
import smtplib
import ssl
import time
import textwrap
import xml.etree.ElementTree as ET
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
    'Delucru.md': 'https://www.delucru.md/jobs/law',
    'Jobber.md': 'https://jobber.md/en/jobs/?query=jurist',
    '999.md': 'https://999.md/ro/list/work/jurisprudence?tab=vacancy&o_16_1=983',
}
KEYWORDS = re.compile(r'юрист|юрисконсульт|адвокат|\bjurist\w*|\bjurisconsult\w*|juridic|\bavocat\w*|\blawyer\b|legal\s+(?:counsel|expert|advisor|officer|specialist)', re.I)
DISCOVERY = re.compile(KEYWORDS.pattern + r'|juridic|\blaw\b', re.I)
AGENT = 'LegalVacancyDigest/1.0'


class Node:
    def __init__(self, tag='', attrs=None, parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs or []), parent, []

    def text(self):
        return plain(' '.join(child.text() if isinstance(child, Node) else child for child in self.children))

    def find(self, predicate):
        if predicate(self):
            yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.find(predicate)

    def has_class(self, name):
        return name in self.attrs.get('class', '').split()


class Tree(HTMLParser):
    def __init__(self, body):
        super().__init__()
        self.root = Node()
        self.stack = [self.root]
        self.feed(body)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, value):
        if self.stack[-1].tag not in ('script', 'style'):
            self.stack[-1].children.append(value)


def delu_job(body, url, today=None):
    if not re.search(r'/job/\d+', urlsplit(url).path):
        return None
    tree = Tree(body).root
    def first(predicate):
        return next(tree.find(predicate), Node())
    title = first(lambda n: n.has_class('job-item-title')).text()
    if not KEYWORDS.search(title):
        return None
    employer = first(lambda n: n.tag == 'a' and '/company/' in n.attrs.get('href', '')).text()
    description = first(lambda n: n.attrs.get('id') == 'job-description').text()
    requirements = re.search(r'cerin[țţt]e|требования|requirements|calificări', description, re.I)
    if requirements:
        description = description[requirements.start():]
    date_text = first(lambda n: n.has_class('page-item-date')).text()
    posted = ''
    match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', date_text)
    today = today or datetime.now(ZoneInfo('Europe/Chisinau')).date()
    if match:
        day, month, year = match.groups()
        posted = f'{year}-{month}-{day}'
    elif re.search(r'\bazi\b|сегодня', date_text, re.I):
        posted = today.isoformat()
    elif re.search(r'\bieri\b|вчера', date_text, re.I):
        posted = (today - timedelta(days=1)).isoformat()
    else:
        relative = re.search(r'(\d+)\s*(?:zile|дн)', date_text, re.I)
        if relative:
            posted = (today - timedelta(days=int(relative[1]))).isoformat()
    city_label = first(lambda n: n.tag == 'div' and n.text() == 'Oraș:')
    city = city_label.parent.text().removeprefix('Oraș:').strip() if city_label.parent else ''
    return dict(source='Delucru.md', employer=employer, title=title, requirements=textwrap.shorten(description, width=350, placeholder='…'), city=city, date=posted, expires='', url=url)


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
    description = plain(job.get('qualifications') or job.get('skills') or job.get('description'))
    required = re.search(r'cerin[țţt]e|требования|requirements|qualifications', description, re.I)
    if required:
        description = description[required.start():]
    return dict(source=source, employer=plain(org.get('name')) if isinstance(org, dict) else plain(org), title=title,
                requirements=textwrap.shorten(description, width=350, placeholder='…'),
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

    def check_robots(self, url):
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

    def get(self, url):
        self.check_robots(url)
        time.sleep(1)
        return self.raw(url)

    def sitemap_candidates(self, root):
        parts = urlsplit(root)
        origin = f'{parts.scheme}://{parts.netloc}'
        parser = self.robots.get(origin)
        pending = list(parser.site_maps() or []) if parser else []
        visited, candidates = set(), []
        while pending and len(visited) < 4:
            url = pending.pop(0)
            if url in visited or urlsplit(url).netloc.removeprefix('www.') != parts.netloc.removeprefix('www.'):
                continue
            visited.add(url)
            try:
                document = ET.fromstring(self.get(url))
                links = [node.text.strip() for node in document.iter() if node.tag.rsplit('}', 1)[-1] == 'loc' and node.text]
                if document.tag.rsplit('}', 1)[-1] == 'sitemapindex':
                    pending.extend(sorted(links, key=lambda value: not bool(re.search('job|vacan|en|ro', value, re.I))))
                else:
                    candidates.extend(link for link in links if DISCOVERY.search(link))
            except (OSError, ValueError, RuntimeError, ET.ParseError):
                continue
        return candidates


class BrowserFetcher(Fetcher):
    """Use a normal Chromium browser where listings require JavaScript."""
    def __init__(self):
        super().__init__()
        self.engine = self.browser = None

    def get(self, url):
        domain = urlsplit(url).hostname.removeprefix('www.')
        if domain not in {'jobber.md', '999.md', 'lucru.md'} or urlsplit(url).path.endswith(('.xml', '.xml.gz')):
            return super().get(url)
        self.check_robots(url)
        if self.browser is None:
            try:
                from playwright.sync_api import sync_playwright
            except ImportError as exc:
                raise RuntimeError('Browser sources require playwright and Chromium; see README') from exc
            self.engine = sync_playwright().start()
            self.browser = self.engine.chromium.launch()
        page = self.browser.new_page()
        try:
            response = page.goto(url, wait_until='domcontentloaded', timeout=45000)
            page.wait_for_timeout(6500)
            if urlsplit(page.url).hostname.removeprefix('www.') != domain:
                raise RuntimeError('Unexpected cross-site browser redirect')
            body = page.content()
            title = page.title()
            if response and response.status >= 400 or re.search(r'403 Forbidden|Access denied|Just a moment|Verify you are human', title, re.I):
                raise RuntimeError('Site denied browser access; source unavailable')
            return body
        finally:
            page.close()

    def close(self):
        if self.browser:
            self.browser.close()
        if self.engine:
            self.engine.stop()
        self.browser = self.engine = None


def collect(fetcher, source, root):
    queue, visited, found, errors = [root], set(), [], []
    verified_board = False
    available_positions = 0
    while queue and len(visited) < 12:
        url = queue.pop(0)
        visit_key = url
        if source == 'Jobber.md':
            job_id = re.search(r'/job/[^/]+/(\d+)/?$', urlsplit(url).path)
            if job_id:
                visit_key = 'jobber:' + job_id[1]
        if visit_key in visited:
            continue
        visited.add(visit_key)
        try:
            body = fetcher.get(url)
            if not body.strip():
                raise RuntimeError('Empty response; source not verified')
            page = Page(body)
            if source == 'Jobber.md' and url == root:
                verified_board = bool(re.search(r'jobs for the query|No jobs|No vacancies', Tree(body).root.text(), re.I))
            if url == root and source not in {'Jobber.md', '999.md', 'Lucru.md'} and hasattr(fetcher, 'sitemap_candidates'):
                queue.extend(fetcher.sitemap_candidates(root))
            if source == 'Delucru.md':
                row = delu_job(body, url)
                if row:
                    row['source'] = source
                    found.append(row)
            if source == '999.md' and url == root:
                verified_board = bool(re.search(r'Jurist, consilier juridic', Tree(body).root.text(), re.I) and re.search(r'Joburi.*CV-uri', Tree(body).root.text(), re.I))
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
                if source == '999.md' and not re.search(r'^/ro/\d+$', urlsplit(target).path):
                    continue
                if source == 'Jobber.md' and not re.search(r'/en/job/[^/]+/\d+/?$', urlsplit(target).path):
                    continue
                if (urlsplit(target).scheme == 'https' and
                        urlsplit(target).netloc.removeprefix('www.') == urlsplit(root).netloc.removeprefix('www.') and
                        DISCOVERY.search(label + ' ' + href) and target not in visited and
                        not (source == 'Delucru.md' and '/ru/' in target)):
                    queue.append(target)
        except Exception as exc:
            errors.append(f'{url}: {type(exc).__name__}: {exc}')
    if not found and not verified_board:
        errors.append('No supported vacancy data extracted; coverage NOT verified')
    return found, dict(source=source, pages=len(visited), postings=len(found), errors=errors,
                       available_positions=available_positions,
                       verified=bool(found) or verified_board,
                       coverage={'Delucru.md': 'Вакансии раздела «Юридические»', 'Jobber.md': 'Поиск jurist; браузерная загрузка, отбор юридических должностей', '999.md': 'Раздел вакансий юриста; только объявления работодателей', 'Lucru.md': 'Доступ через обычный браузер'}.get(source, 'Структурированные вакансии'))


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
        output += '<tr>' + ''.join('<td>' + html.escape(row[key] + (' (обнаружено)' if key == 'date' and row.get('date_basis') == 'first_seen' else '')) + '</td>' for key, _ in fields)
        output += '<td><a href="' + html.escape(row['url'], quote=True) + '">Открыть</a></td></tr>'
    output += '</table><p>Найдено новых объявлений: ' + str(len(rows)) + '.</p>'
    output += '<p>Требования приведены выдержкой из объявления. Метка «обнаружено» означает дату первого обнаружения: сайт не указал дату публикации. Полнота охвата не гарантируется.</p><h3>Проверка источников</h3><ul>'
    for report in reports:
        output += '<li>' + html.escape(f"{report['source']}: страниц {report['pages']}, вакансий {report['postings']}, ошибок {len(report['errors'])}. {report['coverage']}")
        for error in report['errors'][:3]:
            output += '<pre>' + html.escape(error) + '</pre>'
        output += '</li>'
    return output + '</ul>'


def send(body):
    def stage(name):
        Path('output').mkdir(exist_ok=True)
        Path('output/smtp-stage.json').write_text(json.dumps(dict(stage=name)))
    message = EmailMessage()
    message['Subject'] = 'Новые вакансии юриста — еженедельная подборка'
    message['From'] = os.environ['SMTP_FROM']
    message['To'] = os.environ.get('DIGEST_TO', 'kentukydc@gmail.com')
    message.set_content('Откройте HTML-версию письма: таблица вакансий и состояние источников.')
    message.add_alternative(body, subtype='html')
    host, port = os.environ['SMTP_HOST'], int(os.environ.get('SMTP_PORT') or '465')
    context = ssl.create_default_context()
    stage('connect')
    if port == 465:
        connection = smtplib.SMTP_SSL(host, port, context=context, timeout=30)
    else:
        connection = smtplib.SMTP(host, port, timeout=30)
        connection.ehlo()
        connection.starttls(context=context)
        connection.ehlo()
    with connection as smtp:
        stage('authenticate')
        password = os.environ['SMTP_PASSWORD']
        if host == 'smtp.gmail.com':
            normalized = ''.join(password.split())
            Path('output/password-format.json').write_text(json.dumps(dict(valid_app_password_format=bool(re.fullmatch('[a-zA-Z]{16}', normalized)), whitespace_removed=normalized != password)))
            smtp.ehlo_or_helo_if_needed()
            smtp.user = os.environ['SMTP_USER'].strip()
            smtp.password = normalized
            smtp.auth('LOGIN', smtp.auth_login, initial_response_ok=False)
        else:
            smtp.login(os.environ['SMTP_USER'], password)
        stage('send_message')
        smtp.send_message(message)
        stage('accepted')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--send', action='store_true')
    parser.add_argument('--scheduled', action='store_true')
    parser.add_argument('--input-json', help='Use previously collected vacancies for a delivery check')
    args = parser.parse_args()
    now = datetime.now(ZoneInfo('Europe/Chisinau'))
    # Two UTC schedules cover DST; only the local 09:00 invocation runs.
    if args.scheduled and (now.weekday() != 0 or now.hour != 9):
        return
    state_path = Path('state/seen.json')
    seen = json.loads(state_path.read_text()) if state_path.exists() else {}
    rows, reports = [], []
    fetcher = BrowserFetcher()
    if args.input_json:
        cached = json.loads(Path(args.input_json).read_text())
        batches = [(cached, dict(source='Previously collected vacancies', pages=0, postings=len(cached), errors=[], coverage='Cached data for delivery verification'))]
    else:
        batches = (collect(fetcher, source, root) for source, root in SOURCES.items())
    for found, report in batches:
        reports.append(report)
        for row in found:
            key = hashlib.sha256(row['url'].encode()).hexdigest()
            if key not in seen and recent(row, now.date()):
                rows.append(row)
                seen[key] = now.isoformat()
    fetcher.close()
    Path('output').mkdir(exist_ok=True)
    body = render(rows, reports)
    Path('output/digest.html').write_text(body)
    Path('output/vacancies.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    with Path('output/vacancies.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        fields = ['source', 'employer', 'title', 'requirements', 'city', 'date', 'url']
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writerow(dict(zip(fields, ['Сайт', 'Кто ищет', 'Кого ищут', 'Краткие требования', 'Город', 'Дата на сайте', 'Ссылка'])))
        writer.writerows(rows)
    Path('output/report.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2))
    print(json.dumps(dict(new=len(rows), sources=reports), ensure_ascii=False))
    if args.send:
        required = ['SMTP_HOST', 'SMTP_USER', 'SMTP_PASSWORD', 'SMTP_FROM']
        missing = [name for name in required if not os.environ.get(name)]
        # Record only safe metadata, never credentials or SMTP conversation.
        try:
            if missing:
                raise ValueError('Missing SMTP settings: ' + ', '.join(missing))
            send(body)
        except Exception as exc:
            Path('output/delivery.json').write_text(json.dumps(dict(status='failed', missing_settings=missing, error_type=type(exc).__name__, smtp_code=getattr(exc, 'smtp_code', None)), indent=2))
            raise
        Path('output/delivery.json').write_text(json.dumps(dict(status='accepted_by_smtp', recipient=os.environ.get('DIGEST_TO', 'kentukydc@gmail.com')), indent=2))
        # Commit deduplication state only after SMTP accepts the message.
        state_path.parent.mkdir(exist_ok=True)
        state_path.write_text(json.dumps(seen, indent=2))
    if all(report['errors'] for report in reports):
        raise SystemExit('Every source reported errors; inspect output/report.json')


if __name__ == '__main__':
    main()
