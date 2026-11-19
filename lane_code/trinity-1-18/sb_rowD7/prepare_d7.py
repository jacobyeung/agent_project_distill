"""Select the newest intact local seal and authenticate copied D6 references."""
import hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent; K=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w')
def pin(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return dict(sha256=h.hexdigest(),bytes=p.stat().st_size)
pins={str(Path(__file__)):pin(Path(__file__))}; seals={}
for w in ('w20','w21'):
 p=K/w/'out/TREE_SEAL.json'; pins[str(p)]=pin(p); s=json.loads(p.read_text());bad=[]
 for rel,h in s['files'].items():
  f=K/w/'work/tree_r1'/rel
  a=pin(f) if f.exists() else {'sha256':'MISSING'}
  if a['sha256']!=h:bad.append(dict(path=str(f),expected=h,actual=a['sha256']))
 seals[w]=dict(tree_sha256=s['tree_sha256'],files=len(s['files']),mismatches=bad)
assert not seals['w20']['mismatches'];assert seals['w21']['mismatches'],'W21 now sealed: update selected tree'
for p in [*sorted((B/'reference').glob('d6_*.py')),B/'reference/COVERAGE_V2_PUB.tar',B/'reference/coverage_rows_v2.py',B/'reference/source_build_away.py']:
 pins[str(p)]=pin(p)
for name in ('NEW_ROWS.jsonl','SOURCE_MAP.jsonl','GATE.json','CHECKS.json','VERIFY.json'):
 p=B/'work/d6_out'/name;q=Path('/scratch/jjyeung/orch_n30/sb_rowD6/out')/name
 pins[str(p)]=pin(p);pins[str(q)]=pin(q);assert pins[str(p)]==pins[str(q)]
v=dict(command='nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 python prepare_d7.py',input_sha256=pins,status='PASS',selected='w20',seals=seals)
(B/'out/INPUT_AUDIT.json').write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps({w:dict(files=s['files'],mismatches=len(s['mismatches'])) for w,s in seals.items()}))
