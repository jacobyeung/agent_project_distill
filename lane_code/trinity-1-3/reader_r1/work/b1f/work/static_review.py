from pathlib import Path
import json,collections
O=Path('out');d=json.loads((O/'EAT1_DELTA.json').read_text());review=[]
for path,fn,rule,detail in d['added']:
 if path=='b/e2e_reader/real.py' and fn=='TowerG3T._fresh' and rule=='A3.data_file':
  reason='The identical file literal belongs to the unchanged G3T fresh-call body, renamed from __call__ to _fresh; DELTA_AUDIT.json proves AST identity.';new=False
 elif rule=='A3.constant' and ('17179869184' in detail or detail in ('constant 16','constant 1024')):
  reason='The constant declares the default retained-byte limit. It only controls eviction or binds that limit into settings; it never scales, clips or selects a perception value.';new=True
 elif path=='b/e2e_reader/perception_memo.py' and fn=='Memo.begin_read' and rule=='A3.threshold':
  reason='The comparison chooses whether this scheduled read recomputes hits. It does not choose a model result or alter any returned value.';new=True
 elif path=='b/e2e_reader/perception_memo.py' and fn=='Memo.call' and rule=='A3.threshold':
  reason='The comparison admits or evicts stored bytes. Every miss calls the unchanged fresh module.';new=True
 elif path=='orchard_h10/runner.py' and rule=='A3.table_load':
  reason='The runner reads the existing settings file before launching a worker to bind its exact identity. The memo itself performs no file IO.';new=True
 else:raise AssertionError((path,fn,rule,detail))
 review.append(dict(file=path,function=fn,rule=rule,detail=detail,new=new,reason=reason))
value=dict(raw_before=d['before'],raw_after=d['after'],raw_added=len(d['added']),relocated_findings=sum(not r['new'] for r in review),
 newly_attributable_findings=sum(r['new'] for r in review),new_A4_findings=sum(r['new'] and r['rule'].startswith('A4') for r in review),
 strict_zero_new_findings_pass=False,reviewed_response_value_findings=0,reviewed_response_value_pass=True,
 no_allowlist_changes=True,whole_reader_EAT1_pass=False,
 conclusion='The strict static gate is NOT passed. Manual review classifies the new flags as identity, scheduling and memory bookkeeping, with zero new response-value or fallback rules. Review remains required; the raw scanner results are retained.',
 adjudication=review)
(O/'EAT1_GATE.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps({k:v for k,v in value.items() if k!='adjudication'},indent=2))
