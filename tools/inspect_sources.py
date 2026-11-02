"""Read public source markup for adapter development; no mail or secrets."""
import concurrent.futures
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collector import Fetcher, Page, Tree

TARGETS = {
 'lucru-root': 'https://www.lucru.md/',
 'lucru-ro': 'https://www.lucru.md/ro',
 'lucru-jobs': 'https://www.lucru.md/ro/jobs-moldova',
 'jobber-jobs': 'https://jobber.md/en/jobs/',
 'jobber-search': 'https://jobber.md/en/jobs/?search=jurist',
 '999-search': 'https://999.md/ro/search?query=jurist&o_16_1=983',
 '999-work': 'https://999.md/ro/work',
 'muncitorul-vacancies': 'https://muncitorul.md/ro/posturi_vacante',
 'top-juridic': 'https://www.topangajatori.md/juridic',
}

def inspect(item):
 name,url=item
 f=Fetcher()
 result={'url':url}
 try:
  body=f.get(url)
  page=Page(body)
  result.update(bytes=len(body), links=page.links, forms=re.findall(r'<form[^>]*>|<input[^>]*>',body), scripts=page.scripts, text=Tree(body).root.text()[:70000])
  clean=re.sub(r'<(style|script)\b[^>]*>.*?</\1>', '',body, flags=re.S|re.I)
  Path('output',name+'.html').write_text(clean[:700000])
  result['inline_data']=[s[:800000] for s in re.findall(r'<script[^>]*>(.*?)</script>',body,flags=re.S|re.I) if '__next_f' in s or 'JobPosting' in s]
 except Exception as e:result['error']=str(e)
 Path('output',name+'.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 print(name, result.get('bytes'),result.get('error',''))

Path('output').mkdir(exist_ok=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(inspect,TARGETS.items()))
