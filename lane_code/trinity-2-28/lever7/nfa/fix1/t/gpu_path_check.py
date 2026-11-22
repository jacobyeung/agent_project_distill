"""Show that fix 1 leaves the GPU job's executed code unchanged: the BATCH bundle differs only in 7.py,
and 7.py differs from the placed operator only inside rehearsal() plus the constant only rehearsal() reads."""
import ast, hashlib, io, json, re, sys, tarfile
from pathlib import Path
NFA = Path('/scratch/jjyeung/orch_n30/lever7/nfa')
old_pkg, new_pkg = NFA/'fix1/pre/pkg', NFA/'fix1/pkg_new'
sha = lambda b: hashlib.sha256(b).hexdigest()
def bundle(p):
    t = (p/'BATCH.sh').read_text(); m = re.search(r"bytes\.fromhex\('([0-9a-f]+)'\)", t)
    with tarfile.open(fileobj=io.BytesIO(bytes.fromhex(m.group(1)))) as a:
        return t[:m.start(1)] + t[m.end(1):], {e.name: a.extractfile(e).read() for e in a}
ot, ob = bundle(old_pkg); nt, nb = bundle(new_pkg)
assert ot == nt, 'BATCH.sh text outside the bundle differs'
assert ob['0.py'] == nb['0.py'] and ob['0.json'] == nb['0.json'], 'bootstrap or descriptor differs'
assert ob['7.py'] == (old_pkg/'a/6.py').read_bytes() and nb['7.py'] == (new_pkg/'a/6.py').read_bytes()
print('BATCH.sh: outside the hex bundle identical; bundle 0.py, 0.json identical; 7.py == a/6.py in each package')
o, n = ast.parse(ob['7.py']), ast.parse(nb['7.py'])
def top(tree):
    out = {}
    for node in tree.body:
        key = node.name if hasattr(node, 'name') else (node.targets[0].id if isinstance(node, ast.Assign) else ast.dump(node)[:60])
        out[key] = ast.dump(node)
    return out
O, N = top(o), top(n)
changed = sorted(k for k in set(O) | set(N) if O.get(k) != N.get(k))
print('top-level names changed:', changed)
assert changed == ['CPU_SKIPPED', 'rehearsal'], changed
users = sorted({f.name for f in n.body if isinstance(f, ast.FunctionDef)
                for x in ast.walk(f) if isinstance(x, ast.Name) and x.id == 'CPU_SKIPPED'})
assert users == ['rehearsal'], users
callers = sorted({f.name for f in n.body if isinstance(f, ast.FunctionDef)
                  for x in ast.walk(f) if isinstance(x, ast.Call) and getattr(x.func, 'id', None) == 'rehearsal'})
assert callers == ['main'], callers
print('CPU_SKIPPED read only by rehearsal(); rehearsal() called only from main() under cfg.get("rehearsal")')
job = (NFA/'ref/payload/orchard_h10/job.py').read_text()
line = [l for l in job.splitlines() if "write(dispatch/'1.json'" in l]
assert len(line) == 1 and 'rehearsal' not in line[0], line
print('GPU job.py writes its 1.json without a rehearsal key:', line[0].strip())
for f in ('0.json', '0.tgz', '3.py', 'CONFIG.json', 'INPUTS.example.json', 'SUBMIT.cmd', 'a/1.json', 'a/5.py', 'a/export.json'):
    assert (NFA/'kit/pkg'/f).read_bytes() == (new_pkg/f).read_bytes(), f
print('byte-identical to the placed package: 0.json 0.tgz 3.py CONFIG.json INPUTS.example.json SUBMIT.cmd a/1.json a/5.py a/export.json')
print('old 7.py', sha(ob['7.py']), 'new 7.py', sha(nb['7.py']))
print('PASS')
