from pathlib import Path
import os,sys,ast,json,base64,hashlib,subprocess,tarfile
J=Path.cwd();D=J/'work/build24m4z10';O=J/'out';K=O/'kit_n';E=O/'e3'
def load(p):
 v=json.loads(p.read_bytes());return json.loads(base64.b64decode(v['payload'])) if isinstance(v,dict) and 'payload' in v else v
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
sys.path.insert(0,str(K/'b'));import z
sys.path.insert(0,str(J/'work/tree_r1c'));from launch_r1.build import verify
checks=[]
for name in ('out/kit_n','out/kit_n_go','work/build24/kits/n','work/build24/kits/q','out/kit_qd'):
 k=J/name
 own=subprocess.run([sys.executable,'-I','-s','-B',str(k/'b/v.py'),str(k)],capture_output=True,text=True)
 assert own.returncode==0,own.stderr
 native=verify(k);h=sha(k/'SHA256SUMS.txt');assert native==own.stdout.strip()==load(k/'BUILD.json')['kit_sha256']==h
 go=load(k/'k/a.json')['GO'];assert go==(name=='out/kit_n_go')
 checks.append(dict(kit=name,seal=h,own_checker=own.stdout.strip(),native_checker=native,GO=go))
write(D/'KIT_CHECKS.json',checks)
assert load(K/'k/n.json')['recipe']['stop_before_seconds']==3600
for name in ('b/o.py','b/pc.py','b/pc.sh','k/y.json'):
 assert (K/name).read_bytes()==(O/'kit_n_go'/name).read_bytes()==(J/'work/build24/kits/n'/name).read_bytes()
for root in ('kit_n','kit_n_go'):
 for name in ('k/n.json','b/gc.py','k/a.json'):
  assert (O/root/name).read_bytes()==(J.parent/'w24z7/out'/root/name).read_bytes()
for p in list((K/'b').glob('*.py'))+list(E.glob('*.py'))+list((O/'tgcs').glob('*.py'))+[O/'set_stop.py']:
 ast.parse(p.read_bytes(),str(p))
for p in (K/'b/pc.sh',O/'jn3.sh',E/'e3.sh',E/'run.sh',E/'trinity.sh',O/'tgcs/run_tgcs.sh'):
 subprocess.run(['bash','-n',str(p)],check=True)
for name,h in load(E/'pins.json').items():assert sha(E/name)==h,(name,h)
with tarfile.open(E/'k.tgz') as t:bundle={m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in t}
assert bundle=={str(p.relative_to(K)):sha(p) for p in K.rglob('*') if p.is_file()}
for root in (E,O/'tgcs'):
 assert len((root/'SESSION_NAMES.template.list').read_text().splitlines())==112
 assert sum('_u.log' in s for s in (root/'STATUS_NAMES.template.list').read_text().splitlines())==4
assert len((E/'STATUS_NAMES.template.list').read_text().splitlines())==16
for root in (E,O/'tgcs'):
 s=(root/'observe.py').read_text()
 assert not __import__('re').search(r'class\s+\w+\([^)]*(?:Original|HTTPSConnection)',s)
 assert not __import__('re').search(r'http\.client\.HTTPSConnection\s*=',s)
