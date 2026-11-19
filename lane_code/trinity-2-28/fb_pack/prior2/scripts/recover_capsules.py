import json,hashlib,base64,subprocess
from pathlib import Path
W=Path.cwd();R=Path('/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/tree_rebuild10_w');record=json.loads((W/'out/INPUT_LOCATIONS.json').read_text());wanted={p['sha256']:p for p in record['missing']};found={};sources={}
def visit(x,source):
 if isinstance(x,dict):
  if isinstance(x.get('payload'),str) and isinstance(x.get('sha256'),str):
   try:raw=base64.b64decode(x['payload'],validate=True)
   except ValueError:raw=None
   if raw is not None and hashlib.sha256(raw).hexdigest()==x['sha256']:
    if x['sha256'] in wanted:
     p=W/'work/recovered'/x['sha256'];p.write_bytes(raw)
     if x['sha256']=='c0167f682bd49fce84d1ca447a64131ae1605a345f534ce61ee98aabf7bee9c8':(W/'work/recovered/card.json').write_bytes(raw)
     found[x['sha256']]=str(p);sources[x['sha256']]={'path':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
    try:visit(json.loads(raw),source)
    except (ValueError,UnicodeError):pass
  for v in x.values():
   if isinstance(v,(dict,list)):visit(v,source)
 elif isinstance(x,list):
  for v in x:
   if isinstance(v,(dict,list)):visit(v,source)
for n in subprocess.check_output(['rg','--files',str(R/'w24')],text=True).splitlines():
 p=Path(n)
 if p.suffix!='.json' or any(s in n for s in ('/tree_r1/','/s/','/reference/tree/')) or p.stat().st_size>30_000_000:continue
 try:visit(json.loads(p.read_text()),p)
 except (ValueError,UnicodeError):pass
out={'found':found,'sources':sources,'inputs':[{'path':str(W/'out/INPUT_LOCATIONS.json'),'sha256':hashlib.sha256((W/'out/INPUT_LOCATIONS.json').read_bytes()).hexdigest()},{'path':str(Path(__file__).resolve()),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}]}
(W/'out/CAPSULE_RECOVERY.json').write_text(json.dumps(out,indent=2)+'\n');print(found)
