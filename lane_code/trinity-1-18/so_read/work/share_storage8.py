"""Bounded local sharing of immutable completed fixtures; preserve all paths/bytes."""
import hashlib,json,os,subprocess,uuid
from datetime import datetime,timezone
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');root=L/'work/test-artifacts'
cut=datetime(2026,11,19,17,30,31,tzinfo=timezone.utc).timestamp()
m=json.loads((L/'out_round8/patches/MANIFEST.json').read_text());base=Path(m['verification_root'])/'src'
refs={}
for rel,pin in m['base_pin']['inventory'].items():
 p=base/rel
 if p.stat().st_size>=1024:refs[(p.stat().st_size,pin)]=p
for p in (L/'work/round8-before-u0').rglob('*'):
 if p.is_file() and p.stat().st_size>=1024:refs[(p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())]=p
count=saved=read_bytes=0
for d in sorted(root.iterdir(),key=lambda p:p.stat().st_mtime,reverse=True):
 if d.stat().st_mtime>=cut or not d.is_dir():continue
 for p in d.rglob('*'):
  if p.is_symlink() or not p.is_file():continue
  st=p.stat()
  if st.st_nlink>1 or st.st_size<1024:continue
  if read_bytes+st.st_size>100_000_000:continue
  raw=p.read_bytes();read_bytes+=len(raw);key=(len(raw),hashlib.sha256(raw).hexdigest());ref=refs.get(key)
  if ref is None:refs[key]=p
  elif ref!=p and ref.stat().st_ino!=st.st_ino:
   assert ref.read_bytes()==raw
   temp=p.with_name(p.name+'.share8'+uuid.uuid4().hex)
   os.link(ref,temp);os.replace(temp,p)
   count+=1;saved+=len(raw)
  if saved>=60_000_000 or read_bytes>=99_000_000:break
 if saved>=60_000_000 or read_bytes>=99_000_000:break
size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0])
value=dict(paths_preserved=True,changed_files=count,unique_bytes_shared=saved,read_bytes=read_bytes,workspace_bytes=size,scope='completed pre-task fixtures only; replacements checked byte-for-byte; bounded 100 MB local candidate reads')
(L/'out/checks/STORAGE8.json').write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
print(json.dumps(value,sort_keys=True))
