"""Stage base/new/delta/live trees from the sealed sources and verify zero-fuzz patch application."""
import hashlib, json, os, shutil, subprocess, sys
from pathlib import Path

W = Path(__file__).resolve().parent
FB = Path('/scratch/jjyeung/orch_n30/fb_pack')
BASE_SRC = FB / 'ro/orch_n30/tree_rebuild10_w/w24/work/tree_r1'
BASE_SEAL = FB / 'ro/orch_n30/tree_rebuild10_w/w24/out/TREE_SEAL.json'
LIVE_ROOT = Path('/scratch/jjyeung/orch_n30/tree_rebuild15_w24l')
LIVE_SEAL = LIVE_ROOT / 'out24j/TREE24J_SEAL.json'
P2 = FB / 'donor2/out/PATCH_DONOR2.patch'
P1 = FB / 'donor/out/PATCH_DONOR.patch'
PD = FB / 'donor2/out/PATCH_DONOR2_DELTA.patch'
FT = json.loads((FB / 'donor2/out/FILES_TOUCHED.json').read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
dig = lambda d: hashlib.sha256(json.dumps(d, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
out = {}


def inventory(root):
    files = {}
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in ('__pycache__', '.git')]
        for f in fn:
            if f.endswith('.pyc'):
                continue
            p = Path(dp) / f
            files[str(p.relative_to(root))] = sha(p)
    return files


def stage(src, files, dest):
    if dest.exists():
        shutil.rmtree(dest)
    for n, h in files.items():
        b = (src / n).read_bytes(); assert hashlib.sha256(b).hexdigest() == h, n
        q = dest / n; q.parent.mkdir(parents=True, exist_ok=True); q.write_bytes(b)


def apply(tree, patch):
    r = subprocess.run(['patch', '--fuzz=0', '--batch', '-p1', '-d', str(tree), '-i', str(patch)], text=True, capture_output=True)
    return dict(patch=str(patch), patch_sha256=sha(patch), rc=r.returncode, stdout=r.stdout, stderr=r.stderr,
                fuzz='fuzz' in r.stdout.lower(), offset='offset' in r.stdout.lower(), rej=any(tree.rglob('*.rej')),
                orig=any(tree.rglob('*.orig')))


# Base
seal = json.loads(BASE_SEAL.read_text())
base = inventory(BASE_SRC)
listed = {l.split('  ', 1)[1]: l.split('  ', 1)[0] for l in (FB / 'donor2/out/TREE_FILES.sha256').read_text().splitlines()}
out['base'] = dict(files=len(base), digest=dig(base), seal=seal['tree_sha256'], match_seal=dig(base) == seal['tree_sha256'],
                   equals_donor2_listing=base == listed)
assert out['base']['match_seal'], out['base']
stage(BASE_SRC, base, W / 'base')

# New = base + PATCH_DONOR2
stage(BASE_SRC, base, W / 'new')
out['apply_full'] = apply(W / 'new', P2)
new = inventory(W / 'new')
exp = dict(base); exp.update({e['path']: e['new_sha256'] for e in FT['files']})
out['new_matches_files_touched'] = new == exp
out['new_changed'] = sorted(n for n in new if base.get(n) != new[n])

# Delta = base + PATCH_DONOR + DELTA
stage(BASE_SRC, base, W / 'delta')
out['apply_donor1'] = apply(W / 'delta', P1)
d1 = inventory(W / 'delta')
out['donor1_matches'] = all(d1.get(e['path']) == e['donor_sha256'] for e in FT['files'])
out['apply_delta'] = apply(W / 'delta', PD)
out['delta_equals_new'] = inventory(W / 'delta') == new

# Live 189df6ac
ls = json.loads(LIVE_SEAL.read_text())
lfiles = ls['files']
out['live'] = dict(files=len(lfiles), digest=dig(lfiles), seal=ls['tree_sha256'], base_tree=ls['base_tree_sha256'])
assert dig(lfiles) == ls['tree_sha256'] == '189df6ac590caf7622354c3bd1f991e599776494ced635a23f0c93eb1b567710'
src = LIVE_ROOT / 'work/tree_r1_base'
stage(src, lfiles, W / 'live_base')
stage(src, lfiles, W / 'live')
d2live = inventory(FB / 'donor2/work/live_base')
out['donor2_live_base_equals_seal'] = d2live == lfiles
out['live_vs_base_diff'] = sorted(set(n for n in set(lfiles) | set(base) if lfiles.get(n) != base.get(n)))
out['apply_live'] = apply(W / 'live', P2)
live = inventory(W / 'live')
lexp = dict(lfiles); lexp.update({e['path']: e['new_sha256'] for e in FT['files']})
out['live_matches_expected'] = live == lexp
out['live_mismatch'] = sorted(n for n in set(live) | set(lexp) if live.get(n) != lexp.get(n))
out['inputs'] = {str(p): sha(p) for p in (P1, P2, PD, BASE_SEAL, LIVE_SEAL, Path(__file__))}
(W / 'SETUP.json').write_text(json.dumps(out, indent=1))
print(json.dumps({k: v for k, v in out.items() if k not in ('inputs',)}, indent=1)[:6000])
