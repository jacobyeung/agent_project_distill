from pathlib import Path
import hashlib,json,tarfile
W=Path(__file__).resolve().parents[1];O=W/'out';B=W/'work/followup_baseline'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def members(p):
 with tarfile.open(p) as t:return {m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in t if m.isfile()}
a,b=members(B/'0.tgz'),members(O/'0.tgz')
assert a==b and sha(B/'0.tgz')==sha(O/'0.tgz')
old,new=members(B/'1.tgz'),members(O/'1.tgz')
changed=sorted(n for n in old.keys()|new.keys() if old.get(n)!=new.get(n))
assert set(changed)=={'BATCH.sh','PACKAGE.json','a/5.py','a/6.py'}
# The local source inventory still matches every sealed payload byte.
for n,h in b.items():
 p=O/'src'/n
 if p.exists():assert sha(p)==h,n
value=dict(passed=True,token=(O/'TOKEN').read_text().strip(),same_token_reason='Only operator files and their enclosing seals change; payload bytes are identical.',
 payload_sha256=sha(O/'0.tgz'),identical_members=len(b),changed_delivery_members=changed,
 plan_unchanged=json.loads((O/'READ_PLAN.json').read_text())['plan_sha256']==json.loads((B/'READ_PLAN.json').read_text())['plan_sha256'])
assert value['plan_unchanged']
(O/'OPERATOR_ONLY_AUDIT.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(value))
