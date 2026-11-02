"""Inspect publication-date metadata on the three reported public vacancies."""
import concurrent.futures,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from collector import Fetcher,Page,Tree
Path('output').mkdir(exist_ok=True)
def inspect(item):
 job,lang=item;name=f'date-{job}-{lang}';url=f'https://www.delucru.md/{"ru/" if lang=="ru" else ""}job/{job}';out={'url':url}
 try:
  body=Fetcher().get(url);page=Page(body)
  out.update(scripts=page.scripts,dates=[body[max(0,m.start()-100):m.end()+180] for m in re.finditer(r'datePosted|datePublished|dateCreated|created_at|published_at|dateModified|updated_at|datetime=|publicationDate',body,re.I)],meta=re.findall(r'<meta[^>]*>',body,re.I),text=Tree(body).root.text()[:45000])
  clean=re.sub(r'<style\b[^>]*>.*?</style>','',body,flags=re.S|re.I)
  Path('output',name+'.html').write_text(clean)
 except Exception as e:out['error']=str(e)
 Path('output',name+'.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(name,out.get('error',''))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(inspect,[(j,l) for j in ('114007','112801','115686') for l in ('ro','ru')]))
