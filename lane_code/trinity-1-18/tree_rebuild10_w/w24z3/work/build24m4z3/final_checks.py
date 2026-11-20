from pathlib import Path
import json,hashlib,ast,sys,os,subprocess,tarfile
J=Path.cwd();D=J/'work/build24m4z3';O=J/'out';E=O/'e2'
sys.path.insert(0,str(O/'kit_n/b'));import z
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
seals={}
for n,k in [('n',O/'kit_n'),('n_go',O/'kit_n_go'),('q',J/'work/build24/kits/q'),('qd',O/'kit_qd')]:
 seals[n]=z.seal(k);assert z.load(k/'BUILD.json')['kit_sha256']==seals[n]
 for f in ('BUILD.json','k/a.json'):assert z.load(k/f)['GO']==(n=='n_go')
for r in json.loads((D/'FINAL_SEALS.json').read_text()):assert r['native_checker']==r['own_checker']
changes=json.loads((D/'DELTA.json').read_text());assert changes['status']=='PASS'
for r in changes['full_diff'].values():assert not r['added'] and not r['missing']
ordinary=json.loads((O/'UPLOADS_24M4Z3.json').read_text());go=json.loads((O/'UPLOADS_24M4Z3_GO.json').read_text());e2=json.loads((O/'UPLOADS_24M4Z3_E2.json').read_text())
baseline=json.loads((D/'BASELINE_FILES.json').read_text())
for record,prefix,root,oldroot in ((ordinary,'n',O/'kit_n','work/build24/kits/n'),(go,'n_go',O/'kit_n_go','out/kit_n_go')):
 replay=dict(baseline[oldroot])
 for r in record['files']:
  if r['name'].startswith(prefix+'/'):
   name=r['name'][len(prefix)+1:];assert replay[name]['sha256']==r['baseline_sha256']
   replay[name]=dict(type='file',sha256=r['sha256'],bytes=r['bytes'],mode=int(r['mode'],8))
 actual={str(p.relative_to(root)):dict(type='file',sha256=sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in root.rglob('*') if p.is_file()}
 assert replay==actual
for stem,record in [('UPLOADS_24M4Z3',ordinary),('UPLOADS_24M4Z3_GO',go),('UPLOADS_24M4Z3_E2',e2)]:
 assert (O/(stem+'.list')).read_text().splitlines()==[r['name'] for r in record['files']]
 for r in record['files']:
  p=J/r['relative_path'];assert sha(p)==r['sha256'] and p.stat().st_size==r['bytes']<=5_000_000
  z.name_guard(O/'kit_n')(r['name'])
for name,h in json.loads((E/'pins.json').read_text()).items():assert sha(E/name)==h
with tarfile.open(E/'k.tgz') as t:
 got={m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in t}
expected={str(p.relative_to(O/'kit_n')):sha(p) for p in (O/'kit_n').rglob('*') if p.is_file()}
assert got==expected
for p in E.glob('*.py'):ast.parse(p.read_text(),str(p))
for p in (E/'e2.sh',E/'run.sh',O/'jn2.sh',O/'kit_n/b/pc.sh'):subprocess.run(['bash','-n',str(p)],check=True)
source=(E/'e2.sh').read_text()
for part in ('--partition=preempt','--cpus-per-task=4','--mem=16G','--time=01:00:00','--hold'):
 if part!='--hold':assert part in source
assert '--gres' not in source
import re
job=re.search(r'--job-name=(\S+)',source)[1];assert re.fullmatch(r'a15_cot_ap[0-9a-f]{12}',job);z.name_guard(O/'kit_n')(job)
assert len((E/'SESSION_NAMES.template.list').read_text().splitlines())==108
report=json.loads((D/'e2_final/n/E2.json').read_text());assert report['status']=='PASS' and report['checks']['archive_while_full']=='PASS'
assert all(v=='PASS' for k,v in report['checks'].items() )
assert json.loads((D/'current_final/RESULT.json').read_text())['status']=='PASS'
assert json.loads((D/'READBACK_TEST.json').read_text())['status']=='PASS'
assert json.loads((J/'work/enospc3/wrapper2/RESULT.json').read_text())['status']=='PASS'
assert (O/'jn2.sh').read_bytes()==(J/'inputs/jn2.sh').read_bytes()
assert len((O/'BUILD24M4Z3_REPORT.md').read_text().splitlines())<12
assert all(r['status']=='PASS' for r in json.loads((J/'work/enospc3/RESULTS.json').read_text()))
assert json.loads((D/'current_final/RESULT.json').read_text())['tests']==10
assert json.loads((D/'legacy_verified/LIVE_TESTS.json').read_text())['passed']
assert all(r['ok'] for r in json.loads((J/'work/enospc3/results4.json').read_text()))
assert len(report['objects'])==16 and len(report['archive']['objects'])==4
assert len(set((E/'SESSION_NAMES.template.list').read_text().splitlines()))==108
assert all(p.read_bytes()==(O/'kit_n_go'/p.relative_to(O/'kit_n')).read_bytes() for p in (O/'kit_n/b/o.py',O/'kit_n/b/pc.py',O/'kit_n/b/pc.sh',O/'kit_n/k/y.json'))
for p in (O/'kit_n',O/'kit_n_go'):
 z.name_guard(p)(z.load(p/'k/y.json')['objects']['o'])
 z.name_guard(p)('--finish')
assert (J/'work/enospc3/kit/b/pc.py').read_bytes()==(O/'kit_n/b/pc.py').read_bytes()
assert (J/'work/enospc3/kit/b/o.py').read_bytes()==(O/'kit_n/b/o.py').read_bytes()
assert json.loads((D/'FAILURES.json').read_text())['unresolved']==[]
write(D/'VALIDATION.json',dict(status='PASS',enospc_gate='PASS',reason='Exact exit archive and RESULT.json reach the sink while X is full',artifact_checks='PASS',tree=changes['tree_sha256'],kits=seals,full_diff='DELTA.json',normal_uploads=len(ordinary['files']),GO_uploads=len(go['files']),E2_uploads=len(e2['files']),largest_upload=max(r['bytes'] for r in ordinary['files']+go['files']+e2['files']),ordinary_and_go_replay=True,E2_bundle_matches_N=True,session_names=108,local_E2_check_result=report['checks'],nice=os.getpriority(os.PRIO_PROCESS,0),remote_run=False))
print(json.dumps(dict(status='PASS',kits=seals,ordinary=7,GO=6,E2=6,session_names=108)))
