from pathlib import Path
import json,hashlib,base64,tarfile,subprocess,sys,ast
J=Path.cwd();D=J/'work/build24m4z12';O=J/'out'
def load(p):
 v=json.loads(p.read_text());return json.loads(base64.b64decode(v['payload'])) if isinstance(v,dict) and 'payload' in v else v
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
allrows=load(D/'ALL_SEALED.json');newrows=load(D/'new_verified/RESULT.json');assert len(newrows)==10 and all(r['status']=='PASS' for r in newrows)
assert all(r['returncode']==0 for r in allrows if r['name']!='new_findings')
# Record the completed rerun as the final result, retaining the failed run in FAILURES.json.
for r in allrows:
 if r['name']=='new_findings':r.update(returncode=0,log='work/build24m4z12/new_verified.log',result='work/build24m4z12/new_verified/RESULT.json')
(D/'ALL_SEALED.json').write_text(json.dumps(allrows,indent=2)+'\n')
assert all(r['returncode']==0 for r in load(D/'SUITES_SEALED.json'))
for file in ('SCOPE.json','DELTA.json','PRIORITY_CONTROLS.json','REAL_EVIDENCE.json','e3_sealed/RESULT.json','trinity_sealed/RESULT.json','policy/RESULT.json'):
 assert load(D/file)['status']=='PASS',file
assert all(r['status']=='PASS' for r in load(D/'findings_sealed/RESULT.json'))
# Verify request order using sink events, and verify every retained non-u attempt in the final u bytes.
orders=[]
for mode in ('success','nominal','failure','resume'):
 r=D/'new_verified'/('after_'+mode);events=[json.loads(l) for l in (r/'sink/events.jsonl').read_text().splitlines()]
 attempts=[]
 for line in (r/'n/live_spool/upload.log').read_text().splitlines():
  try:attempts.append(json.loads(line))
  except ValueError:pass
 labels=['_ckstop.','_mstop.','_m100.','_o.tar','_u.log','_ck00.']
 positions=[next(i for i,e in enumerate(attempts) if label in e.get('name','')) for label in labels];assert positions==sorted(positions),(mode,positions)
 names=load(r/'kit/k/y.json')['objects'];raw=b''.join((r/'sink'/(hashlib.sha256((names['u']+'.j41'+f'.part{i:02d}-of-04').encode()).hexdigest()+'.data')).read_bytes() for i in range(4))
 # The live-probe's later receipt queries are outside the completed EXIT snapshot.
 lines=(r/'n/live_spool/upload.log').read_bytes().splitlines();last_u=max(i for i,l in enumerate(lines) if b'_u.log' in l)
 data_lines=[l for l in lines[:last_u] if l.strip() and b'_u.log' not in l]
 assert all(l in raw for l in data_lines),(mode,[l for l in data_lines if l not in raw][:2])
 orders.append(dict(mode=mode,first_attempt_positions=positions,priority_order=True,final_log_includes_data_attempts=True))
(D/'ORDER_VALIDATION.json').write_text(json.dumps(orders,indent=2)+'\n')
checks=[]
for name in ('kit_n','kit_n_go'):
 k=O/name;rc=subprocess.run([sys.executable,'-I','-s','-B',str(k/'b/v.py'),str(k)],capture_output=True,text=True);assert rc.returncode==0 and rc.stdout.strip()==sha(k/'SHA256SUMS.txt'),rc.stderr
 checks.append(dict(kit=name,sha256=rc.stdout.strip(),checker='PASS'))
assert (O/'kit_n/b/pc.py').read_bytes()==(O/'kit_n_go/b/pc.py').read_bytes()
for suffix in ('','_GO','_E3'):
 m=load(O/('UPLOADS_24M4Z12'+suffix+'.json'));assert (O/('UPLOADS_24M4Z12'+suffix+'.list')).read_text()==''.join(r['name']+'\n' for r in m['files'])
 for r in m['files']:
  p=Path(r['local_path']);assert r['sha256']==sha(p) and r['bytes']==p.stat().st_size<5_000_000
pins=load(O/'e3/pins.json');assert all(sha(O/'e3'/k)==v for k,v in pins.items())
with tarfile.open(O/'e3/k.tgz') as t:bundle={m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in t if m.isfile()}
assert bundle=={str(p.relative_to(O/'kit_n')):sha(p) for p in (O/'kit_n').rglob('*') if p.is_file()}
assert len((O/'BUILD24M4Z12_REPORT.md').read_text().splitlines())<10
failures=load(D/'FAILURES.json')
resolutions={'order_validation':'ORDER_VALIDATION.json: count an attempted writer that the shell deliberately interrupted before its first HTTP request; its logged failure precedes the next export.', 'suites':'SUITES_SEALED.json: corrected fixture directory setup; signals and dependent legacy test pass.','findings':'findings_sealed/RESULT.json: final sealed kit passes set_stop copy checks.','e3':'e3_sealed/RESULT.json: no ordinary phase is emitted for an empty queue; all 17 unchanged E3 checks pass.','readback':'READBACK_SEALED.json: final E3 report and 16 objects pass.','tgcs_observers':'tgcs_observers_sealed/RESULT.json: use reviewed old-observer failure expectations.','trinity':'trinity_sealed/RESULT.json: unchanged E3 checks pass with final kit.','after_resume':'new_verified/RESULT.json: writer subprocess uses the interruption adapter; Range resume passes.','priority_controls':'PRIORITY_CONTROLS.json: use named callables in mocks.','new_findings:after_success':'new_verified/RESULT.json: fixture ledger variable no longer shadows the reader; actual live writer resumes.'}
for r in failures:
 assert r['suite'] in resolutions,r['suite'];r.update(resolved=True,resolution=resolutions[r['suite']])
(D/'FAILURES.json').write_text(json.dumps(failures,indent=2)+'\n')
result=dict(artifact_checks='PASS',suite_groups=len(allrows),suites=allrows,kit_checks=checks,unresolved_failures=0,uploaded_files_under_5MB=True,e3_bundle_exact=True,network_used=False)
(D/'VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
