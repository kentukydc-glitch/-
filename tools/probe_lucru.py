"""Inspect normal public Lucru endpoints; no authentication or challenge solving."""
import concurrent.futures,json,re,sys
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from collector import Page,Tree,AGENT
TARGETS={
 'public-search-rss':'https://www.bing.com/search?format=rss&q=Lucru.md+RSS+Telegram+vacancies',
 'public-search-jurist':'https://www.bing.com/search?format=rss&q=site%3Alucru.md+jurist',
 'public-search-google':'https://www.google.com/search?q=Lucru.md+RSS+vacancies',
}

Path('output').mkdir(exist_ok=True)
def probe(item):
 name,url=item;out={'url':url}
 try:
  with urlopen(Request(url,headers={'User-Agent':AGENT}),timeout=25) as response:
   body=response.read(3000000).decode('utf-8',errors='replace')
   out.update(status=response.status,final_url=response.url,content_type=response.headers.get('Content-Type'),bytes=len(body),title=re.findall(r'<title[^>]*>(.*?)</title>',body,flags=re.S|re.I),links=Page(body).links,scripts=Page(body).scripts,text=Tree(body).root.text()[:45000])
   out['canonical']=re.findall(r'<link[^>]*rel=["\']canonical["\'][^>]*>',body,re.I)
   out['branding']=re.findall(r'<meta[^>]*(?:og:site_name|og:url)[^>]*>',body,re.I)
   clean=re.sub(r'<(script|style)\b[^>]*>.*?</\1>','',body,flags=re.S|re.I)
   Path('output',name+'.html').write_text(clean[:300000])
 except Exception as e:out['error']=str(e)
 Path('output',name+'.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(name,out.get('status'),out.get('bytes'),out.get('error',''))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(probe,TARGETS.items()))
