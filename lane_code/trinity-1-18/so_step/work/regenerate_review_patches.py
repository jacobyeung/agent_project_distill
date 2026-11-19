"""Build a four-part ordered series from bounded source-file snapshots, without Git."""
import difflib
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'in/tree/work/tree_r1'
TREE=ROOT/'work/tree'
OUT=ROOT/'out/patches'
carrier='student_pilot/carrier_c1_run.py'
original=(BASE/carrier).read_text()
final=(TREE/carrier).read_text()

def optimize(text):
    a=text.index('def optimize_step(')
    b=text.index('\n\ndef dryrun(',a)
    return a,b,text[a:b]

a,b,old_step=optimize(original)
c,d,new_step=optimize(final)
stage1=final[:c]+old_step+final[d:]
cache_block="""    cache_record = {}
    if performance_switch('C1_DECODED_CACHE_MIB') != '0':
        from .c1_decoded_cache import stats
        cache_record['decoded_cache'] = stats()
"""
stage2=stage1.replace("    return dict(step=step, **({'gf1_harm_screen'",cache_block+"    return dict(step=step, **cache_record, **({'gf1_harm_screen'")
assert stage2 != stage1
stages=[
 ('01_cpu_prefetch.diff',dict([(carrier,stage1)]+[(p,(TREE/p).read_text()) for p in (
  'student_pilot/c1_cpu_prefetch.py','student_pilot/c1_switches.py','tests/so_helpers.py',
  'tests/so_processor.py','tests/test_so_prefetch.py','tests/test_so_review.py',
  'tests/test_carrier_c1_run.py','tests/test_gx_carrier.py','tests/test_gx_s6.py',
  'tests/test_gx_s7.py','tests/test_gx_s8.py','tests/test_carrier_c1_t0.py')])),
 ('02_decoded_rgb_cache.diff',dict([(carrier,stage2)]+[(p,(TREE/p).read_text()) for p in (
  'student_pilot/c1_decoded_cache.py','student_pilot/pose_samples.py','student_pilot/batches.py','tests/test_so_cache.py')])),
 ('03_batch_metrics.diff',dict([(carrier,final)]+[(p,(TREE/p).read_text()) for p in (
  'student_pilot/c1_batch_metrics.py','tests/test_so_metrics.py','tests/test_so_joint.py')])),
]
joint='tests/test_so_joint.py'
fixed=stages[2][1][joint]
unfixed=fixed.replace('source.detach().contiguous().reshape(-1).view(torch.uint8)',
                      'source.detach().contiguous().view(torch.uint8)')
assert fixed != unfixed
stages[2][1][joint]=unfixed
stages.append(('04_test_joint_hash_0dim.diff',{joint:fixed,
    'tests/test_so_round2.py':(TREE/'tests/test_so_round2.py').read_text()}))
state={}
manifest={}
for name, files in stages:
    pieces=[]
    for path,new in files.items():
        old=state.get(path,(BASE/path).read_text() if (BASE/path).exists() else '')
        pieces.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),
                      fromfile='a/'+path if old else '/dev/null',tofile='b/'+path))
        state[path]=new
    payload=''.join(pieces).encode()
    (OUT/name).write_bytes(payload)
    manifest[name]=dict(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),paths=list(files))
    print(name,len(payload),manifest[name]['sha256'])
manifest['_application']=dict(method='Apply 01, 02, 03, 04 in this order to the untouched input with patch --batch --fuzz=0 -p1. Each patch is relative to the preceding stage; 04 stays separate.',
    test_method='Run all tests.test_so_* modules after the complete series. Shared switch validation ships in 01. Two-rank gloo rerun is assigned to the coordinator outside the sandbox.',
    defaults={'C1_CPU_PREFETCH':'0','C1_DECODED_CACHE_MIB':'0','C1_BATCH_METRICS':'0'},
    input_root=str(BASE), base_pin=json.loads((ROOT/'in/tree/out/TREE_SEAL.json').read_text()),
    input_sha256={p:hashlib.sha256((BASE/p).read_bytes()).hexdigest() if (BASE/p).exists() else None for p in state},
    patch_04='kept separate; scalar collective hashing and round-2 regression tests')
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for path,text in state.items():
    assert (TREE/path).read_text()==text,path
print('SERIES_GENERATED: four ordered patches; final touched files match work/tree')
