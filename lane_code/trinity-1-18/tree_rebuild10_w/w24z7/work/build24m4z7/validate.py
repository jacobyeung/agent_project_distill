from pathlib import Path
import ast,base64,json,hashlib,subprocess,sys,tarfile,os
J=Path.cwd();D=J/'work/build24m4z7';O=J/'out';K=O/'kit_n';E=O/'e3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):
 v=json.loads(p.read_bytes());return json.loads(base64.b64decode(v['payload'])) if isinstance(v,dict) and 'payload' in v else v
sys.path.insert(0,str(K/'b'));import z
rows=load(D/'FINAL_SEALS.json')
for row in rows:
 k=J/row['kit'];assert z.seal(k)==row['own_checker']==row['native_checker']==load(k/'BUILD.json')['kit_sha256']
 assert load(k/'k/a.json')['GO']==row['GO']
assert [r['kit'] for r in rows if r['GO']]==['out/kit_n_go']
for p in list((K/'b').glob('*.py'))+list(E.glob('*.py'))+list((O/'tgcs').glob('*.py')):ast.parse(p.read_bytes(),str(p))
for p in (K/'b/pc.sh',O/'jn3.sh',E/'e3.sh',E/'run.sh',O/'tgcs/run_tgcs.sh'):subprocess.run(['bash','-n',str(p)],check=True)
assert '--job-name=a15_cot_apb2edfac4' in (O/'jn3.sh').read_text()
assert 'exec bash "$ROOT/job.sh"' not in (O/'jn3.sh').read_text()
all_uploads=[]
baseline=load(D/'BASELINE_FILES.json')
for suffix in ('','_GO','_E3'):
 stem='UPLOADS_24M4Z7'+suffix;v=load(O/(stem+'.json'));all_uploads+=v['files']
 assert (O/(stem+'.list')).read_text().splitlines()==[r['name'] for r in v['files']]
 for r in v['files']:
  p=J/r['relative_path'];assert p.stat().st_size==r['bytes']<5_000_000 and sha(p)==r['sha256'];z.name_guard(K)(r['name'])
for prefix,root,old in [('n',K,'work/build24/kits/n'),('n_go',O/'kit_n_go','out/kit_n_go')]:
 replay=dict(baseline[old]);suffix='' if prefix=='n' else '_GO'
 for row in load(O/('UPLOADS_24M4Z7'+suffix+'.json'))['files']:
  if row['name'].startswith(prefix+'/'):
   name=row['name'][len(prefix)+1:];assert replay[name]['sha256']==row['baseline_sha256']
   replay[name]=dict(type='file',sha256=row['sha256'],bytes=row['bytes'],mode=int(row['mode'],8))
 actual={str(p.relative_to(root)):dict(type='file',sha256=sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in root.rglob('*') if p.is_file()}
 assert actual==replay
for name,h in load(E/'pins.json').items():assert sha(E/name)==h
with tarfile.open(E/'k.tgz') as t:bundle={m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in t}
assert bundle=={str(p.relative_to(K)):sha(p) for p in K.rglob('*') if p.is_file()}
assert len((E/'SESSION_NAMES.template.list').read_text().splitlines())==108
assert len((E/'STATUS_NAMES.template.list').read_text().splitlines())==16
for row in load(D/'SUITES_GUARD.json'):assert row['returncode']==0
assert all(row['status']=='PASS' for row in load(J/'work/enospc7_guard/RESULTS.json'))
for name in ('core_guard','advanced_guard'):assert all(r['status']=='PASS' for r in load(D/name/'RESULT.json'))
for name in ('e3_guard/RESULT.json','READBACK_GUARD.json','FINAL_LOOP.json','DELTA.json','wrapper_exception/RESULT.json'):assert load(D/name)['status']=='PASS'
for r in load(D/'exit_guard/RESULT.json'):assert r['archive_receipt']==(r['version']=='after')
for r in load(D/'wrapper_signals_a/RESULT.json'):assert r['child_trap'] and r['final_publish']==(r['version']=='after')
report=load(D/'e3_guard/n/E3.json');assert all(v=='PASS' for v in report['checks'].values()) and len(report['checks'])==16
assert report['seal']==sha(K/'SHA256SUMS.txt')
assert len((O/'BUILD24M4Z7_REPORT.md').read_text().splitlines())<12
for row in load(O/'UPLOADS_24M4Z7_E3.json')['files']:assert row['sha256'] in (E/'E3_USAGE.md').read_text()
assert load(D/'FAILURES.json')['unresolved'] and load(D/'FAILURES.json')['local_suites']=='PASS'
summary=dict(status='PASS',artifact_checks='PASS',local_suites='PASS',training_gate='NO-GO',real_GCS='NOT_RUN',E3_checks=16,upload_files=len(all_uploads),largest_upload=max(r['bytes'] for r in all_uploads),full_baseline_diff='PASS',native_seals='PASS',nice=os.getpriority(os.PRIO_PROCESS,0),kit_seals={r['kit']:r['own_checker'] for r in rows})
(D/'VALIDATION.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
