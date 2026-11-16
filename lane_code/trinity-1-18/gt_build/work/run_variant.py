"""Run a declared ARKit builder variant on named captures (<=24 procs). usage: run_variant.py NAME BUILDER.py SRCSET CID..."""
import json, os, subprocess, sys, hashlib
from concurrent.futures import ThreadPoolExecutor
G = '/scratch/jjyeung/orch_n30/gt_build'; W = G + '/work'; PY = '/scratch/jjyeung/envs/p1cpu/bin/python'
name, builder, srcset, cids = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
P = {r['canonical']: r for r in json.load(open(W + '/cr/PILOT300_INPUTS.json'))}
C = {p['canonical']: p['gt']['expected_sha256'] for p in json.load(open('/scratch/jjyeung/orch_cd/k1_build/work/kit_k1a/out/CAPTURES.json'))['pilot']}
od = f'{G}/out/variants/{name}'; os.makedirs(od, exist_ok=True)
env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
def run(c):
    r = P['arkitscenes/' + c]; out = f'{od}/{c}.npz'
    if not os.path.exists(out):
        p = subprocess.run([PY, builder, c, f'{W}/{srcset}/{c}/src', out, json.dumps(r['grid'])], env=env, capture_output=True, text=True)
        if p.returncode: return dict(c=c, rc=p.returncode, err=p.stderr[-300:])
    h = hashlib.sha256(open(out, 'rb').read()).hexdigest()
    return dict(c=c, sha=h, match=h == C['arkitscenes/' + c])
with ThreadPoolExecutor(min(24, len(cids))) as ex, open(f'{G}/logs/VARIANT_{name}.jsonl', 'a') as log:
    res = list(ex.map(run, cids))
    for x in res: log.write(json.dumps(x) + '\n')
print(name, 'match', sum(bool(x.get('match')) for x in res), 'of', len(res), 'fail', [x for x in res if x.get('rc')])
