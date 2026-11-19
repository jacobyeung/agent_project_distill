"""Build base+A, base+A+CAMFORM2, base+A2, base+A2+CAMFORM2_ON_A2 and compare to FILES_TOUCHED.json."""
from pathlib import Path
import hashlib, json, subprocess, shutil, sys
W = Path(__file__).resolve().parent
FB = W.parents[1]
RO = FB/'ro/orch_n30'
TREE = RO/'tree_rebuild10_w/w24/work/tree_r1'
MAN = RO/'tree_rebuild10_w/w24/out/TREE_FILES.sha256'
SEAL = RO/'tree_rebuild10_w/w24/out/TREE_SEAL.json'
PA = FB/'patchA/out/PATCH_A.patch'
PA2 = FB/'patchA2/out/PATCH_A2.patch'
PC = FB/'camform2/out/PATCH_CAMFORM2.patch'
PC2 = FB/'camform2/out/PATCH_CAMFORM2_ON_A2.patch'
FT = json.loads((FB/'camform2/out/FILES_TOUCHED.json').read_text())
sha = lambda b: hashlib.sha256(b).hexdigest()
out = {}
files = {}
for line in MAN.read_text().splitlines():
    h, rel = line.split('  ', 1); assert sha((TREE/rel).read_bytes()) == h, rel; files[rel] = h
seal = sha(json.dumps(files, sort_keys=True, separators=(',', ':')).encode())
out['base_files'] = len(files); out['seal'] = seal; out['seal_ok'] = seal == json.loads(SEAL.read_text())['tree_sha256']
out['sha'] = {p.name: sha(p.read_bytes()) for p in (PA, PA2, PC, PC2)}
def build(name, patches):
    t = W/('tree_'+name)
    if t.exists(): sys.exit('exists '+str(t))
    for rel in files:
        p = t/rel; p.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(TREE/rel, p)
    logs = []
    for pp in patches:
        r = subprocess.run(['patch', '--batch', '--fuzz=0', '--no-backup-if-mismatch', '-p1', '-i', str(pp)], cwd=t, capture_output=True, text=True)
        logs.append((pp.name, r.returncode, r.stdout + r.stderr))
    return logs
for name, patches in (('A', [PA]), ('C', [PA, PC]), ('A2', [PA2]), ('C2', [PA2, PC2])):
    out['apply_'+name] = build(name, patches)
def tree(t): return {str(p.relative_to(t)): sha(p.read_bytes()) for p in sorted(t.rglob('*')) if p.is_file()}
T = {n: tree(W/('tree_'+n)) for n in ('A', 'C', 'A2', 'C2')}
out['file_counts'] = {n: len(v) for n, v in T.items()}
def check(a, c, ft):
    diff = {k: (T[a].get(k), T[c].get(k)) for k in set(T[a]) | set(T[c]) if T[a].get(k) != T[c].get(k)}
    res = {}
    for f in ft:
        got = diff.pop(f['path'], None); res[f['path']] = got == (f['base_sha256'], f['new_sha256'])
    return res, diff
out['A_vs_C'], out['A_vs_C_extra'] = check('A', 'C', FT['files'])
out['A2_vs_C2'], out['A2_vs_C2_extra'] = check('A2', 'C2', FT['A2']['files'])
for mine, theirs in (('C', 'new'), ('C2', 'newA2'), ('A', 'base'), ('A2', 'baseA2')):
    N = {k: v for k, v in tree(FB/'camform2/work'/theirs).items() if '__pycache__' not in k}
    out['mine_%s_vs_their_%s' % (mine, theirs)] = sorted(k for k in set(N) | set(T[mine]) if N.get(k) != T[mine].get(k))
# the delivered patch's new files and touched-file set
out['A_vs_A2_differs'] = sorted(k for k in set(T['A']) | set(T['A2']) if T['A'].get(k) != T['A2'].get(k))
(W/'R1_APPLY.json').write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))
