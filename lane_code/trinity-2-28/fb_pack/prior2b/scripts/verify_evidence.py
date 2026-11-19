"""Authenticate the recorded evidence inputs, including retained code snapshots."""
from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parents[1]
roots=['work/final_gate/RESULT.json','out/SOURCE_RECONSTRUCTION.json','out/INPUT_AUDIT_FINAL.json','out/STORE_AUDIT.json','out/SEALED_PATCH.json','out/LIVE_PATCH.json','out/CHECKER_NEGATIVE_TESTS.json','out/COUNT_CROSSCHECK.json']
seen={};checked=[];failures=[];parsed=set()
def sha(p):
 p=Path(p).resolve()
 if p not in seen:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
  seen[p]=h.hexdigest()
 return seen[p]
def inspect(path):
 path=Path(path).resolve()
 if path in parsed:return
 parsed.add(path);v=json.loads(path.read_text())
 if not isinstance(v,dict):return
 for item in v.get('inputs',[]):
  p=Path(item['path']);expected=item['sha256'];snapshot=W/'work/code_snapshots'/expected
  try:
   actual=sha(p)
   used=p
   if actual!=expected and snapshot.is_file() and sha(snapshot)==expected:used=snapshot;actual=expected
   status='PASS' if actual==expected else 'MISMATCH'
   rec=dict(path=str(p),sha256=expected,actual_sha256=actual,status=status)
   if used!=p:rec['retained_exact_input']=str(used)
   checked.append(rec)
   if status!='PASS':failures.append(rec)
   if status=='PASS' and used==p and p.is_relative_to(W) and p.suffix=='.json':inspect(p)
  except (OSError,ValueError,KeyError,TypeError) as error:failures.append(dict(path=str(p),sha256=expected,error=str(error)))
for name in roots:inspect(W/name)
result=dict(status='PASS' if not failures else 'FAIL',references_checked=len(checked),unique_files_hashed=len(seen),failures=failures,checked=checked,
 command='OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 PYTHONDONTWRITEBYTECODE=1 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python scripts/verify_evidence.py',
 inputs=[dict(path=str(p),sha256=sha(p)) for p in [Path(__file__).resolve(),*[W/n for n in roots]]])
(W/'out/EVIDENCE_CHECK.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ('checked','inputs','command')})
if failures:raise SystemExit(1)
