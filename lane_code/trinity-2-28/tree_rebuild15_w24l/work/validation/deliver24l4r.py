"""Seal the tested role-list change and replay its patch without Git or deletion."""
import ast
from collections import Counter
import difflib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tarfile

J=Path(__file__).resolve().parents[2]
T=J/'work/tree_r1';B=J/'work/tree_r1_24l3';O=J/'out'
sys.path.insert(0,str(T))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest,sha256


def put(name,value):
    with (O/name).open('x') as f:f.write(json.dumps(value,indent=2,sort_keys=True)+'\n')


def read(name):return json.loads((O/name).read_text())

before,after=inventory(B),inventory(T)
base='96ff9a03ae3be43972e060050ab411967e99dc312dc1380fe1c73435bbecebbf'
assert digest(before)==base and len(before)==943
assert before==read('TREE24L3_SEAL.json')['files']
seal=digest(after)
changed=[n for n in sorted(before.keys()|after.keys()) if before.get(n)!=after.get(n)]
expected=['launch_s1/build.py','student_pilot/carrier_c1_data.py','student_pilot/carrier_c1_run.py',
 'student_pilot/ground_target_filter.py','student_pilot/r1_launch22.py','student_pilot/r1_rooms.py',
 'student_pilot/r1_routing.py','student_pilot/row_removals.py','student_pilot/s1_pool.py',
 'student_pilot/s1_routing.py','student_pilot/scene_division_gate.py','tests/test_host24l4r.py']
assert changed==expected and len(after)==944
assert not before.keys()-after.keys()
for name in changed:compile((T/name).read_text(),name,'exec')
protected={}
for name,names in {
 'student_pilot/carrier_c1_run.py':['identity','validate','Rows','train'],
 'student_pilot/r1_rooms.py':['Rooms','verify_audit'],
 'student_pilot/r1_launch22.py':['bound','naming_rows','REMOVAL_ORDER','NAMING_REMOVE'],
 'student_pilot/row_removals.py':['row_keys'],
 'launch_r1/entry.py':['admit','frame_host'],
 'student_pilot/r1_coverage.py':['verify_union','validate_binding','deferred'],
}.items():
    for symbol in names:
        hashes=[]
        for root in (B,T):
            text=(root/name).read_text();nodes=ast.parse(text).body
            node=next(n for n in nodes if getattr(n,'name',None)==symbol or
                      isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==symbol for t in n.targets))
            hashes.append(hashlib.sha256(ast.get_source_segment(text,node).encode()).hexdigest())
        assert hashes[0]==hashes[1],(name,symbol)
        protected[name+':'+symbol]=dict(before=hashes[0],after=hashes[1],identical=True)
# Verify that the three preparation changes only forward removal stream context.
source=(B/'student_pilot/carrier_c1_run.py').read_text()
source=source.replace('removals.assert_clean(row)','removals.assert_clean(row, name)')
source=source.replace('removals.assert_clean(dict(row_key=pointing_key(row)))',"removals.assert_clean(dict(row_key=pointing_key(row)), 'pointing')")
source=source.replace('removals.assert_clean(json.loads(row))',"removals.assert_clean(json.loads(row), 'pose')")
assert source==(T/'student_pilot/carrier_c1_run.py').read_text()

focused=read('focused_final24l4r.json');new=read('protected_release24l4r.json');legacy=read('legacy_removals24l4r.json')
for value,count in ((focused,80),(new,37),(legacy,4)):
    assert value['tests_run']==len(value['passed'])==count
    assert not value['errors'] and not value['failures'] and not value['skipped']
hosts=[n for n in focused['passed'] if not n.startswith('tests.test_host24l4r.')]
assert len(hosts)==44
old,scoped=read('regression_base24l4r.json'),read('regression_after24l4r.json')
def outcomes(v):
    return (v['tests_run'],sorted(v['passed']),sorted((e['test'],e['traceback'].strip().splitlines()[-1]) for e in v['errors']),v['failures'],v['skipped'])
assert outcomes(old)==outcomes(scoped)==outcomes(read('regression_snapshot24l3.json'))
assert scoped['tests_run']==110 and len(scoped['passed'])==50 and len(scoped['errors'])==60
causes=Counter(e['traceback'].strip().splitlines()[-1] for e in scoped['errors'])
assert all(c.startswith('FileNotFoundError:') for c in causes)
evidence=['focused_final24l4r.json','focused_final24l4r.log','protected_release24l4r.json','protected_release24l4r.log',
 'legacy_removals24l4r.json','legacy_removals24l4r.log','regression_base24l4r.json','regression_base24l4r.log',
 'regression_after24l4r.json','regression_after24l4r.log']
