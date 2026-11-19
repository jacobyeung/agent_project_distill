from pathlib import Path
import collections,hashlib,json,re
W=Path(__file__).resolve().parents[1];O=W/'out'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(name):return json.loads((O/name).read_text())
def norm(text):
 text=re.sub(re.escape(str(W))+r'/work/(?:live_base|live|base|new)(?=/)', '<tree>',text)
 text=re.sub(re.escape(str(W))+r'/work/(?:suite_final|focused)_(?:live_base|live|base|new)/[^/\s\"\']+/', '<fixture>/',text)
 # This test requests a forbidden /tmp directory; only its generated suffix differs.
 text=re.sub(r'/tmp/headcall_test_cache/hcfull_frames_[a-z0-9_]{8}(?=$|[ /\"\'])', '/tmp/headcall_test_cache/hcfull_frames_<temporary>', text)
 # Paths in test-produced exception descriptions sometimes name the runner output directory itself.
 return re.sub(r'(?:suite_final|focused)_(?:live_base|live|base|new)', '<suite>',text)
def events(r):
 result=[]
 for kind in ('errors','failures'):
  for name,trace in r[kind]:
   if name=='failed' or 'raise RuntimeError(message)' in trace:
    paths=re.findall(r'/work/(?:live_base|live|base|new)/(tests/[^"\n]+\.py)',trace)
    name='collection:'+paths[0].replace('/','.') if paths else 'collection:'+trace.splitlines()[-1]
   lines=trace.strip().splitlines();marks=[i for i,line in enumerate(lines) if re.match(r'^(?:[\w.]+(?:Error|Exception)|SystemExit):',line)]
   cause=' '.join(lines[marks[-1]:]) if marks else lines[-1]
   result.append(dict(test=norm(name),kind=kind,cause=norm(cause),traceback=trace))
 return result
def compare(a,b):
 x,y=events(a),events(b)
 signatures=lambda rows:collections.Counter((v['test'],v['kind'],v['cause']) for v in rows)
 added=signatures(y)-signatures(x)
 return dict(status='PASS' if not added else 'FAIL',new_failure_signatures=[dict(test=k[0],kind=k[1],cause=k[2],count=v) for k,v in added.items()],preexisting=x)
def counts(r):return dict(tests_run=r['tests_run'],errors=len(r['errors']),failures=len(r['failures']),skips=len(r['skipped']),seconds=r['seconds'],command=r['command'])
reports={n:read(n+'.json') for n in ('SUITE_BASE_FINAL','SUITE_NEW_FINAL','FOCUSED_BASE','FOCUSED_NEW','FOCUSED_LIVE_BASE','FOCUSED_LIVE')}
pairs={name:compare(reports[a],reports[b]) for name,a,b in [('full','SUITE_BASE_FINAL','SUITE_NEW_FINAL'),('focused','FOCUSED_BASE','FOCUSED_NEW'),('live_focused','FOCUSED_LIVE_BASE','FOCUSED_LIVE')]}
unit_counts={}
for name in ('unit_final.log','unit_live.log'):
 s=(O/name).read_text();assert s.strip().endswith('OK'),name;unit_counts[name]=int(re.search(r'Ran (\d+) tests',s)[1])
parity=read('PARITY_base.json')['outputs']==read('PARITY_new.json')['outputs'];assert parity
assert read('ABSENT_BASE.json')['outputs']==read('ABSENT_NEW.json')['outputs']
k1=read('K1_INVARIANCE.json');assert k1['status']=='PASS'
assert all(a['scale_before']!=b['scale_before'] for a,b in zip(k1['variants'][0]['captures'],k1['variants'][1]['captures']))
assert all(c['invariance_assertion_caught'] and c['leaky_v1_status']=='FAIL' for c in k1['variants'][0]['negative_control'])
for n in ('EXPORT_CHECK_V1.json','EXPORT_CHECK_V2.json','ADVERSARIAL.json','PATCH_APPLICATION.json'):assert read(n)['status']=='PASS'
a,b=read('EXPORT_CHECK_V1.json'),read('EXPORT_CHECK_V2.json');assert all(x['scale']!=y['scale'] for x,y in zip(a['before'],b['before']))
source_checks={}
for name,r in reports.items():
 expected={p:h for p,h in r['input_sha256'].items() if '/work/' in p and Path(p).is_relative_to(W/'work')}
 changed=[p for p,h in expected.items() if sha(p)!=h];assert not changed,changed
 source_checks[name]=dict(files=len(expected),all_recorded_sources_unchanged=True)
