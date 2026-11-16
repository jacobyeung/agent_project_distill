"""Seal V1f while retaining the exact V1c reference archive and family policy."""
from pathlib import Path
import difflib,sys,tarfile
B=Path(__file__).resolve().parents[1];OLD=B.parent/'03_vsti_c';sys.path.append(str(B/'code'))
from adapter import *
import engine
assert sha(B/'out/d.tar')==sha(OLD/'out/d.tar')=='9a1de8608ea0e75e2f2436259b81f0e991b2007002a59de11d85062e8384d08f'
with tarfile.open(B/'out/c.tar','w') as t:
 for p in sorted((B/'code').rglob('*')):
  if not p.is_file():continue
  info=tarfile.TarInfo(str(p.relative_to(B/'code')));info.size=p.stat().st_size;info.mtime=0;info.mode=p.stat().st_mode&0o777
  with p.open('rb') as stream:t.addfile(info,stream)
f=load(OLD/'out/FAMILY.json');f['code']=pin(B/'out/c.tar');f['code_sources']=engine.source_pins()
f['added']['c'].update(sha256=sha(B/'out/c.tar'),bytes=(B/'out/c.tar').stat().st_size,generation=None,verified=False)
dump(B/'out/FAMILY.json',f)
patch=[];changed=[]
for group in ('code','tests'):
 for p in sorted((B/group).rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(B);old=OLD/rel
  if old.exists() and old.read_bytes()==p.read_bytes():continue
  changed.append(str(rel))
  patch.extend(difflib.unified_diff(old.read_text().splitlines(True) if old.exists() else [],p.read_text().splitlines(True),fromfile='V1c/'+str(rel),tofile='V1f/'+str(rel)))
(B/'out/DIFF_vs_V1c.patch').write_text(''.join(patch))
assert [p for p in changed if p.startswith('code/')]==['code/o.py','code/sj/orch_cd/evalx/work/milestone/orchard_results.py']
old_batch=[line for line in (OLD/'code/o.py').read_text().splitlines() if '#SBATCH' in line]
assert old_batch==[line for line in (B/'code/o.py').read_text().splitlines() if '#SBATCH' in line]
dump(B/'out/PACKAGE.json',dict(code=pin(B/'out/c.tar'),family=pin(B/'out/FAMILY.json'),reference=pin(B/'out/d.tar'),changed=changed,batch_directives_identical=True))
print('Package rebuilt; only return wrapper and inherited token admission changed.')
