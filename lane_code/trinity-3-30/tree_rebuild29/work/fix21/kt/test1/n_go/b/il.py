import hashlib,json,os,sys
from pathlib import Path
# Init links for ranks 1-3. Their load reads the init artifact's own paths for the weight folder and the head file
# (verify off, no relocation); those paths lie in the donor run's folder under the mount's runs folder, which the job
# backs with its empty run folder. Each becomes a link to the staged copy that the persisted-file map names by
# sha256, the copy rank 0 authenticates. Refuses by name; never replaces an existing entry.
# Usage: il.py <job config v.json> <mount root>
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def refuse(code,detail):
 print(json.dumps(dict(event='init_links',status='REFUSE',code=code,detail=detail)),flush=True);raise SystemExit(3)
if len(sys.argv)!=3:refuse('E90','usage')
cfg=json.loads(Path(sys.argv[1]).read_text());runs=Path(sys.argv[2])/'runs'
spec=cfg.get('init_artifact') or {};pf=(cfg.get('r1_training') or {}).get('persisted_files')
if not isinstance(pf,dict) or not pf:refuse('E91','persisted_files missing')
pin=spec.get('artifact') or {}
if pin.get('sha256') not in pf:refuse('E92','init artifact pin not in persisted_files')
ap=Path(pf[pin['sha256']])
if not ap.is_file() or sha(ap)!=pin['sha256']:refuse('E93','init artifact target missing or differs')
artifact=json.loads(ap.read_text())
def target(key):
 p=artifact.get(key) or {}
 if not isinstance(p.get('path'),str) or p.get('sha256') not in pf:refuse('E94',key+' pin missing or not in persisted_files')
 t=Path(pf[p['sha256']])
 if not t.is_file():refuse('E95',key+' target missing')
 got=sha(t)
 if got!=p['sha256']:refuse('E96',key+' target differs')
 return Path(p['path']),t,got
fw_raw,fw_t,fw_h=target('full_weights');hd_raw,hd_t,hd_h=target('heads')
manifest=json.loads(fw_t.read_text())
names=[manifest['index']['name'],*(f['name'] for f in manifest['files'])]
for n in names:
 if not (fw_t.parent/n).is_file():refuse('E97','full_weights member missing: '+n)
links=[(fw_raw.parent,fw_t.parent),(hd_raw,hd_t)]
for raw,dest in links:
 if not raw.is_absolute() or not raw.is_relative_to(runs) or '..' in raw.parts or raw==runs:refuse('E98','raw path outside the runs folder')
 if os.path.lexists(raw):
  if not raw.is_symlink() or os.readlink(raw)!=str(dest):refuse('E99','raw path exists and is not this link')
 else:
  raw.parent.mkdir(parents=True,exist_ok=True);os.symlink(str(dest),raw)
 if os.readlink(raw)!=str(dest) or raw.resolve()!=dest.resolve():refuse('E89','link does not resolve to its target')
print(json.dumps(dict(event='init_links',status='OK',
 full_weights=dict(link=str(fw_raw.parent),readlink=os.readlink(fw_raw.parent),manifest_sha256=fw_h,members=len(names)),
 heads=dict(link=str(hd_raw),readlink=os.readlink(hd_raw),sha256=hd_h))),flush=True)