inputs={str(O/(n+'.json')):sha(O/(n+'.json')) for n in reports}
for n in ('unit_final.log','unit_live.log','PARITY_base.json','PARITY_new.json','ABSENT_BASE.json','ABSENT_NEW.json','K1_INVARIANCE.json','EXPORT_CHECK_V1.json','EXPORT_CHECK_V2.json','ADVERSARIAL.json','BASE_NEGATIVE.json','ENVIRONMENT.json','FILES_TOUCHED.json','PATCH_APPLICATION.json','READER_SOURCE_HASHES.json','S1_STATUS.json','K1_SELECTION.json','MISSING_INPUTS.json','INPUTS.json'):
 inputs[str(O/n)]=sha(O/n)
inputs[str(Path(__file__).resolve())]=sha(__file__)
par=read('PARITY_base.json')['outputs']
r=dict(input_sha256=inputs,status='PASS' if all(x['status']=='PASS' for x in pairs.values()) else 'FAIL',scope='M1-M3/S2/S3 and regression validation; S1 remains documented; no production weight or launch claim.',suites={k:counts(v) for k,v in reports.items()},comparisons=pairs,source_checks=source_checks,unit_tests=unit_counts,field_absent=dict(status='PASS',state_tensors=len(par['state2']),optimizer_tensors=len(par['opt2']),exported_head_tensors=len(par['export_heads']),scope='both decode arms before/after two native steps/after reload; groups by name; handover table; model and optimizer state; exported heads and artifact keys'),K1=dict(status='PASS',captures=len(k1['variants'][0]['captures']),anchor_frames=len([p for p in read('K1_SELECTION.json')['input_sha256'] if p.startswith('/scratch/jjyeung/k1_frames/')]),steps_per_variant=2,variants=['V1','V2'],variant_scales_differ=True,leaky_v1_negative_control='FAIL on both captures as required; caught by invariance assertion',real_weights='MISSING'),items=dict(M1='PASS',M2='PASS: byte-identity requirement and all nine file hashes documented; enforcement preserved',M3='PASS: actual mdg_runtime strict load tested with/without metadata preprocessing; legacy R2 guard remains',S1='DOCUMENTED_NOT_IMPLEMENTED: native resume requires a legality transition',S2='PASS: default heads hash once; follower skips heads hash; both mmap and verify tensors/features/visuals',S3='PASS: top-level scale_donor binding and configurable PYTHON'),command='python code/assemble_final.py',normalization='Compare exception signatures after normalizing tree roots and generated fixture directory names, including the eight-character hcfull_frames suffix in the same forbidden /tmp path. Preserve every test identity, exception type and remaining cause.')
(O/'TESTS.json').write_text(json.dumps(r,indent=2)+'\n')
lines=['# Pre-existing failures and errors','', 'Each entry retains the full traceback in TESTS.json. The commands are recorded in each suite JSON.','']
for label in ('full','focused','live_focused'):
 lines+=['## '+label,'']
 for x in pairs[label]['preexisting']:lines.append(f"- `{x['test']}` ({x['kind']}): {x['cause']}")
 lines.append('')
(O/'PREEXISTING_FAILURES.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(status=r['status'],suites=r['suites'],new_failures={k:v['new_failure_signatures'] for k,v in pairs.items()}),indent=2))
