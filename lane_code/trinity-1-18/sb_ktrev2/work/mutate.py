"""Mutation probe of the fixed kit's tests on a local copy (work/kitcopy); never touches sb_ktfix.
M1-M12 are the first review's mutations verbatim; N1-N9 target the sb_ktfix edits."""
import subprocess, json, os
from pathlib import Path
W = Path('/scratch/jjyeung/orch_n30/sb_ktrev2/work')
K = W / 'kitcopy'
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
 ('N1 NO_CONVERT_EXPORT guard removed', 'code/evaluate_v2.py', " if not gp.is_file():return dict(", " if False:return dict("),
 ('N2 scale assertion disabled', 'code/evaluate_v2.py', "assert r['relative_error']<=1e-4, 'C64", "assert True, 'C64"),
 ('N3 placeholder DECISION kept', 'code/evaluate_v2.py', " if d.get('status')=='MISSING':d=dict(bars={},complete={})\n", ""),
 ('N4 added-frame verdict accepts zero', 'code/evaluate_v2.py', "'PASS' if afg['low']>0 else 'FAIL'", "'PASS' if afg['low']>=0 else 'FAIL'"),
 ('N5 camera license reverted to pose-or-lifting', 'code/metrics.py', "out['reader_C64_licensed']=out['context_pays_pose']", "out['reader_C64_licensed']='PASS' if out['context_pays_pose']=='PASS' or out['lifting']['status']=='PASS' else 'FAIL'"),
 ('N6 DA3 GO check removed', 'code/runner.py', "if not g.is_file() or 'GO' not in [l.strip() for l in g.read_text().splitlines()]:raise", "if False:raise"),
 ('N7 HALTED check removed before admit', 'code/runner.py', " if (OUT/f'HALTED_{part}.json').exists():raise RuntimeError('HALTED: operator review required; no automatic retry')\n from budget import admit\n try:", " from budget import admit\n try:"),
 ('N8 A0 row-set equality not asserted', 'code/kbox_hook.py', " assert {r['row_id'] for r in got}==set(ref), 'Produced", " assert True, 'Produced"),
 ('N9 NOT_ADMITTED receipt not written', 'code/runner.py', "  write_json(OUT/f'NOT_ADMITTED_{part}.json',", "  dict(OUT/f'NOT_ADMITTED_{part}.json',"),
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
    finally:
        p.write_text(src)
    print(res[-1], flush=True)
(W / 'mutations.json').write_text(json.dumps(res, indent=1))
print('killed', sum(x['killed'] for x in res), 'of', len(res), '| original 12:', sum(x['killed'] for x in res[:12]))
