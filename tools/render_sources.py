"""Inspect normal browser-rendered public job listings, respecting robots.txt."""
import asyncio,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from collector import Fetcher,Page,Tree
from playwright.async_api import async_playwright
TARGETS={
 'browser-jobber':'https://jobber.md/en/jobs/',
 'browser-999':'https://999.md/ro/search?query=jurist&o_16_1=983',
 'browser-lucru':'https://www.lucru.md/ro/jobs-moldova',
}
async def main():
 Path('output').mkdir(exist_ok=True)
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  for name,url in TARGETS.items():
   result={'url':url}
   page=await browser.new_page()
   try:
    Fetcher().get(url)  # Includes the robots permission check.
    response=await page.goto(url,wait_until='domcontentloaded',timeout=45000)
    await page.wait_for_timeout(7000)
    if name=='browser-jobber':
     box=page.get_by_placeholder('Name of the vacancy')
     if await box.count():
      await box.fill('jurist')
      await box.press('Enter')
      await page.wait_for_timeout(6000)
    body=await page.content()
    parsed=Page(body)
    result.update(final_url=page.url,status=response.status if response else None,text=Tree(body).root.text()[:80000],links=parsed.links,scripts=parsed.scripts)
    clean=re.sub(r'<(style|script)\b[^>]*>.*?</\1>','',body,flags=re.S|re.I)
    Path('output',name+'.html').write_text(clean[:1000000])
   except Exception as e:result['error']=str(e)
   Path('output',name+'.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
   print(name,result.get('status'),result.get('error',''))
   await page.close()
  await browser.close()
asyncio.run(main())