baseline=load(D/'BASELINE_FILES.json');all_uploads=[]
for suffix,prefix,root,old in [('', 'n',K,'work/build24/kits/n'),('_GO','n_go',O/'kit_n_go','out/kit_n_go'),('_E3','e3',E,None)]:
 stem='UPLOADS_24M4Z10'+suffix;rows=load(O/(stem+'.json'))['files'];all_uploads+=rows
 assert (O/(stem+'.list')).read_text().splitlines()==[r['name'] for r in rows]
 for r in rows:
  p=J/r['relative_path'];assert p.stat().st_size==r['bytes']<5_000_000 and sha(p)==r['sha256'];z.name_guard(K)(r['name'])
 if old:
  replay=dict(baseline[old])
  for row in rows:
   if row['name'].startswith(prefix+'/'):
    name=row['name'][len(prefix)+1:];assert replay[name]['sha256']==row['baseline_sha256']
    replay[name]=dict(type='file',sha256=row['sha256'],bytes=row['bytes'],mode=int(row['mode'],8))
  actual={str(p.relative_to(root)):dict(type='file',sha256=sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in root.rglob('*') if p.is_file()}
  assert replay==actual
for row in load(O/'UPLOADS_24M4Z10_E3.json')['files']:assert row['sha256'] in (E/'E3_USAGE.md').read_text()
assert load(D/'DELTA.json')['status']=='PASS'
assert len((O/'BUILD24M4Z10_REPORT.md').read_text().splitlines())<12
results=[]
for r in load(D/'SUITES_FINAL.json'):assert r['returncode']==0;results.append(r)
for r in load(D/'ALL_FINAL.json'):
 if r['name'] not in ('tgcs_observers','trinity'):
  assert r['returncode']==0;results.append(r)
for r in load(D/'HARNESS_FINAL.json'):assert r['returncode']==0;results.append(r)
for label in ('core_final','advanced_final','findings_final'):
 for r in load(D/label/'RESULT.json'):assert r['status']=='PASS',(label,r)
assert all(r['status']=='PASS' for r in load(J/'work/enospc10final/RESULTS.json'))
assert load(D/'current_suite_final/RESULT.json')['status']=='PASS'
assert load(D/'archive_suite_final/RESULT.json')['status']=='PASS'
assert load(D/'legacy_suite_final/LIVE_TESTS.json')['passed']
for f in ('policy/RESULT.json','FINAL_LOOP_FINAL.json','READBACK_FINAL.json','trinity_pass/RESULT.json','tgcs_observers_pass/RESULT.json','tgcs_final/RESULT.json','e3_sealed/RESULT.json','wrapper_exception/RESULT.json'):
 assert load(D/f)['status']=='PASS',f
for r in load(D/'wrapper_race_fixed/RESULT.json'):
 if r['version']=='after':assert r['returncode']==(7 if r['signal']=='TERM' else 9) and r['final_publish']
for r in load(D/'wrapper_signals_final/RESULT.json'):assert r['child_trap'] and r['final_publish']==(r['version']=='after')
for r in load(D/'exit_final/RESULT.json'):assert r['archive_receipt']==(r['version']=='after')
report=load(D/'e3_sealed/n/E3.json')
assert report['status']=='PASS' and len(report['checks'])==17 and all(v=='PASS' for v in report['checks'].values())
assert report['seal']==sha(K/'SHA256SUMS.txt') and len(report['objects'])==16
assert report['resume_real']['status']=='PASS' and report['resume_real']['real_service'] is False
for name in ('e3.py','observe.py','run.sh','k.tgz'):
 assert sha(E/name)==sha(D/'e3_sealed/n'/('observe_actual.py' if name=='observe.py' else name))
write(D/'SUITE_RESULTS.json',dict(status='PASS',suites=results,additional=['policy','wrapper_signals','wrapper_race','wrapper_exception'],checks=17,remote_service='NOT_RUN'))
failures=[]
for name,log,reason in [
 ('legacy_fixture','legacy_guard.log','Direct stop-method fixture now selects final state explicitly.'),
 ('existing_enospc_fixture','existing_enospc_guard.log','Fixture no longer requires a duplicate ordinary upload of the stop checkpoint.'),
 ('wrapper_race_argument','wrapper_race.log','Supplied the required output suffix.'),
 ('wrapper_race_control','wrapper_race_guard.log','Staged the missing pre-fix wrapper control.'),
 ('tgcs_constructor_control','all_tgcs_observers.log','A constructor failure has no HTTP response log; the control now asserts its constructor error and zero receipts.'),
 ('trinity_memory_cap','all_trinity.log','The launcher now respects a lower inherited hard memory limit.')
]:
 p=D/log
 failures.append(dict(name=name,resolved=True,reason=reason,log=str(p.relative_to(J)),output=p.read_text() if p.exists() else 'Recorded in prior suite output.'))
failures.append(dict(name='fixture_script_quoting',resolved=True,output='-euo: line 28: here-document ended early; /b/pc.sh: No such file or directory; touch /started: Read-only file system.',reason='Interrupted only the malformed local command; wrote the fixture with apply_patch. No out-of-workspace write succeeded.'))
write(D/'FAILURES.json',dict(local_suites='PASS',resolved=failures,unresolved=[dict(item='measurement',reason='Historical checkpoint write times W and real E3 rate/resume were not available under the offline run constraint.'),dict(item='training_gate',reason='The shipped stop constant remains 3600 as required; evaluate the measured formula and review the constant before training.')],expected_fail_before='Retained in findings_final, core_final, exit_final and tgcs_observers_pass',real_GCS_new_bytes='NOT_RUN'))
summary=dict(status='PASS',artifact_checks='PASS',local_suites='PASS',training_gate='NO-GO',E3_checks=17,session_names=112,upload_files=len(all_uploads),largest_upload=max(r['bytes'] for r in all_uploads),full_baseline_diff='PASS',native_seals='PASS',nice=os.getpriority(os.PRIO_PROCESS,0),real_service='NOT_RUN',kit_seals={r['kit']:r['seal'] for r in checks})
write(D/'VALIDATION.json',summary);print(json.dumps(summary))
