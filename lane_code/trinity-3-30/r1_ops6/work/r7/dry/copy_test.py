import json,sys,os,io,hashlib,tarfile
from pathlib import Path
XR,STEP,CKN=sys.argv[1:4]; CAP=64<<20; TOTAL=1536<<20
def sha(p):
  h=hashlib.sha256()
  with open(p,'rb') as f:
    for b in iter(lambda:f.read(1<<20),b''): h.update(b)
  return h.hexdigest()
seen={}; skipped=[]; queue=[]
def add(path,want=None,why='',level=0):
  p=str(path)
  if p in seen: return
  if not os.path.isfile(p): skipped.append(dict(path=p,reason='absent',why=why)); seen[p]=None; return
  n=os.path.getsize(p)
  if n>CAP: skipped.append(dict(path=p,reason='over 64 MB',bytes=n,why=why)); seen[p]=None; return
  s=sha(p); seen[p]=dict(path=p,bytes=n,sha256=s,pin=want,match=(want is None or want==s),why=why)
  if p.endswith('.json') and level<3 and os.path.basename(p)!='frames.json': queue.append((p,level+1))
def walk(v,why,level):
  if isinstance(v,dict):
    if isinstance(v.get('path'),str) and isinstance(v.get('sha256'),str) and v['path'].startswith('/'):
      add(v['path'],v['sha256'],why,level)
    for x in v.values(): walk(x,why,level)
  elif isinstance(v,list):
    for x in v: walk(x,why,level)
M=XR+'/m'+STEP
for f in ('artifact.json','RP.json','h.json'): add(M+'/'+f,None,'milestone')
for f in ('binding.json','attempt_171377.json','inputs/data_receipt.json','inputs/first_step_171377.json',
          'inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/config.json'): add(XR+'/'+f,None,'run')
if CKN:
  c=XR+'/'+CKN; add(c+'/complete.json',None,'checkpoint')
  try:
    for name,pin in json.load(open(c+'/complete.json')).get('files',{}).items():
      if not name.startswith('shards/') and name!='replicated.pt': add(c+'/'+name,pin.get('sha256'),'checkpoint file')
  except Exception as e: skipped.append(dict(path=c,reason='complete.json unreadable '+repr(e)))
done=set()
while queue:
  p,level=queue.pop(0)
  if p in done: continue
  done.add(p)
  try: v=json.load(open(p))
  except Exception: continue
  walk(v,'pinned by '+p,level)
  if len(done)>400: break
items=[v for v in seen.values() if v]; total=sum(v['bytes'] for v in items)
man=dict(schema='r7-handover-small-files-v1',run='6ed2c7aa',step=int(STEP),checkpoint=CKN,files=items,skipped=skipped,bytes=total)
if total>TOTAL: man['truncated']=True
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as t:
  raw=json.dumps(man,indent=1,sort_keys=True).encode(); ti=tarfile.TarInfo('MANIFEST.json'); ti.size=len(raw); t.addfile(ti,io.BytesIO(raw))
  acc=0
  for v in items:
    acc+=v['bytes']
    if acc>TOTAL: break
    t.add(v['path'],arcname='files'+v['path'],recursive=False)
print('files',len(items),'bytes',total,'skipped',len(skipped),'mismatch',sum(1 for v in items if not v['match']),file=sys.stderr)
