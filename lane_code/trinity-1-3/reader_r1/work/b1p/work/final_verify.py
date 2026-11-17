from pathlib import Path
import ast,hashlib,io,json,re,subprocess,sys,tarfile
W=Path.cwd();O=W/'out';P=O/'package';R=W/'in/repin/out'
sys.path.insert(0,str(O/'src'))
from orchard_h10.common import template,sha,canonical
public=json.loads((P/'0.json').read_text());manifest=json.loads((P/'PACKAGE.json').read_text())
assert sha(P/'0.tgz')==public['payload_sha256']==sha(O/'0.tgz')
for n,h in manifest['files'].items():assert sha(P/n)==h,n
with tarfile.open(P/'0.tgz') as t:payload={m.name:t.extractfile(m).read() for m in t}
assert canonical(json.loads(payload['9.json']))==public['plan_sha256']
template(O/'src/orchard_h10/vendor');import orchard_launcher as L
assert L.tar_bytes(payload)==(P/'0.tgz').read_bytes(),'Production tar rules differ'
with tarfile.open(O/'1.tgz') as t:
 for m in t:assert t.extractfile(m).read()==(P/m.name).read_bytes(),m.name
for n in ('export_544.json','inputs_544.json'):
 assert (O/n).read_bytes()==(R/n).read_bytes(),n
before=json.loads((R/'inputs_544.json').read_text());after=json.loads((O/'inputs_tower.json').read_text())
input_delta={k for k in before.keys()|after.keys() if before.get(k)!=after.get(k)}
assert input_delta=={'types'},input_delta
for p in list(O.glob('*.py'))+list((W/'work').glob('*.py')):ast.parse(p.read_text())
ops=(O/'OPERATIONS_TOWER.md').read_text();report=(O/'REPORT.md').read_text()
assert sha(O/'1.tgz') in ops and sha(P/'PACKAGE.json') in report
for code in re.findall(r'```bash\n(.*?)```',ops,re.S):subprocess.run(['bash','-n'],input=code,text=True,check=True)
for code in re.findall(r'```bash\n(.*?)```',report,re.S):subprocess.run(['bash','-n'],input=code,text=True,check=True)
for m in re.finditer(r'\bsrun\b',ops):assert '--job-name=a15_cot_ap' in ops[m.start():m.start()+250]
from orchard_h10.common import submit_argv
argv=submit_argv(public['token'],1,'05:00:00')
assert '--job-name=a15_cot_ap'+public['token'] in argv
assert '--gres=gpu:1' in argv
r=json.loads((O/'REPLAY_CHECK.json').read_text());assert r['runs']==600 and not r['mismatches']
assert all(x['not_seen_pairs']==7 for x in r['table'] if x['rule']=='candidates_argmax')
assert json.loads((O/'EAT1_GATE.json').read_text())['passed']
assert '31 passed' in (O/'existing.log').read_text()
size=sum(p.stat().st_size for p in W.rglob('*') if p.is_file() and not p.is_symlink());assert size<3_000_000_000,size
value=dict(passed=True,payload_sha256=public['payload_sha256'],plan_sha256=public['plan_sha256'],
 package_sha256=sha(P/'PACKAGE.json'),delivery_sha256=sha(O/'1.tgz'),workspace_bytes=size,
 input_changed_fields=sorted(input_delta),production_tar_bytes_reproduced=True,shell_blocks_syntax=True,
 real_node_check=False,real_gpu_read=False)
(O/'FINAL_VERIFICATION.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
