"""Stage base/new/delta/live_base/live trees from sealed sources; verify zero-fuzz application of donor3 patches.

new   = base 57a1f14d + PATCH_DONOR3
delta = base + PATCH_DONOR2 + PATCH_DONOR3_DELTA
live  = live 189df6ac + PATCH_DONOR3
Also compares new against donor2's patched tree (donor2rev/work/new) file by file.
"""
import hashlib, json, os, shutil, subprocess
from pathlib import Path

W = Path(__file__).resolve().parent
FB = Path('/scratch/jjyeung/orch_n30/fb_pack')
BASE_SRC = FB / 'ro/orch_n30/tree_rebuild10_w/w24/work/tree_r1'
BASE_SEAL = FB / 'ro/orch_n30/tree_rebuild10_w/w24/out/TREE_SEAL.json'
LIVE_ROOT = Path('/scratch/jjyeung/orch_n30/tree_rebuild15_w24l')
LIVE_SEAL = LIVE_ROOT / 'out24j/TREE24J_SEAL.json'
P2 = FB / 'donor2/out/PATCH_DONOR2.patch'
P3 = FB / 'donor3/out/PATCH_DONOR3.patch'
P3D = FB / 'donor3/out/PATCH_DONOR3_DELTA.patch'
D2NEW = FB / 'donor2rev/work/new'
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


diff = lambda a, b: sorted(n for n in set(a) | set(b) if a.get(n) != b.get(n))

seal = json.loads(BASE_SEAL.read_text())
base = inventory(BASE_SRC)
out['base'] = dict(files=len(base), digest=dig(base), seal=seal['tree_sha256'], match_seal=dig(base) == seal['tree_sha256'])
assert out['base']['match_seal'], out['base']
assert seal['tree_sha256'].startswith('57a1f14d'), seal['tree_sha256']
stage(BASE_SRC, base, W / 'base')

stage(BASE_SRC, base, W / 'new')
out['apply_full'] = apply(W / 'new', P3)
new = inventory(W / 'new')
out['new_vs_base'] = diff(base, new)

d2 = inventory(D2NEW)
out['donor2_new_vs_base'] = diff(base, d2)
out['new_vs_donor2_new'] = diff(d2, new)

stage(BASE_SRC, base, W / 'delta')
out['apply_donor2'] = apply(W / 'delta', P2)
out['delta_after_donor2_equals_donor2_new'] = inventory(W / 'delta') == d2
out['apply_delta3'] = apply(W / 'delta', P3D)
out['delta_equals_new'] = inventory(W / 'delta') == new

ls = json.loads(LIVE_SEAL.read_text())
lfiles = ls['files']
assert dig(lfiles) == ls['tree_sha256'] == '189df6ac590caf7622354c3bd1f991e599776494ced635a23f0c93eb1b567710'
out['live'] = dict(files=len(lfiles), seal=ls['tree_sha256'])
src = LIVE_ROOT / 'work/tree_r1_base'
stage(src, lfiles, W / 'live_base')
stage(src, lfiles, W / 'live')
out['live_vs_base'] = diff(base, lfiles)
out['apply_live'] = apply(W / 'live', P3)
live = inventory(W / 'live')
lexp = dict(lfiles); lexp.update({n: new[n] for n in out['new_vs_base']})
out['live_matches_expected'] = live == lexp
out['live_mismatch'] = diff(live, lexp)
out['inputs'] = {str(p): sha(p) for p in (P2, P3, P3D, BASE_SEAL, LIVE_SEAL, Path(__file__))}
ok = (all(out[k]['rc'] == 0 and not out[k]['fuzz'] and not out[k]['offset'] and not out[k]['rej']
          for k in ('apply_full', 'apply_donor2', 'apply_delta3', 'apply_live'))
      and out['new_vs_donor2_new'] == ['tests/test_scale_donor.py'] and out['delta_equals_new']
      and out['live_matches_expected'])
out['status'] = 'PASS' if ok else 'FAIL'
(W / 'SETUP.json').write_text(json.dumps(out, indent=1))
print(json.dumps({k: v for k, v in out.items() if k != 'inputs' and not k.startswith('apply')}, indent=1))
print({k: (v['rc'], v['fuzz'], v['offset'], v['rej']) for k, v in out.items() if k.startswith('apply')})
