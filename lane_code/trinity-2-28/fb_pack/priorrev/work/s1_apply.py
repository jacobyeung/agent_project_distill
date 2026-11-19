"""Check 1: copy the sealed base, apply PATCH_PRIOR with fuzz 0, and compare hashes."""
import hashlib, json, shutil, subprocess, sys
from pathlib import Path

W = Path(__file__).resolve().parent
R = Path('/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/tree_rebuild10_w/w24')
SRC = R/'work/tree_r1'
P2 = Path('/scratch/jjyeung/orch_n30/fb_pack/prior2/out')
P2B = Path('/scratch/jjyeung/orch_n30/fb_pack/prior2b/out')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def tree_digest(inv):
    return hashlib.sha256(json.dumps(inv, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


manifest = {n: h for h, n in (l.split('  ', 1) for l in (R/'out/TREE_FILES.sha256').read_text().splitlines())}
out = {'manifest_tree_sha256': tree_digest(manifest), 'manifest_files': len(manifest)}
actual = sorted(str(p.relative_to(SRC)) for p in SRC.rglob('*') if p.is_file())
out['actual_files'] = len(actual)
out['extra_files_in_src'] = sorted(set(actual) - set(manifest))[:50]
bad = [n for n, h in manifest.items() if sha(SRC/n) != h]
out['seal_mismatch'] = bad
for name in ('base', 'new'):
    d = W/name
    if d.exists():
        sys.exit(f'{d} exists; use fresh dir')
    for n in manifest:
        (d/n).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SRC/n, d/n)
patch = P2/'PATCH_PRIOR.patch'
out['patch_sha256'] = sha(patch)
out['patch2b_sha256'] = sha(P2B/'PATCH_PRIOR.patch')
r = subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-d', str(W/'new'), '-i', str(patch)],
                   capture_output=True, text=True)
out['patch_rc'] = r.returncode
out['patch_stdout'] = r.stdout
out['patch_stderr'] = r.stderr
new_inv = {str(p.relative_to(W/'new')): sha(p) for p in (W/'new').rglob('*') if p.is_file()}
out['new_files'] = len(new_inv)
out['new_tree_sha256'] = tree_digest(new_inv)
ft = json.loads((P2/'FILES_TOUCHED.json').read_text())
out['ft_base'] = ft['base_tree_sha256'] == out['manifest_tree_sha256']
out['ft_new'] = ft['new_tree_sha256'] == out['new_tree_sha256']
out['ft_patch'] = ft['patch']['sha256'] == out['patch_sha256']
changed = sorted(n for n in new_inv if manifest.get(n) != new_inv[n])
out['changed'] = changed
out['removed'] = sorted(set(manifest) - set(new_inv))
per = []
for f in ft['files']:
    per.append(dict(path=f['path'], before_ok=manifest.get(f['path']) == f['before_sha256'],
                    after_ok=new_inv.get(f['path']) == f['after_sha256'],
                    bytes_ok=(W/'new'/f['path']).stat().st_size == f['bytes']))
out['per_file'] = per
out['ft_paths_equal_changed'] = sorted(f['path'] for f in ft['files']) == changed
(W/'S1_APPLY.json').write_text(json.dumps(out, indent=1) + '\n')
print(json.dumps({k: v for k, v in out.items() if k not in ('per_file',)}, indent=1))
print(per)