put('TESTS24L4R.json',dict(new_tests_passed=37,host_tests_passed=44,legacy_removal_tests_passed=4,
    unique_focused_passed=85,focused_tests=sorted(set(hosts+new['passed']+legacy['passed'])),
    scoped_tests_run=110,scoped_passed=50,scoped_preexisting_errors=60,scoped_failures=0,
    base_outcomes_identical=True,error_causes=dict(causes),
    evidence={n:sha256(O/n) for n in evidence},
    limits='Synthetic authority hashes and naming-pin fixture; real Rooms parser/Withheld bytes. Some consumer integration expressions are isolated from model setup. No production census or launch.'))
put('TREE24L4R_SEAL.json',dict(tree_sha256=seal,commit='sha256:'+seal,file_count=len(after),files=after,
    base_tree_sha256=base,method='student_pilot.source_seal.inventory + student_pilot.p3_provenance.digest'))
put('UNCHANGED24L4R.json',dict(before_tree_sha256=base,after_tree_sha256=seal,changed=changed,
    files={n:dict(before=before.get(n),after=after.get(n),unchanged=before.get(n)==after.get(n)) for n in sorted(before.keys()|after.keys())},
    protected_functions=protected,prepare_and_prepared_only_forward_stream_context=True,
    native_postcondition_wired=False))

chunks=[]
for name in changed:
    oldlines=(B/name).read_text().splitlines(keepends=True) if name in before else []
    newlines=(T/name).read_text().splitlines(keepends=True)
    chunks.extend(difflib.unified_diff(oldlines,newlines,fromfile='a/'+name if name in before else '/dev/null',tofile='b/'+name))
patchtext=''.join(chunks)
with (O/'HOST24L4R.patch').open('x') as f:f.write(patchtext)
lines=patchtext.splitlines(keepends=True);i=0;rebuilt={}
while i<len(lines):
    assert lines[i].startswith('--- ');oldname=lines[i][4:].strip();i+=1
    assert lines[i].startswith('+++ b/');name=lines[i][6:].strip();i+=1
    oldlines=(B/name).read_text().splitlines(keepends=True) if oldname!='/dev/null' else []
    result=[];cursor=0
    while i<len(lines) and not lines[i].startswith('--- '):
        m=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',lines[i]);assert m
        start,count=int(m[1]),int(m[2] or 1);position=start-1 if count else start
        result.extend(oldlines[cursor:position]);cursor=position;i+=1
        while i<len(lines) and not lines[i].startswith(('@@ ','--- ')):
            op,line=lines[i][0],lines[i][1:]
            if op in (' ','-'):assert oldlines[cursor]==line;cursor+=1
            if op in (' ','+'):result.append(line)
            i+=1
    result.extend(oldlines[cursor:]);rebuilt[name]=hashlib.sha256(''.join(result).encode()).hexdigest()
    assert rebuilt[name]==after[name]
assert set(rebuilt)==set(changed)
put('PATCH_CHECK24L4R.json',dict(status='PASS',before_tree_sha256=base,after_tree_sha256=seal,
    files=rebuilt,method='Unified hunks replayed against the 96ff9a03 base in memory.'))
