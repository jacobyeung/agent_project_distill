"""Verify the sealed delivery and emit the requested ten-line completion summary."""
from pathlib import Path
import hashlib,json,re,subprocess,tarfile
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
assert not (O/'package/a/c/CPU.json').exists(), 'Local fixture must not authorize Orchard submission'
required=['0.tgz','1.tgz','PACKAGE.json','READ_PLAN.json','ITEM_KEYS.txt','TESTS.txt','PATCH.diff','REPORT.md','OPERATIONS_ROOM.md']
assert all((O/n).is_file() for n in required)
status=json.loads((O/'TEST_SUMMARY.json').read_text());plan=json.loads((O/'READ_PLAN.json').read_text())
assert status['failed_tests']==0
assert plan['token']=='c3cc59fb4aae0'
assert plan['cpu_check']['walltime']=='04:00:00' and plan['cpu_check']['gpus']==0
for name in ('LOCAL_CPU_CHECK.json','LOCAL_NATIVE_CPU_CHECK.json'):
 r=json.loads((O/name).read_text());assert r['passed'] and r['synthetic_devs1']
 assert [v['set'] for v in r['full_reader']['records']]==['dev-S1','R0-dev']
 assert all(v['record']['complete'] and v['record']['output']['finish']=='eos' for v in r['full_reader']['records'])
audit=json.loads((O/'OPERATOR_ONLY_AUDIT.json').read_text());assert audit['passed'] and audit['identical_members']==928
comparison=json.loads((O/'W5_BINDING_EQUIVALENCE.json').read_text());assert comparison['passed'] and comparison['rows']==36
ops=(O/'OPERATIONS_ROOM.md').read_text()
assert h['1.tgz']['sha256'] in ops and '--time=04:00:00 --export=ALL' in ops
for block in re.findall(r'```bash\n(.*?)```',ops,re.S):
 subprocess.run(['bash','-n'],input=block,text=True,check=True,capture_output=True)
 for python in re.findall(r"<<'PYCODE'\n(.*?)\nPYCODE",block,re.S):compile(python,'operator-runbook','exec')
size=sum(p.stat().st_size for p in W.rglob('*') if p.is_file());assert size<2500000000
result=dict(integrity_passed=True,operator_commands_syntax_passed=True,workspace_bytes=size,local_checks_passed=True,
 fully_validated=False,orchard_cpu_check_run=False,unresolved=status['unresolved'])
(O/'FINAL_CHECK.json').write_text(json.dumps(result,indent=2)+'\n')
lines=[f"Token: {plan['token']}; retained because all 928 payload members are unchanged.",
 f"Payload SHA256: {h['0.tgz']['sha256']}",f"Delivery SHA256: {h['1.tgz']['sha256']}",
 f"PACKAGE SHA256: {h['PACKAGE.json']['sha256']}",f"Operator SHA256: {h['tower_sequence.py']['sha256']}",
 f"Tests: {status['passed_tests']} passed; {status['failed_tests']} failed across the latest suite results.",
 'Local proof: both full-reader records finish; all 36 dev-S1 bindings match W5.',
 'Orchard check: staged frame hashes/decode, real reader and scoring with CPU model stubs; both records and pass flag required.',
 'CPU allocation: general, 8 CPUs, 200G, 04:00:00, no GPU; exact commands are in out/OPERATIONS_ROOM.md.',
 'Open risks: real Orchard CPU check remains pending; GPU behavior, timing and return-pool occupancy are unmeasured.']
assert len(lines)==10
(O/'SUMMARY.txt').write_text('\n'.join(lines)+'\n');(O/'final_message.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
