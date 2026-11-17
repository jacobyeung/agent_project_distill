from pathlib import Path
import hashlib,json,tarfile
W=Path(__file__).resolve().parents[1];O=W/'out'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
h=json.loads((O/'HASHES.json').read_text())
for n,v in h.items():assert (O/n).stat().st_size==v['bytes'] and sha(O/n)==v['sha256'],n
with tarfile.open(O/'1.tgz') as t:
 for m in t:
  assert m.isfile() and '..' not in Path(m.name).parts
  assert t.extractfile(m).read()==(O/'package'/m.name).read_bytes(),m.name
assert (O/'PACKAGE.json').read_bytes()==(O/'package/PACKAGE.json').read_bytes()
required=['0.tgz','1.tgz','PACKAGE.json','READ_PLAN.json','ITEM_KEYS.txt','TESTS.txt','PATCH.diff','REPORT.md','OPERATIONS_ROOM.md','REMOVAL_CANDIDATES.md']
assert all((O/n).is_file() for n in required)
size=sum(p.stat().st_size for p in W.rglob('*') if p.is_file());assert size<2500000000
status=json.loads((O/'TEST_SUMMARY.json').read_text());plan=json.loads((O/'READ_PLAN.json').read_text())
result=dict(integrity_passed=True,all_requested_deliverables_present=True,workspace_bytes=size,fully_validated=status['failed_tests']==0,unresolved=status['unresolved'])
(O/'FINAL_CHECK.json').write_text(json.dumps(result,indent=2)+'\n')
lines=[f"Token: {plan['token']}",f"Payload SHA256: {h['0.tgz']['sha256']}",f"Delivery SHA256: {h['1.tgz']['sha256']}",f"PACKAGE SHA256: {h['PACKAGE.json']['sha256']}",f"Plan SHA256: {plan['plan_sha256']}",f"Item-set SHA256: {plan['item_set_sha256']}",f"Tests: {status['passed_tests']} passed; {status['failed_tests']} failed (missing dev-S1 frames).",'Walltime: 02:30:00; one GPU.','Return estimate: 10,428,800 bytes; workspace below 2.5 GB.','Open risks: missing dev-S1 tar blocks full validation; GPU/staging timing and pool occupancy unmeasured.']
assert len(lines)==10
(O/'SUMMARY.txt').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
