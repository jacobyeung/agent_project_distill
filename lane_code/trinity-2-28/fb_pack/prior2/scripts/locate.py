import json,hashlib,subprocess,base64
from pathlib import Path
W=Path.cwd();RO=Path('/scratch/jjyeung/orch_n30/fb_pack/ro');PR=RO/'orch_n30/fb_pack/prior/out/PRIOR_DELTA.json'
items=json.loads(PR.read_text())['inputs']; missing={p['sha256']:p for p in items if not (RO/p['path'].removeprefix('/scratch/jjyeung/')).is_file()}
found={};sizes={p.get('bytes') for p in missing.values()}
root=RO/'orch_n30/tree_rebuild10_w'
files=subprocess.check_output(['rg','--files',str(root)],text=True).splitlines()
for name in files:
 p=Path(name)
 if p.stat().st_size in sizes:
  h=hashlib.sha256(p.read_bytes()).hexdigest()
  if h in missing:found[h]=str(p)
# The kit's content-addressed pin pool may embed original bytes in capsules.
for name in files:
 p=Path(name)
 if p.suffix!='.json' or not p.stat().st_size<10_000_000:continue
 if '/tree_r1/' in name or '/s/' in name or '/reference/tree/' in name:continue
 try:x=json.loads(p.read_text())
 except (ValueError,UnicodeError):continue
 while isinstance(x,dict) and x.get('encoding')=='base64-json':
  raw=base64.b64decode(x['payload']);h=hashlib.sha256(raw).hexdigest()
  if h!=x['sha256']:break
  if h in missing:
   d=W/'work/recovered'/h;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(raw);found[h]=str(d)
  x=json.loads(raw)
record={'inputs':[{'path':str(PR),'sha256':hashlib.sha256(PR.read_bytes()).hexdigest()},{'path':str(Path(__file__).resolve()),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}],'found':found,'missing':[p for h,p in missing.items() if h not in found]}
(W/'out/INPUT_LOCATIONS.json').write_text(json.dumps(record,indent=2)+'\n')
print('found',found); print('MISSING',[(p['path'],p['sha256'][:8]) for p in record['missing']])
