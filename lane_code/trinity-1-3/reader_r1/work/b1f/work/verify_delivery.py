from pathlib import Path
import ast,hashlib,io,json,re,tarfile,sys
W=Path.cwd();O=W/'out';P=O/'package';sha=lambda raw:hashlib.sha256(raw).hexdigest()
sys.path[:0]=[str(O/'src'),str(O)]
from orchard_h10.common import opaque,submit_argv
checks=[]
def check(value,label):
 assert value,label
 checks.append(label)
required=['0.tgz','1.tgz','PACKAGE.json','PATCH.diff','PATCH_vs_bf94a7976a7e9.diff','PATCH_vs_c91bb8ec884e9.diff','FILE_SHA256_DIFF_vs_bf94a7976a7e9.tsv','FILE_SHA256_DIFF_vs_c91bb8ec884e9.tsv','TESTS.txt','REPORT.md','OPERATIONS_TOWER.md','REMOVAL_CANDIDATES.md']
check(all((O/n).is_file() for n in required),'all required deliverables exist')
token=(O/'TOKEN').read_text().strip();check(re.fullmatch('[a-f][0-9a-f]{12}',token) is not None,'one compatible 13-hex token')
check(token not in ('b01ec87a6f29b','bf94a7976a7e9','e47d0593fefec','c91bb8ec884e9','c4d7e0a91b28f','d8a2f6c09e137'),'token differs from all prohibited tokens')
with tarfile.open(O/'0.tgz') as t:payload={m.name:t.extractfile(m).read() for m in t if m.isfile()}
config=json.loads(payload['9.json']);public=json.loads((P/'0.json').read_text())
check(config['token']==public['token']==token,'payload and public token agree')
check(sha((O/'0.tgz').read_bytes())==public['payload_sha256'],'public payload hash')
for name,pin in config['payload_pins'].items():
 check(sha(payload[name])==pin['sha256'] and len(payload[name])==pin['bytes'],'payload pin '+name)
 if name not in ('8.py','9.json'):check(payload[name]==(O/'src'/name).read_bytes(),'payload source '+name)
with tarfile.open(O/'1.tgz') as t:delivery={m.name:t.extractfile(m).read() for m in t if m.isfile()}
for name,raw in delivery.items():check(raw==(P/name).read_bytes(),'delivery member '+name)
receipt=json.loads((O/'PACKAGE.json').read_text());check((O/'PACKAGE.json').read_bytes()==delivery['PACKAGE.json'],'top package receipt')
for name,h in receipt['files'].items():check(sha(delivery[name])==h,'sealed operator pin '+name)
check(delivery['a/5.py']==(O/'node_check.py').read_bytes(),'CPU helper bytes')
check(delivery['a/6.py']==(O/'tower_sequence.py').read_bytes(),'sequence helper bytes')
batch=delivery['BATCH.sh'].decode();opaque([batch]);raw=bytes.fromhex(re.search(r"bytes.fromhex\('([0-9a-f]+)'\)",batch)[1])
with tarfile.open(fileobj=io.BytesIO(raw)) as t:
 check(t.extractfile('0.py').read()==(O/'tower_bootstrap.py').read_bytes(),'batch bootstrap bytes')
 check(t.extractfile('6.py').read()==(O/'tower_sequence.py').read_bytes(),'batch sequence bytes')
argv=submit_argv(token,1,'05:00:00');opaque(argv);check('--job-name=a15_cot_ap'+token in argv,'opaque job name')
for n in ('inputs_tower.json','export_544.json'):check((O/n).read_bytes()==(W.parent/'b1m/out'/n).read_bytes(),'unchanged '+n)
for n,h in json.loads((O/'DELIVERY_SHA256.json').read_text()).items():
 if n in ('plan_sha256','BATCH_sha256'):continue
 check(sha((O/n).read_bytes())==h,'report hash '+n)
rep=json.loads((O/'REPLAY_CHECK.json').read_text());check(rep['runs']==600 and not rep['mismatches'],'600-run zero-mismatch replay')
base=json.loads((O/'BASELINE_AB.json').read_text())['modes']['off']['output_sha256']
for mode,r in json.loads((O/'MEMO_AB.json').read_text())['modes'].items():check(r['output_sha256']==base,'baseline parity '+mode)
check(json.loads((O/'EAT1_GATE.json').read_text())['passed'],'EAT-1 scope gate')
for n in ('MULTITYPE_AB.json','MEMO_BINDING.json','LOCAL_REHEARSAL.json','RETURN_MEMBERS.json','STOP_PROOF.json','RETURN_CLI.json'):
 check(json.loads((O/n).read_text())['passed'],'passing receipt '+n)
from h1eval.cli import code_hash
for mode,receipt in json.loads((O/'MULTITYPE_AB.json').read_text())['modes'].items():
 for env in Path(receipt['root']).glob('journal/*/*/environment.json'):
  binding=json.loads(env.read_text())['binding']
  check(binding['evaluator_code_sha256']==code_hash(),'sealed multi-type evaluator '+mode)
  check(binding['reader_sha256']==code_hash(O/'src/b/e2e_reader'),'sealed multi-type reader '+mode)
scan=json.loads((O/'EAT1_DELTA.json').read_text());check(not scan['c91']['added'],'zero new A3/A4 reader findings')
check(not json.loads((O/'TIME_PRICE.json').read_text())['case']['one_worker_per_read']['fits_with_stop_and_return_margin'],'time limitation disclosed')
check(not json.loads((O/'MEMORY_BOUND.json').read_text())['production_measurement_available'],'memory limitation disclosed')
for name in ('tower_sequence.py','tower_bootstrap.py','tower_pair.py','unpack_return.py','node_check.py'):ast.parse((O/name).read_text())
size=sum(p.stat().st_size for p in W.rglob('*') if p.is_file());check(size<3*1024**3,'workspace under 3 GiB')
result=dict(passed=True,checks=len(checks),workspace_bytes=size,token=token,payload_sha256=public['payload_sha256'],delivery_sha256=sha((O/'1.tgz').read_bytes()),production_ready=False,notes=['Production memory measurement outstanding','786-read estimate 5.167 hours with margins','Legacy missing-K1 tests do not pass'])
(O/'FINAL_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
