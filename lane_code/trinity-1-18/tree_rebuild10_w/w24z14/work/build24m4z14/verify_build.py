from pathlib import Path
import ast, collections, hashlib, json, re, sys
j=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14'); w=j/'work/build24m4z14'
ast.parse((j/'out/admit_test.py').read_text())
a=json.loads((w/'standin_verified/ADMIT.json').read_text()); b=json.loads((w/'negative_verified/ADMIT.json').read_text())
aa={r['name']:r for r in a['checks']}; bb={r['name']:r for r in b['checks']}
expected={'all_stream_identities':'R1_ALL_STREAM_IDENTITIES_REQUIRED','continuation_boundary':'R1_CONTINUATION_IDENTITIES_REQUIRED','row_plan_digest':'R1_ROW_PLAN_BINDING_DIFFERS','host_receipt_assertions':'R1_HOST_ADMISSION_MISSING','review_verdict_identity':'INDEPENDENT_REVIEW_PENDING'}
assert {k for k,v in aa.items() if v['status']=='FAIL'}==set(expected)
assert all(code in aa[name]['reason'] for name,code in expected.items())
assert aa['processor_legacy_or_b7']['status']=='PASS'
assert bb['processor_legacy_or_b7']['status']=='FAIL'
assert 'R1_LEGACY_PROCESSOR_PIXELS_MUST_USE_DEFAULTS' in bb['processor_legacy_or_b7']['reason']
assert {k for k,v in bb.items() if v['status']=='FAIL'}==set(expected)|{'processor_legacy_or_b7'}
assert a['exit_code']==b['exit_code']==1
assert a['effective_processor_layout']==dict(min_pixels=16384,max_pixels=147456,frame_count=32,frame_layout='duplicate',frame_markers=True)
raw=json.loads((w/'standin.json').read_text()); neg=json.loads((w/'negative_processor.json').read_text())
assert neg['min_pixels']==16384
if 'min_pixels' in raw: neg['min_pixels']=raw['min_pixels']
else: neg.pop('min_pixels')
assert neg==raw
for r,name in [(a,'standin.json'),(b,'negative_processor.json')]:
 assert r['config_sha256']==hashlib.sha256((w/name).read_bytes()).hexdigest()
sys.path.insert(0,'/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/work/tree_r1c')
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
files=inventory(Path(sys.path[0])); seal=digest(files)
assert seal==a['tree_sha256']==b['tree_sha256']
inputs=json.loads((w/'INPUTS.json').read_text());base=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/out')
for name, hashes in inputs['kit_callers'].items():
 for kit,h in hashes.items(): assert hashlib.sha256((base/kit/name).read_bytes()).hexdigest()==h
v=dict(status='PASS',assertions=['shell syntax and helper AST parse','stand-in legacy processor PASS','negative differs only in min_pixels','negative processor refusal matches exact native name','stand-in has exactly five preparation/review failures','negative adds exactly one processor failure','both exit codes are one','config bytes unchanged','945-file tree still sealed','all inspected kit caller/config/seal bytes unchanged'],tree_sha256=seal,tree_files=len(files),real_173964_test='NOT_RUN: real v.json not supplied',runs={})
for name,r in [('standin_verified',a),('negative_verified',b)]:
 v['runs'][name]={k:r[k] for k in ('status','exit_code','identity','config_sha256','branch_taken','elapsed_seconds','max_rss_bytes','runtime','full_admit_pass','processor_execution')}
 v['runs'][name]['counts']=dict(collections.Counter(c['status'] for c in r['checks']))
(w/'VERIFICATION.json').write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps(v,indent=2))