archive=O/f'tree_rebuild_b24l4r_{seal[:8]}.tar'
report=[
 f'New seal: {seal}; 944 files; base {base}.',
 'Consumers checked: validator, matcher, prepare/rank 0, builders, shared pool, scene/room audits, coverage/union, counts, receipts, naming and staging; 11 production files change (API table lists each).',
 'Native admission does not call the post-condition; complete source and selected-store readers need more than a one-call integration. The kit must call it before launch.',
 'The 12 pinned lists retain their exact order and final NAMING_REMOVE; protected_rooms entries occupy only the gap after pin 11 and carry an authenticated SHA256 plus a recognized stream.',
 'The sealed prefix retains its two empty-list SHA duplicates; every added SHA must be unique and absent from the sealed pins.',
 'Legacy lists remain global. Role lists affect only their declared stream; shared source intake defers them until final VQA/routing materialization.',
 'check_protected_rooms(cfg, stream, source_rows, admitted_rows) returns source/admitted counts, list/key counts and protected_rows=0; PROTECTED_ROOMS_API.md specifies all inputs, returns, refusals and kit adapters.',
 'The check verifies each listed key in its complete source, rejects every protected admitted row, uses pointing provenance.canonical_scene and authenticates K1/R0 and withheld-80 authorities.',
 'Unresolved admitted rooms refuse. The caller binds complete input iterables and store pins; no production-store census was available in this workspace.',
 'Identity is unchanged and tests prove that role and stream affect its digest. Naming parsing, union validation, Rooms authority, host admit and unrelated policies remain unchanged.',
 'All 85 distinct focused tests pass: 37 role/post-condition/consumer tests, 44 retained 24j/24l/24n/24l3 tests, and 4 legacy removal/target-filter tests.',
 'Both base and final scoped suites run 110 tests: 50 pass and the same 60 error on absent archived fixtures; no new failure or skip occurs.',
 'TESTS24L4R.json records every outcome and missing-fixture cause; 35 scoped errors require work/base/tree_b01ce449/student_pilot/carrier_c1_run.py.',
 'Some integration tests execute native consumer expressions to isolate model/archived-fixture setup; real synthetic list bytes, SQLite selection, Rooms parsing and bundled withheld aliases are exercised.',
 'The kit must add discovered lists, update removal_order/config identity and dependent seals/receipts, preserve role metadata during staging, filter final streams and bind the native census results.',
 'The untouched base remains 96ff9a03; the stopped work is preserved at work/tree_r1_24l4_stopped. BEFORE24L4R.json records both checked seals.',
 'UNCHANGED24L4R.json records every file hash; HOST24L4R.patch replays exactly against the sealed base. No files were deleted.',
 f'Delivery: {archive.name}; the archive contains work/tree_r1, retained 24l3 reports and all final 24l4r evidence.',
 'All work stayed under J on trinity-2-28 with nice 10, one-thread library limits and a 19,000,000-KiB process memory ceiling; no Git, network, SSH, GPU or other agent was used.',
]
assert len(report)<25
with (O/'BUILD24L4R_REPORT.md').open('x') as f:f.write('\n'.join(report)+'\n')
# Retain the exact out reports delivered by 24l3, without nesting any tree archive.
retained=read('DELIVERY_MANIFEST24L3.json')['members']
files={'work/tree_r1/'+n:T/n for n in after}
for name,h in retained.items():
    if name.startswith('out/'):
        assert sha256(J/name)==h,name
        files[name]=J/name
files['out/DELIVERY_MANIFEST24L3.json']=O/'DELIVERY_MANIFEST24L3.json'
final_reports=['BEFORE24L4R.json','HOST24L4R.patch','TREE24L4R_SEAL.json','UNCHANGED24L4R.json',
 'PROTECTED_ROOMS_API.md','BUILD24L4R_REPORT.md','TESTS24L4R.json','PATCH_CHECK24L4R.json',*evidence]
for name in final_reports:files['out/'+name]=O/name
for name in ('run_tests.py','scoped24l3.py','deliver24l4r.py'):
    files['work/validation/'+name]=J/'work/validation'/name
manifest={n:sha256(p) for n,p in sorted(files.items())}
put('DELIVERY_MANIFEST24L4R.json',dict(tree_sha256=seal,members=manifest))
files['out/DELIVERY_MANIFEST24L4R.json']=O/'DELIVERY_MANIFEST24L4R.json'
with tarfile.open(archive,'x') as tar:
    for name,path in sorted(files.items()):
        raw=path.read_bytes();info=tarfile.TarInfo(name);info.size=len(raw)
        info.mode=0o755 if os.access(path,os.X_OK) else 0o644
        tar.addfile(info,io.BytesIO(raw))
with tarfile.open(archive,'r') as tar:
    actual={m.name:hashlib.sha256(tar.extractfile(m).read()).hexdigest() for m in tar}
assert actual=={n:sha256(p) for n,p in files.items()}
assert inventory(B)==before and inventory(T)==after
put('PACKAGE_CHECK24L4R.json',dict(status='PASS',tree_sha256=seal,archive=archive.name,
    archive_sha256=sha256(archive),archive_bytes=archive.stat().st_size,archive_members=len(actual),
    every_member_verified=True,patch_replay=True,base_unchanged=True))
print(json.dumps(dict(status='PASS',seal=seal,files=len(after),changed=len(changed),focused_passed=85,
    scoped_passed=50,preexisting_errors=60,archive=archive.name,archive_bytes=archive.stat().st_size)))
