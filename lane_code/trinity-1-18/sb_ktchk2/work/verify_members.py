import json, hashlib, tarfile, difflib
from pathlib import Path
W = Path(__file__).resolve().parent
R3, R2 = W/'ex3', W/'ex2'
TAR3 = '/scratch/jjyeung/orch_n30/sb_ktfix2/out/sb_ktfix3.tar'
CLAIM = '47ecaeecd8f59f91190b28c05394e9b08ca48a997b86279710f400b099ec0fc2'
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()
def pins(R):
    DS = ('cpu.sh', 'gpu_environment.sh', 'run_A.sh', 'run_B.sh', 'run_C.sh', 'run_H.sh')
    paths = [p for p in (R/'code').rglob('*') if p.is_file() and p.suffix in ('.py', '.json', '.md')]
    paths += [p for p in (R/'configs').glob('*.json') if p.name != 'CODE_REVIEW.json']
    paths += [R/'scripts'/n for n in DS] + [R/'scripts'/n for n in ('finalize_v3.py', 'bind_camera.py')]
    paths += [R/'inputs/CAMERA_FRAME_JOINS.json', R/'inputs/TASK_RULINGS.txt']
    paths += [R/'inputs'/n for n in ('V2_SOURCES.json', 'KIT_SPEC_tower_frames_v2.md', 'pose_k1.py')]
    paths += list((R/'inputs/K1_ROWSETS').glob('*'))
    paths += [p for p in (R/'inputs/exclusions').rglob('*') if p.is_file()]
    return {str(p.relative_to(R)): sha(p) for p in sorted(paths)}
dg = lambda x: hashlib.sha256(json.dumps(x, sort_keys=True, allow_nan=False).encode()).hexdigest()
t = tarfile.open(TAR3); mem = t.getmembers()
names = [m.name for m in mem if m.isfile()]
m = json.load(open(R3/'out/FIX3_MEMBERS.json')); mf = m['files'] if 'files' in m else m
bad = [k for k, v in mf.items() if sha(R3/k) != v]
p3, p2 = pins(R3), pins(R2)
c = json.load(open(R3/'out/CODE_SHA256.json'))
res = dict(tar_members=len(mem), non_file=[x.name for x in mem if not x.isfile()], manifest_files=len(mf), hash_mismatch=bad,
           in_tar_not_manifest=sorted(set(names) - set(mf)), in_manifest_not_tar=sorted(set(mf) - set(names)),
           code_files=len(p3), code_sha256=dg(p3), matches_claim=dg(p3) == CLAIM, old_code_sha256=dg(p2),
           code_json=c.get('code_sha256'), pin_diffs_vs_CODE_SHA256_json=sorted(k for k in set(p3) | set(c['files']) if p3.get(k) != c['files'].get(k)))
for n in ('DRYRUN.json', 'GPU_NEED.json', 'TESTS.json', 'VALIDATION.json', 'PACKAGE.json', 'FIX3_PROBES.json'):
    try: res[n+'_code_sha'] = json.load(open(R3/'out'/n)).get('code_sha256')
    except Exception as e: res[n+'_code_sha'] = repr(e)
live = Path('/scratch/jjyeung/orch_n30/sb_ktfix2')
res['live_kit_differs_from_tar3'] = [k for k in p3 if not (live/k).is_file() or sha(live/k) != p3[k]]
# full-tree diff of code-bearing directories (all files, not only pinned suffixes)
def allfiles(R):
    out = {}
    for d in ('code', 'configs', 'scripts', 'inputs'):
        for p in (R/d).rglob('*'):
            if p.is_file(): out[str(p.relative_to(R))] = sha(p)
    for p in R.glob('*'):
        if p.is_file(): out[p.name] = sha(p)
    return out
a3, a2 = allfiles(R3), allfiles(R2)
res['tree_added'] = sorted(set(a3) - set(a2)); res['tree_removed'] = sorted(set(a2) - set(a3))
res['tree_changed'] = sorted(k for k in set(a2) & set(a3) if a2[k] != a3[k])
res['pinned_added'] = sorted(set(p3) - set(p2)); res['pinned_removed'] = sorted(set(p2) - set(p3))
res['pinned_changed'] = sorted(k for k in set(p2) & set(p3) if p2[k] != p3[k])
w3 = {str(p.relative_to(R3)) for p in (R3/'work').rglob('*') if p.is_file()}; w2 = {str(p.relative_to(R2)) for p in (R2/'work').rglob('*') if p.is_file()}
res['work_added'] = sorted(w3 - w2); res['work_removed'] = sorted(w2 - w3)
res['work_changed'] = sorted(k for k in w2 & w3 if sha(R2/k) != sha(R3/k))
print(json.dumps(res, indent=1)); json.dump(res, open(W/'verify_members.json', 'w'), indent=1)
with open(W/'code_tree.diff', 'w') as f:
    for k in res['tree_changed'] + res['tree_added']:
        try:
            a = (R2/k).read_text().splitlines(keepends=True) if (R2/k).exists() else []
            b = (R3/k).read_text().splitlines(keepends=True)
        except UnicodeDecodeError:
            f.write(f'BINARY {k}\n'); continue
        f.writelines(difflib.unified_diff(a, b, 'ktfix2/'+k, 'ktfix3/'+k, n=2))
