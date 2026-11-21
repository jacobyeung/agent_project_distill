from pathlib import Path
import json,base64,hashlib,tarfile,sys,subprocess,ast,os
J=Path.cwd();D=J/'work/build24m4z4';O=J/'out';E=O/'e2';W=J/'work/enospc4_final'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):
 v=json.loads(p.read_bytes());return json.loads(base64.b64decode(v['payload'])) if isinstance(v,dict) and v.get('encoding') else v
sys.path.insert(0,str(O/'kit_n/b'));import z
seals=load(D/'FINAL_SEALS.json')
for r in seals:
 k=J/r['kit'];assert z.seal(k)==r['own_checker']==r['native_checker']==load(k/'BUILD.json')['kit_sha256']
 for name in ('BUILD.json','k/a.json'):assert load(k/name)['GO']==r['GO']
for root in (O/'kit_n',O/'kit_n_go',J/'work/build24/kits/n'):
 for p in (root/'b').glob('*.py'):ast.parse(p.read_bytes(),str(p))
for p in E.glob('*.py'):ast.parse(p.read_bytes(),str(p))
for p in (E/'e2.sh',E/'run.sh',O/'kit_n/b/pc.sh',O/'kit_n_go/b/pc.sh',O/'jn2.sh'):subprocess.run(['bash','-n',str(p)],check=True)
assert load(D/'DELTA.json')['status']=='PASS'
baseline=load(D/'BASELINE_FILES.json')
for stem,prefix,root,oldroot in [('UPLOADS_24M4Z4','n',O/'kit_n','work/build24/kits/n'),('UPLOADS_24M4Z4_GO','n_go',O/'kit_n_go','out/kit_n_go')]:
 replay=dict(baseline[oldroot])
 for r in load(O/(stem+'.json'))['files']:
  if r['name'].startswith(prefix+'/'):
   name=r['name'][len(prefix)+1:];assert replay[name]['sha256']==r['baseline_sha256']
   replay[name]=dict(type='file',sha256=r['sha256'],bytes=r['bytes'],mode=int(r['mode'],8))
 actual={str(p.relative_to(root)):dict(type='file',sha256=sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in root.rglob('*') if p.is_file()}
 assert replay==actual
uploads=[]
for stem in ('UPLOADS_24M4Z4','UPLOADS_24M4Z4_GO','UPLOADS_24M4Z4_E2'):
 rows=load(O/(stem+'.json'))['files'];uploads+=rows
 assert (O/(stem+'.list')).read_text().splitlines()==[r['name'] for r in rows]
 for r in rows:
  p=J/r['relative_path'];assert p.stat().st_size==r['bytes']<5_000_000 and sha(p)==r['sha256']
  z.name_guard(O/'kit_n')(r['name'])
for name,h in load(E/'pins.json').items():assert sha(E/name)==h
with tarfile.open(E/'k.tgz') as t:got={m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in t}
expected={str(p.relative_to(O/'kit_n')):sha(p) for p in (O/'kit_n').rglob('*') if p.is_file()};assert got==expected
objects=load(O/'kit_n/k/y.json')['objects'];assert len(objects)==27
names=[v+'.j<job>'+f'.part{i:02d}-of-04' for v in objects.values() for i in range(4)]
assert (E/'SESSION_NAMES.template.list').read_text().splitlines()==names and len(names)==108
for v in objects.values():z.name_guard(O/'kit_n')(v)
for r in load(D/'FINAL_SUITES.json'):assert r['returncode']==0 and (J/r['log']).is_file()
for r in load(W/'RESULTS.json'):assert r['status']=='PASS'
assert load(D/'FINAL_LOOP.json')['status']=='PASS'
assert load(D/'current_final/RESULT.json')['status']=='PASS'
assert load(D/'archive_final/RESULT.json')['status']=='PASS'
assert load(D/'legacy_final/LIVE_TESTS.json')['passed'] and load(D/'legacy_final/LIVE_TESTS.json')['tests']==5
assert all(r['status']=='PASS' for r in load(D/'LEGACY_GATE.json')['tests'])
assert load(D/'READBACK_TEST.json')['status']=='PASS'
assert load(D/'FAILURES.json')['unresolved']==[]
e2=load(D/'e2_verified/n/E2.json');assert e2['status']=='PASS' and all(v=='PASS' for v in e2['checks'].values()) and len(e2['checks'])==14
assert len(e2['objects'])==16 and len(e2['archive']['objects'])==4
assert e2['archive']['sha256']==sha(D/'e2_verified/n/n/o/o.tar')
assert load(D/'e2_verified/RESULT.json')['capability_leak']==False
assert load(W/'wrapper2/RESULT.json')['status']=='PASS'
assert (O/'jn2.sh').read_bytes()==(J/'inputs/jn2.sh').read_bytes()
assert len((O/'BUILD24M4Z4_REPORT.md').read_text().splitlines())<12
usage=(E/'E2_USAGE.md').read_text()
for row in load(O/'UPLOADS_24M4Z4_E2.json')['files']:assert row['sha256'] in usage
assert sha(E/'readback.py') in usage
assert '108 fresh' in usage and 'all 108 names' in usage
source=(E/'e2.sh').read_text()
for part in ('--partition=preempt','--cpus-per-task=4','--mem=16G','--time=01:00:00'):assert part in source
assert '--gres' not in source
summary=dict(status='PASS',artifact_checks='PASS',enospc_gate='PASS',E2_aggregate='PASS',E2_checks=14,objects=16,session_names=108,legacy_tests=5,current_tests=8,archive_tests=4,final_loop='PASS',upload_files=len(uploads),largest_upload=max(r['bytes'] for r in uploads),own_native_seals='PASS',syntax='PASS',baseline_overlay_replay='PASS',complete_bundle_matches_N=True,kit_seals={r['kit']:r['own_checker'] for r in seals},tree_sha256=load(D/'DELTA.json')['tree_sha256'],real_GCS='NOT_RUN',nice=os.getpriority(os.PRIO_PROCESS,0))
(D/'VALIDATION.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n');print(json.dumps(summary))
