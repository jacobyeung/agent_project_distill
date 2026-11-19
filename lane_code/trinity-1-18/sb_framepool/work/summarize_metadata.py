import json,hashlib,collections
from pathlib import Path
reg=json.load(open('work/metadata_fixed.json'))['files'];summ=[];errors=[]
for h,e in reg.items():
 try:
  if e['kind']=='json':
   d=json.load(open(e['blob']))
   if isinstance(d,dict):
    summary=dict(type='dict',keys=list(d)[:50],schema=d.get('schema'))
    if isinstance(d.get('streams'),dict):summary['streams']={k:v for k,v in d['streams'].items()}
   elif isinstance(d,list):summary=dict(type='list',count=len(d),sample=d[:1])
   else:summary=dict(type=type(d).__name__)
  elif e['kind']=='jsonl':
   with open(e['blob']) as f:line=next((l for l in f if l.strip()),'')
   summary=dict(type='jsonl',sample=json.loads(line) if line else None)
  else:continue
  summ.append(dict(sha256=h,locations=e['locations'],**summary))
 except Exception as ex:errors.append(dict(sha256=h,locations=e['locations'],error=str(ex)))
Path('work/metadata_summary.json').write_text(json.dumps(dict(inputs={'work/metadata_fixed.json':{'sha256':hashlib.sha256(Path('work/metadata_fixed.json').read_bytes()).hexdigest()}},files=summ,errors=errors)))
print('parsed',len(summ),'errors',len(errors))
for e in summ:
 loc=e['locations'][0]
 if 'streams' in e and any(x in loc for x in ('/prepared/receipt','/fx/k/','/w12/')):print(e['sha256'][:12],loc,{k:v.get('count') if isinstance(v,dict) else v for k,v in e['streams'].items()})
