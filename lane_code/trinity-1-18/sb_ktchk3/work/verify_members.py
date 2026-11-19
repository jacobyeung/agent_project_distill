"""Checks 1-2 for sb_ktfix4: members, code hash, and the full source diff against sb_ktfix3.tar and the sb_ktchk2 trial."""
import json, hashlib, tarfile, difflib
from pathlib import Path
W = Path(__file__).resolve().parent
R4, R3 = W/'ex4', W/'ex3'
TRY = Path('/scratch/jjyeung/orch_n30/sb_ktchk2/work/fixtry')
TAR4 = '/scratch/jjyeung/orch_n30/sb_ktfix2/out/sb_ktfix4.tar'
CLAIM = '076c5d87ab581e9b49332f9deaea20991cee2b8d989cd2287d1a6160e2b93e9c'
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
def allfiles(R, dirs=('code', 'configs', 'scripts', 'inputs', 'work', 'out')):
    out = {}
    for d in dirs:
        for p in (R/d).rglob('*'):
            if p.is_file() or p.is_symlink(): out[str(p.relative_to(R))] = 'LINK' if p.is_symlink() else sha(p)
    for p in R.glob('*'):
        if p.is_file(): out[p.name] = sha(p)
    return out
t = tarfile.open(TAR4); mem = t.getmembers()
names = [m.name for m in mem if m.isfile()]
m = json.load(open(R4/'out/FIX4_MEMBERS.json')); mf = m['files'] if 'files' in m else m
p4, p3 = pins(R4), pins(R3)
c = json.load(open(R4/'out/CODE_SHA256.json'))
res = dict(tar_members=len(mem), non_file=[x.name for x in mem if not x.isfile()], bad_paths=[n for n in names if n.startswith('/') or '..' in n.split('/')],
           manifest_files=len(mf), hash_mismatch=[k for k, v in mf.items() if sha(R4/k) != v],
           in_tar_not_manifest=sorted(set(names) - set(mf)), in_manifest_not_tar=sorted(set(mf) - set(names)),
           code_files=len(p4), code_sha256=dg(p4), matches_claim=dg(p4) == CLAIM, fix3_code_sha256=dg(p3),
           code_json=c.get('code_sha256'), pin_diffs_vs_CODE_SHA256_json=sorted(k for k in set(p4) | set(c['files']) if p4.get(k) != c['files'].get(k)))
for n in ('DRYRUN.json', 'GPU_NEED.json', 'TESTS.json', 'VALIDATION.json', 'PACKAGE.json', 'FIX3_PROBES.json', 'FIX4_DIFF.json', 'FIX4_DELIVERY_CHECK.json'):
    try: res[n+'_code_sha'] = json.load(open(R4/'out'/n)).get('code_sha256')
    except Exception as e: res[n+'_code_sha'] = repr(e)
live = Path('/scratch/jjyeung/orch_n30/sb_ktfix2')
res['live_kit_differs_from_tar4'] = [k for k in p4 if not (live/k).is_file() or sha(live/k) != p4[k]]
res['live_code_sha256'] = dg(pins(live))
a4, a3 = allfiles(R4), allfiles(R3)
res['pinned_added'] = sorted(set(p4) - set(p3)); res['pinned_removed'] = sorted(set(p3) - set(p4))
res['pinned_changed'] = sorted(k for k in set(p3) & set(p4) if p3[k] != p4[k])
src = lambda k: k.split('/')[0] in ('code', 'configs', 'scripts', 'inputs') or '/' not in k
res['source_added'] = sorted(k for k in set(a4) - set(a3) if src(k)); res['source_removed'] = sorted(k for k in set(a3) - set(a4) if src(k))
res['source_changed'] = sorted(k for k in set(a3) & set(a4) if src(k) and a3[k] != a4[k])
res['work_added'] = sorted(k for k in set(a4) - set(a3) if k.startswith('work/')); res['work_removed'] = sorted(k for k in set(a3) - set(a4) if k.startswith('work/'))
res['work_changed'] = sorted(k for k in set(a3) & set(a4) if k.startswith('work/') and a3[k] != a4[k])
res['out_changed_or_added'] = sorted(k for k in a4 if k.startswith('out/') and a3.get(k) != a4[k])
# The four edited non-test files must equal the sb_ktchk2 trial byte for byte; test_fix3.py is the only new content.
res['equal_to_trial'] = {k: sha(R4/k) == sha(TRY/k) for k in ('code/evaluate_v2.py', 'code/process_guard.py', 'scripts/gpu_environment.sh', 'code/test_kit.py', 'code/test_fix3.py')}
mine = []
for k in res['source_changed'] + res['source_added']:
    a = (R3/k).read_text().splitlines(keepends=True) if (R3/k).exists() else []
    b = (R4/k).read_text().splitlines(keepends=True)
    mine += list(difflib.unified_diff(a, b, 'sb_ktfix3/'+k, 'sb_ktfix4/'+k))
(W/'source_tree.diff').write_text(''.join(mine))
def hunks(text): return [l for l in text.splitlines() if l[:1] in '+-' and not l.startswith(('+++', '---'))]
res['builder_diff_equals_mine'] = hunks(''.join(mine)) == hunks((R4/'out/FIX4_SOURCE.diff').read_text())
tri = (W.parent.parent/'sb_ktchk2/work/fixtry.patch').read_text()
res['trial_patch_lines_in_builder_diff'] = all(l in hunks(''.join(mine)) for l in hunks(tri))
test3 = [l for l in hunks(''.join(mine)) if l not in hunks(tri)]
res['non_trial_changed_lines'] = len(test3)
res['non_trial_lines_outside_test_fix3'] = [l for l in test3 if l not in hunks(''.join(difflib.unified_diff((R3/'code/test_fix3.py').read_text().splitlines(keepends=True), (R4/'code/test_fix3.py').read_text().splitlines(keepends=True))))]
print(json.dumps(res, indent=1)); json.dump(res, open(W/'verify_members.json', 'w'), indent=1)
