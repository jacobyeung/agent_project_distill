from common import *
import subprocess
track(__file__);cfg=config();wanted={}
def collect(v):
 if isinstance(v,dict):
  if 'path' in v and 'sha256' in v:wanted[v['sha256']]=v
  for x in v.values():collect(x)
 elif isinstance(v,list):
  for x in v:collect(x)
collect(cfg);found={};sources={}
def visit(v,p):
 if isinstance(v,dict):
  if v.get('encoding')=='base64-json' and 'payload' in v:
   raw=base64.b64decode(v['payload'],validate=True);h=hashlib.sha256(raw).hexdigest()
   if h!=v['sha256']:raise ValueError('capsule mismatch')
   if h in wanted:
    dest=W/'work/recovered'/h;dest.parent.mkdir(exist_ok=True)
    if not dest.exists():dest.write_bytes(raw)
    found[h]=str(dest);sources[h]=dict(path=str(p),sha256=P.sha256(p))
   try:visit(json.loads(raw),p)
   except (ValueError,UnicodeError):pass
  for x in v.values():
   if isinstance(x,(dict,list)):visit(x,p)
 elif isinstance(v,list):
  for x in v:
   if isinstance(x,(dict,list)):visit(x,p)
paths=subprocess.check_output(['rg','--files',str(RO/'orch_n30/tree_rebuild10_w/w24'),'-g','*.json'],text=True).splitlines()
for name in paths:
 p=Path(name)
 if any(x in name for x in ('/tree_r1/','/s/','/reference/tree/')) or p.stat().st_size>30_000_000:continue
 raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest()
 if h in wanted:found[h]=str(p);sources[h]=dict(path=str(p),sha256=h)
 try:visit(json.loads(raw),p)
 except (ValueError,UnicodeError):pass
# Exact receipt copy at the source store is another named source candidate.
p=RO/'n30_mirror/rows_r1/out/a2_vqa_v7/vqa/receipt.json';h=P.sha256(p)
if h in wanted:found[h]=str(p);sources[h]=dict(path=str(p),sha256=h)
for p in sources.values():track(p['path'],p['sha256'])
write('out/RECOVERED_METADATA.json',dict(found=found,sources=sources))
print('recovered',len(found),'of',len(wanted));print('\n'.join(wanted[h]['path'] for h in found))
