"""Preserve completed round-5 fixture files while sharing identical immutable bytes."""
import hashlib,json,os,subprocess,uuid
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');root=L/'work/test-artifacts'
m=json.loads((L/'out_round5/patches/MANIFEST.json').read_text());base=Path(m['verification_root'])/'src'
refs={};changed=[]
for rel,pin in m['base_pin']['inventory'].items():
 p=base/rel
 if p.stat().st_size>=1024:refs[(p.stat().st_size,pin)]=p
# Only completed development fixtures, before the full suite started at 14:11:40 UTC.
from datetime import datetime,timezone
lo=datetime(2026,11,19,13,56,45,tzinfo=timezone.utc).timestamp()
hi=datetime(2026,11,19,14,11,40,tzinfo=timezone.utc).timestamp()
for d in root.iterdir():
 if not d.is_dir() or not lo<=d.stat().st_mtime<hi:continue
 for p in d.rglob('*'):
  if p.is_symlink() or not p.is_file() or p.stat().st_size<1024:continue
  raw=p.read_bytes();key=(len(raw),hashlib.sha256(raw).hexdigest());ref=refs.get(key)
  if ref is None:refs[key]=p;continue
  if p.stat().st_ino==ref.stat().st_ino:continue
  if ref.read_bytes()!=raw:raise ValueError('Digest collision')
  temp=p.with_name(p.name+'.share'+uuid.uuid4().hex)
  os.link(ref,temp);os.replace(temp,p)
  assert p.read_bytes()==raw
  changed.append(dict(path=str(p),source=str(ref),sha256=key[1],bytes=key[0]))
(L/'out/checks/FIXTURE_STORAGE5.json').write_text(json.dumps(dict(files_preserved=True,replacements=changed),indent=2)+'\n')
print('Preserved bytes at',len(changed),'fixture paths; shared identical inodes. No path removed.')
print(subprocess.check_output(['du','-sb',str(L)],text=True).strip())
