"""Summarize progress and flag failures in methods that passed build 5."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build6'
old=json.loads((L/'work/build5/proofs/suite_tree/results.json').read_text())
passed=set(old['passed']);new=[];r2=[]
for group in ('generator','legacy','r2'):
 root=B/'proofs/suite_tree'/group
 if (root/'progress.json').exists():print(group,(root/'progress.json').read_text())
 for name in ('live_errors.json','live_failures.json'):
  path=root/name
  if path.exists():
   for test,error in json.loads(path.read_text()):
    if group=='r2':r2.append(dict(test=test,error=error))
    if test.split(' (',1)[0] in passed:new.append(dict(test=test,error=error))
(B/'LIVE_B5_LOSSES.json').write_text(json.dumps(new,indent=2)+'\n')
print(json.dumps(dict(lost_pass_events=len(new),tests=[r['test'] for r in new])))
(B/'LIVE_R2_FAILURES.json').write_text(json.dumps(r2,indent=2)+'\n')
print(json.dumps(dict(r2_failure_events=len(r2),tests=[r['test'] for r in r2])))
for group in ('generator','legacy','r2'):
 path=B/'proofs/suite_base'/group/'progress.json'
 if path.exists():print('base/'+group,path.read_text())
