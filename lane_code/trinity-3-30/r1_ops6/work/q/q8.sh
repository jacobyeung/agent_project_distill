export TZ=UTC
P=/project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820
python3 -B - $P <<'PY'
import json,sys,os
P=sys.argv[1]
def walk(o,path=''):
  out=[]
  if isinstance(o,dict):
    for k,v in o.items():
      if k in ('retained','seen','removed','admitted','rows','count','matched','listed','eligible','total') and isinstance(v,int): out.append((path+'.'+k,v))
      out+=walk(v,path+'.'+k)
  elif isinstance(o,list) and len(o)<60:
    for i,v in enumerate(o): out+=walk(v,path+'[%d]'%i)
  return out
for f in ('vqa/receipt.json','routing/receipt.json','pointing/receipt.json','prepared/receipt.json','result.json'):
  try: d=json.load(open(os.path.join(P,f)))
  except Exception as e: print(f,'ERR',e); continue
  print('==',f,os.path.getsize(os.path.join(P,f)),'keys',list(d)[:15] if isinstance(d,dict) else type(d))
  for k,v in walk(d)[:40]: print('  ',k[:120],v)
PY
