from pathlib import Path
import ast,hashlib,json,re,subprocess,sys,tarfile
W=Path.cwd();O=W/'out';P=O/'package';B=W.parent/'b1p/out'
sys.path.insert(0,str(O/'src'))
from orchard_h10.common import template,canonical,sha,submit_argv,opaque
public=json.loads((P/'0.json').read_text());receipt=json.loads((P/'PACKAGE.json').read_text())
token=(O/'TOKEN').read_text().strip()
assert re.fullmatch('[a-f][0-9a-f]{12}',token)
assert token not in {'e47d0593fefec','bf94a7976a7e9','b01ec87a6f29b','c4d7e0a91b28f','d8a2f6c09e137'}
assert public['token']==token
for n,h in receipt['files'].items():assert sha(P/n)==h,n
assert sha(O/'0.tgz')==sha(P/'0.tgz')==public['payload_sha256']
with tarfile.open(O/'0.tgz') as t:payload={m.name:t.extractfile(m).read() for m in t}
cfg=json.loads(payload['9.json']);assert canonical(cfg)==public['plan_sha256']
for n,pin in cfg['payload_pins'].items():
 assert hashlib.sha256(payload[n]).hexdigest()==pin['sha256'] and len(payload[n])==pin['bytes'],n
 if n!='8.py':assert (O/'src'/n).read_bytes()==payload[n],n
 assert (O/'src/orchard_h10/operator.py').read_bytes()==payload['8.py']
template(O/'src/orchard_h10/vendor');import orchard_launcher as L
assert L.tar_bytes(payload)==(O/'0.tgz').read_bytes()
with tarfile.open(O/'1.tgz') as t:
 names=[]
 for m in t:
  assert m.isfile() and '..' not in Path(m.name).parts
  assert t.extractfile(m).read()==(P/m.name).read_bytes(),m.name
  names.append(m.name)
assert set(names)=={str(p.relative_to(P)) for p in P.rglob('*') if p.is_file()}
for n in ('export_544.json','inputs_544.json','inputs_tower.json'):assert (O/n).read_bytes()==(B/n).read_bytes(),n
ab=json.loads((O/'MEMO_AB.json').read_text());baseline=json.loads((O/'BASELINE_AB.json').read_text())
expected=baseline['modes']['off']['output_sha256']
assert all(r['output_sha256']==expected and r['reads']==30 and r['captures']==5 for r in ab['modes'].values())
assert ab['modes']['on']['g3t_calls']==ab['modes']['on']['sam_encode_calls']==5
assert len(ab['modes']['verify']['events'])==50 and all(e['equal'] for e in ab['modes']['verify']['events'])
r=json.loads((O/'REPLAY_CHECK.json').read_text());assert r['runs']==600 and not r['mismatches']
assert all(row['not_seen_pairs']==7 for row in r['table'] if row['rule']=='candidates_argmax')
for n in ('LOCAL_REHEARSAL.json','MEMO_BINDING.json'):assert json.loads((O/n).read_text())['passed']
assert '31 passed' in (O/'existing.log').read_text() and '3 failed' in (O/'existing.log').read_text() and '10 errors' in (O/'existing.log').read_text()
for n in ('package_final','constraints','b1','stubs','tower','sequence','pairing','b1_report','memo_final','memo_unit_final','memo_isolation','memo_binding_final','production_policy'):
 assert (O/(n+'.log')).read_text().rstrip().endswith('OK'),n
for p in list(O.glob('*.py'))+list((W/'work').glob('*.py')):ast.parse(p.read_text())
for name in ('REPORT.md','OPERATIONS_TOWER.md'):
 text=(O/name).read_text();assert sha(O/'1.tgz') in text
 for block in re.findall(r'```bash\n(.*?)```',text,re.S):subprocess.run(['bash','-n'],input=block,text=True,check=True)
 for match in re.finditer(r'\bsrun\b',text):assert '--job-name=a15_cot_ap'+token in text[match.start():match.start()+250]
assert sha(P/'PACKAGE.json') in (O/'REPORT.md').read_text()
argv=submit_argv(token,1,'05:00:00');assert '--job-name=a15_cot_ap'+token in argv;opaque(argv)
opaque([(P/'BATCH.sh').read_text()])
size=sum(p.stat().st_size for p in W.rglob('*') if p.is_file() and not p.is_symlink());assert size<3_000_000_000,size
static=json.loads((O/'EAT1_GATE.json').read_text())
assert not static['strict_zero_new_findings_pass'] and static['new_A4_findings']==0
assert static['newly_attributable_findings']==17
value=dict(artifact_integrity_pass=True,behavioral_fixture_checks_pass=True,strict_static_gate_pass=False,
 ready_for_submission=False,token=token,payload_sha256=public['payload_sha256'],plan_sha256=public['plan_sha256'],
 package_sha256=sha(P/'PACKAGE.json'),delivery_sha256=sha(O/'1.tgz'),workspace_bytes=size,
 production_tar_bytes_reproduced=True,shell_blocks_syntax=True,real_node_check=False,real_gpu_read=False,
 proof='New off, on and verify plus W2 off all share the response/answer/score hash',response_sha256=expected)
(O/'FINAL_VERIFICATION.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value,indent=2))
