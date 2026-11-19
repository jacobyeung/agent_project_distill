"""Mutation probe of the kit's regression tests on a local copy (work/kitcopy); never touches sb_ktow3."""
import subprocess, json, os
from pathlib import Path
K = Path(__file__).resolve().parents[1]
M = [
 ('M1 printed frames use dense numbers', 'code/replay.py', "mapping={int(slot)+1:i+1 for i,slot in enumerate(anchor_slots)}\n return", "mapping={int(slot)+1:int(slot)+1 for i,slot in enumerate(anchor_slots)}\n return"),
 ('M2 pose bar sign flipped', 'code/metrics.py', "delta=100*(r['G64'][metric]-r['G32'][metric])", "delta=100*(r['G32'][metric]-r['G64'][metric])"),
 ('M3 added frame gain flipped', 'code/evaluate_v2.py', "{'added_frame_gain':(names[0],names[1])}", "{'added_frame_gain':(names[1],names[0])}"),
 ('M4 DECISION drops bars', 'code/evaluate_v2.py', "d.setdefault('bars',{})[part]=bars", "d.setdefault('bars',{})"),
 ('M5 heldout label guard removed', 'code/evaluate_v2.py', "if split=='heldout' and not _HELDOUT_ACTIVE:raise", "if False:raise"),
 ('M6 camera scale ignored', 'code/camera.py', "pose[:,:3]*=scale", "pose[:,:3]*=1"),
 ('M7 budget cap 17 h', 'code/budget.py', "used+active<=16*3600", "used+active<=17*3600"),
 ('M8 heldout before decision', 'code/policy.py', "if not d.get('train_complete'):raise", "if False:raise"),
 ('M9 lifting bar on wrong arm', 'code/metrics.py', "out['lifting']=verdict([r for r in distance_rows if r['arm']=='A2'])", "out['lifting']=verdict([r for r in distance_rows if r['arm']!='A2'])"),
 ('M10 A2 delta direction', 'code/evaluate_v2.py', "paired_scores(rows(32,'GTmask'),rows(64,'GTmask'))", "paired_scores(rows(64,'GTmask'),rows(32,'GTmask'))"),
 ('M11 resume ignores output hash', 'code/common.py', "all(sha(Path(directory)/k)==v for k,v in d['outputs'].items())", "True"),
 ('M12 dense anchor areas not remapped', 'code/replay.py', "areas={str(mapping[f]):r['areas'][str(f)] for f in shared}", "areas={str(mapping[f]):r['areas'][str(f)] for f in shared}|{str(f):1e9 for f in r['frames']}"),
]
env = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='8', TMPDIR=str(K / 'runtime/tmp'), XDG_CACHE_HOME=str(K / 'runtime'))
res = []
for name, f, old, new in M:
    p = K / f; src = p.read_text()
    assert src.count(old) == 1, (name, src.count(old))
    p.write_text(src.replace(old, new))
    try:
        r = subprocess.run(['nice', '-n', '10', '/scratch/jjyeung/envs/p1cpu/bin/python', '-B', 'code/test_kit.py'], cwd=K, env=env, capture_output=True, text=True, timeout=600)
        failed = [l.split(' ')[0] for l in r.stderr.splitlines() if l.endswith('FAIL') or l.endswith('ERROR')]
        res.append(dict(mutation=name, killed=r.returncode != 0, failing_tests=failed))
        (K/'out/fix_validation'/('mutation_'+name.split()[0]+'.log')).write_text(r.stdout+r.stderr)
    finally:
        p.write_text(src)
    print(res[-1], flush=True)
import sys
sys.path.insert(0,str(K/'code'))
from common import sha,write_json,code_pins
sha(__file__);sha(K/'work/reviewer_mutate_original.py');code_pins()
write_json(K/'out/fix_validation/mutations.json',dict(results=res,killed=sum(x['killed'] for x in res),total=len(res)))
print('killed', sum(x['killed'] for x in res), 'of', len(res))
