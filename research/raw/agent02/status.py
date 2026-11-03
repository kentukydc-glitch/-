import json
A=json.load(open('all.json'))
P1=['Accace','Eurofast','BridgeWest','Healy','Commitbiz']
P2=['The Sovereign','TMF','Uniwide','Vistra','Virtuzone']
def status(c):
  n=c['name']
  if any(n.startswith(p) for p in P1): return 'TOP-10 · Приоритет 1'
  if any(n.startswith(p) for p in P2): return 'TOP-10 · Приоритет 2'
  if n.startswith('GSL'): return 'Отложено: требуется комплаенс-проверка'
  if c['exclude']['value']: return 'Исключено'
  return 'Резерв'
for c in A: c['status']=status(c)
# agent01 mapping
m=json.load(open('../merged.json'))
a1={x['name'].split()[0].lower():x for x in m['rows']}
for c in A:
  k=c['name'].replace('The ','').split()[0].lower()
  x=a1.get(k)
  c['a1_score100']=round(x['score']*20) if x else None
json.dump(A,open('final.json','w'),ensure_ascii=False,indent=1)
for c in A: print(c['status'],'|',c['name'],c['total'],c['a1_score100'])
