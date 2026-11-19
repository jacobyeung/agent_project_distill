"""Rebuild ordered build-21 patches and prove zero-offset/fuzz replay without Git."""
import ast
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=Path('/scratch/jjyeung/orch_n30/so_xstore/in/tree21b')
BASE=PACKAGE/'work/tree_r1'
TREE=ROOT/'work/b21_final/work/tree_r1'
OLD=ROOT/'out_round3/patches_b21'
OUT=ROOT/'out/patches_b21'
STAGE=ROOT/'work/round3_old_stages'
BEFORE=ROOT/'work/round3_before/work/tree_r1'
REPLAY=ROOT/'work/round3_replay'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seal=json.loads((PACKAGE/'out/TREE_SEAL.json').read_text())
pins=dict(line.split('  ',1)[::-1] for line in (PACKAGE/'out/TREE_FILES.sha256').read_text().splitlines())
assert hashlib.sha256(json.dumps(pins,sort_keys=True,separators=(',',':')).encode()).hexdigest()==seal['tree_sha256']=='b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8'
old=json.loads((OLD/'manifest.json').read_text())
paths=set(old['_application']['output_sha256'])|{'tests/test_so_round3.py'}
for directory in (STAGE,BEFORE,REPLAY): directory.mkdir(parents=True,exist_ok=False)
for relative,expected in pins.items():
    assert sha(BASE/relative)==expected,relative
    target=BEFORE/relative;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(BASE/relative,target)
    if relative in paths:
        for directory in (STAGE,REPLAY):
            target=directory/relative;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(BASE/relative,target)
print(f'BASE_PIN_PASS: {len(pins)} files, {seal["tree_sha256"]}',flush=True)
state={p:(BASE/p).read_text() if (BASE/p).exists() else '' for p in paths}
manifest={}
for number,(name,item) in enumerate((v for v in old.items() if v[0].endswith('.diff')),1):
    for directory in (STAGE,BEFORE):
        result=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(OLD/name)],cwd=directory,capture_output=True,text=True)
        assert result.returncode==0 and 'offset' not in result.stdout and 'fuzz' not in result.stdout,(name,result.stdout,result.stderr)
    stage={p:(STAGE/p).read_text() for p in item['paths']}
    if number==1:
        for p in ('student_pilot/c1_switches.py','student_pilot/c1_cpu_prefetch.py','tests/test_carrier_c1_t0.py'):
            stage[p]=(TREE/p).read_text()
    if number==3:
        stage['student_pilot/carrier_c1_run.py']=(TREE/'student_pilot/carrier_c1_run.py').read_text()
        stage['tests/test_so_joint.py']=(TREE/'tests/test_so_joint.py').read_text().replace(
            'source.detach().contiguous().reshape(-1).view(torch.uint8)', 'source.detach().contiguous().view(torch.uint8)')
    if number==4:
        for p in ('tests/test_so_joint.py','tests/test_so_round3.py'):
            stage[p]=(TREE/p).read_text()
    parts=[]
    for p,new in stage.items():
        previous=state[p]
        parts.extend(difflib.unified_diff(previous.splitlines(True),new.splitlines(True),
            fromfile='a/'+p if previous else '/dev/null',tofile='b/'+p))
        state[p]=new
    payload=''.join(parts).encode();(OUT/name).write_bytes(payload)
    manifest[name]=dict(sha256=hashlib.sha256(payload).hexdigest(),bytes=len(payload),paths=list(stage),base_pin=seal['tree_sha256'])
    replay=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(OUT/name)],cwd=REPLAY,capture_output=True,text=True)
    print('REPLAY '+name+'\n'+replay.stdout+replay.stderr+'EXIT='+str(replay.returncode),flush=True)
    assert replay.returncode==0 and 'offset' not in replay.stdout and 'fuzz' not in replay.stdout
for p in paths:
    assert (TREE/p).read_text()==state[p]==(REPLAY/p).read_text(),p
    ast.parse(state[p],filename=p)
for p,expected in pins.items():
    if p not in paths: assert sha(TREE/p)==expected,p
manifest['_application']=dict(old['_application'])
manifest['_application'].update(method='Apply 01, 02, 03, 04 in order with patch --batch --fuzz=0 -p1; build 21 only, zero offsets/fuzz.',
    defaults=dict(old['_application']['defaults'],C1_CPU_PREFETCH_FALLBACK='0'),
    input_sha256={p:pins.get(p) for p in sorted(paths)},output_sha256={p:sha(TREE/p) for p in sorted(paths)},
    test_method='REPORT.md Coordinator command; local gates use SO_TEST_TREE='+str(TREE),
    patch_04='Scalar collective-hash repair, round-2 tests and round-3 tests; run tests after all four patches.')
candidate=dict(pins,**manifest['_application']['output_sha256'])
manifest['_application']['candidate_source_tree_sha256']=hashlib.sha256(json.dumps(candidate,sort_keys=True,separators=(',',':')).encode()).hexdigest()
manifest['_application']['candidate_source_files']=len(candidate)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Both delivery entry points are explicitly build 21; the archived bundle retains build 20.
for name in [*filter(lambda n:n.endswith('.diff'),manifest),'manifest.json']:
    shutil.copyfile(OUT/name,ROOT/'out/patches'/name)
shutil.copyfile(TREE/'tests/test_so_round3.py',BEFORE/'tests/test_so_round3.py')
for relative in ('base/tree_b01ce449','build15/inputs','build_n1/inputs'):
    target=BEFORE.parent/relative;target.parent.mkdir(parents=True,exist_ok=True)
    target.symlink_to(TREE.parent/relative,target_is_directory=True)
print(f'ROUND3_REPLAY_PASS: 4 patches, {len(paths)} touched files, {len(pins)-sum(p in pins for p in paths)} untouched files; zero fuzz and offsets',flush=True)
print('CANDIDATE_SOURCE: '+manifest['_application']['candidate_source_tree_sha256']+'; files='+str(len(candidate)),flush=True)
print('PATCHES_ALIAS: out/patches is byte-identical to out/patches_b21; both target build 21',flush=True)
