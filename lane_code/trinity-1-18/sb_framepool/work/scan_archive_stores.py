import json,hashlib,sqlite3
from pathlib import Path
from scan_rows import scan,sha
es=json.load(open('work/all_archive_catalog.json'))['entries'];out=[]
Path('work/archive_stores').mkdir(exist_ok=True)
for e in es:
 if not e['name'].endswith('.sqlite') or e['size']<1000000 or '/tmp' in e['name']:continue
 p=Path('work/archive_stores')/(hashlib.sha256((e['archive']+'::'+e['name']).encode()).hexdigest()+'.sqlite')
 with open(e['archive'],'rb') as f:
  f.seek(e['offset']);p.write_bytes(f.read(e['size']))
 h=sha(p)
 with sqlite3.connect('file:'+str(p)+'?mode=ro&immutable=1',uri=True) as db:
  result=scan((i,json.loads(r)) for i,r in db.execute('select i,row from rows order by i'))
 result.update(source={'path':e['archive']+'::'+e['name'],'sha256':h,'bytes':e['size']},kind='archive_row_store',copies=[],command='/usr/bin/python3 work/scan_archive_stores.py');out.append(result)
 print(e['name'],result['rows'],result['hits'],result['unresolved_rows'],flush=True)
Path('work/archive_store_results.json').write_text(json.dumps(dict(inputs={p:{'sha256':sha(p)} for p in ['work/all_archive_catalog.json','work/captures.json','/scratch/jjyeung/orch_n30/sb_alias2/out/TIERED_ALIAS_MAP.json']},streams=out),indent=2)+'\n')
