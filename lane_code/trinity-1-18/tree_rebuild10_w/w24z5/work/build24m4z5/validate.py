from pathlib import Path
import json,hashlib,base64,sys,tarfile,ast,subprocess,re,os
J=Path.cwd();D=J/'work/build24m4z5';O=J/'out';E=O/'e3'
def load(p):
 v=json.loads(p.read_text());return json.loads(base64.b64decode(v['payload'])) if isinstance(v,dict) and 'payload' in v else v
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sys.path[:0]=[str(J/'work/tree_r1c'),str(O/'kit_n/b')]
from launch_r1.build import verify
import z
seals=load(D/'FINAL_SEALS.json')
for row in seals:
 k=J/row['kit'];assert z.seal(k)==verify(k)==row['own_checker']==row['native_checker']
 assert z.load(k/'BUILD.json')['GO']==z.load(k/'k/a.json')['GO']==row['GO']==(row['kit']=='out/kit_n_go')
baseline=load(D/'BASELINE_FILES.json');uploads=[]
for stem,prefix,root,oldroot in [('UPLOADS_24M4Z5','n',O/'kit_n','work/build24/kits/n'),('UPLOADS_24M4Z5_GO','n_go',O/'kit_n_go','out/kit_n_go')]:
 replay=dict(baseline[oldroot]);record=load(O/(stem+'.json'))
 for r in record['files']:
  if r['name'].startswith(prefix+'/'):
   name=r['name'][len(prefix)+1:];assert replay[name]['sha256']==r['baseline_sha256']
   replay[name]=dict(type='file',sha256=r['sha256'],bytes=r['bytes'],mode=int(r['mode'],8))
 actual={str(p.relative_to(root)):dict(type='file',sha256=sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in root.rglob('*') if p.is_file()}
 assert replay==actual
for stem in ('UPLOADS_24M4Z5','UPLOADS_24M4Z5_GO','UPLOADS_24M4Z5_E3'):
 rows=load(O/(stem+'.json'))['files'];uploads+=rows
 assert (O/(stem+'.list')).read_text().splitlines()==[r['name'] for r in rows]
 for r in rows:
  p=J/r['relative_path'];assert p.stat().st_size==r['bytes']<5_000_000 and sha(p)==r['sha256'];z.name_guard(O/'kit_n')(r['name'])
for name,h in load(E/'pins.json').items():assert sha(E/name)==h
with tarfile.open(E/'k.tgz') as t:actual={m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in t}
assert actual=={str(p.relative_to(O/'kit_n')):sha(p) for p in (O/'kit_n').rglob('*') if p.is_file()}
objects=load(O/'kit_n/k/y.json')['objects'];names=[v+'.j<job>'+f'.part{i:02d}-of-04' for v in objects.values() for i in range(4)]
assert len(names)==108 and (E/'SESSION_NAMES.template.list').read_text().splitlines()==names
for p in [*(O/'kit_n/b').glob('*.py'),*E.glob('*.py')]:ast.parse(p.read_bytes(),str(p))
for p in [O/'jn3.sh',O/'kit_n/b/pc.sh',E/'e3.sh',E/'run.sh']:subprocess.run(['bash','-n',str(p)],check=True)
for r in load(D/'FINAL_SUITES.json'):assert r['returncode']==0 and (J/r['log']).is_file()
for r in load(J/'work/enospc5_final/RESULTS.json'):assert r['status']=='PASS'
for p in ['COMPLETE.json','OWNER.json','RESUME.json','WRAPPER_SIGNALS.json','READBACK_TEST.json','FINAL_LOOP.json']:assert load(D/p)['status']=='PASS'
assert load(D/'PROBES_BEFORE.json')==dict(tests=10,failures=10,errors=0,successful=False)
assert load(D/'PROBES_AFTER.json')==dict(tests=10,failures=0,errors=0,successful=True)
e3=load(D/'e3_final/n/E3.json');assert e3['status']=='PASS' and len(e3['checks'])==15 and all(v=='PASS' for v in e3['checks'].values())
assert len(e3['objects'])==20 and len(e3['rate']['parts'])==4 and e3['rate_bytes']==4<<20
assert all(p['bytes']==1<<20 and p['seconds']>0 and p['MBps']>0 for p in e3['rate']['parts'])
assert e3['archive']['sha256']==sha(D/'e3_final/n/n/o/o.tar')
assert load(D/'e3_final/RESULT.json')['capability_leak']==False
assert (J/'work/enospc5_final/wrapper3/RESULT.json').exists()
assert load(D/'DELTA.json')['status']=='PASS'
assert len((O/'BUILD24M4Z5_REPORT.md').read_text().splitlines())<12
assert len(load(D/'FAILURES.json')['unresolved'])==2
usage=(E/'E3_USAGE.md').read_text()
for r in load(O/'UPLOADS_24M4Z5_E3.json')['files']:assert r['sha256'] in usage
assert sha(E/'readback.py') in usage and '108 fresh' in usage and 'sbatch --hold' in usage
source=(E/'e3.sh').read_text();job=re.search(r'--job-name=(\S+)',source)[1]
assert re.fullmatch(r'a15_cot_ap[0-9a-f]{12}',job) and job!='a15_cot_apf482d730ca91'
for part in ('--partition=preempt','--cpus-per-task=4','--mem=16G','--time=01:00:00'):assert part in source
assert '--gres' not in source
assert '--job-name=a15_cot_apb2edfac4' in (O/'jn3.sh').read_text()
assert 'RATE_BYTES = 2 << 30' in (E/'e3.py').read_text()
summary=dict(artifact_checks='PASS',local_suites='PASS',launch_verdict='NO-GO',unresolved_guarantees=2,
 before_failures=10,after_passes=10,E3_checks=15,E3_objects=20,E3_local_payload_bytes=4<<20,
 E3_real_payload_bytes=2<<30,real_GCS='NOT_RUN',real_rate='NOT_RUN',session_names=108,
 upload_files=len(uploads),largest_upload=max(r['bytes'] for r in uploads),seals='own and native PASS',
 full_archive_diff='PASS',tree_sha256=load(D/'DELTA.json')['tree_sha256'],nice=os.getpriority(os.PRIO_PROCESS,0))
(D/'VALIDATION.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n');print(json.dumps(summary))
