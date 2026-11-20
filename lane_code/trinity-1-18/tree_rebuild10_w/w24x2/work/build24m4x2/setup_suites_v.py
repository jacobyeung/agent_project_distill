from pathlib import Path
import os,json
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4x2';old=L/'work/build24m4t'
for p in old.glob('*.py'):
 q=D/p.name
 if q.exists():continue
 q.write_text(p.read_text().replace('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24t',str(L)).replace('build24m4t','build24m4x2'))
for name in ('inputs','scanners','proofs'):
 for directory,dirs,files in os.walk(old/name):
  for n in files:
   p=Path(directory)/n;q=D/p.relative_to(old);q.parent.mkdir(parents=True,exist_ok=True)
   if not q.exists():os.link(p,q)
for name in ('ARM_BASE_FILES.json','ARM_BASE_SEALS.json'):
 (D/name).write_bytes((old/name).read_bytes())
print('Suite scripts relocated; fixture inputs retained')
