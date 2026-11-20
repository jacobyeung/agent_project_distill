import hashlib, tarfile, json
from pathlib import Path
L = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24v')
expected = {}
for line in Path('patched.files.sha256').read_text().splitlines():
    h, n = line.split('  ', 1); expected[n] = h
prefixes = ('work/tree_r1c/', 'out/kit_n_go/', 'out/kit_qd/', 'work/build24/kits/', 'out/TREE_', 'out/rcj/')
tree, other, names, total = {}, {}, [], 0
with tarfile.open(L/'out/tree_rebuild_b24m4v_3b4b6cff.tar', 'r:*') as a:
    for m in a:
        total += 1
        n = m.name[2:] if m.name.startswith('./') else m.name
        names.append(n)
        if not m.isfile(): continue
        hit = next((p for p in prefixes if n.startswith(p) or ('/' + p) in ('/' + n)), None)
        if hit is None: continue
        h = hashlib.sha256(a.extractfile(m).read()).hexdigest()
        if 'work/tree_r1c/' in n: tree[n.split('work/tree_r1c/', 1)[1]] = h
        else: other[n] = h
res = dict(members=total, first_names=names[:5], tree_members=len(tree), tree_equals_patched=tree == expected,
           tree_diff=sorted(set(tree.items()) ^ set(expected.items()))[:10])
mism = []
for n, h in other.items():
    rel = n.split('/', 1)[1] if not n.startswith(('out/', 'work/')) else n
    disk = L / rel
    if not disk.is_file(): mism.append((n, 'missing_on_disk')); continue
    if hashlib.sha256(disk.read_bytes()).hexdigest() != h: mism.append((n, 'differs'))
res.update(other_checked=len(other), other_mismatch=mism[:20])
Path('pkg_check.json').write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1)[:3000])
