import json,glob
W={'client_relevance':.30,'partner_openness':.25,'moldova_opportunity':.25,'reachability':.10,'scale':.10}
DROP={'Pearse Trust':'Поглощена Hawksford (2022); актуальность сайта не подтверждена; Hawksford уже представлен через Healy',
 'Biz Latin Hub':'Поглощена Vistra (дек. 2025) — дублирует Vistra; фокус Латинская Америка',
 'Acclime Global Business':'Ребрендинг OCRA → Acclime (2024), фокус АТР/офшоры; публичные контакты не подтверждены на собственном сайте'}
rows=[];dropped=[];seen=set()
for f in ['out/b_eu.json','out/a_uk.json','out/c_uae.json','out/d_sg.json']:
  for c in json.load(open(f)):
    key=c['name'].split(' (')[0]
    if key in seen: continue
    seen.add(key)
    c['score']=round(sum(c['scores'][k]*w for k,w in W.items()),2)
    r=next((v for k,v in DROP.items() if c['name'].startswith(k)),None)
    (dropped if r else rows).append(c)
    if r: c['drop_reason']=r
rows.sort(key=lambda c:-c['score'])
json.dump({'rows':rows,'dropped':dropped},open('merged.json','w'),ensure_ascii=False,indent=1)
for i,c in enumerate(rows,1): print(i,c['score'],c['name'],'|',c['moldova_offered'])
print(len(rows),len(dropped))
