"""Run the tree's own closure function (p3_provenance.source_files) on s1_pool.py, as s1_pool.implementation() does."""
import hashlib, importlib.util, json, sys
from pathlib import Path
tree = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2])
spec = importlib.util.spec_from_file_location('p3_provenance_fix20', tree / 'student_pilot' / 'p3_provenance.py')
prov = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prov)
entry = tree / 'student_pilot' / 's1_pool.py'
files = prov.source_files([entry])
impl = {str(p.relative_to(tree)): prov.sha256(p) for p in files}
out.write_text(''.join(f'{v}  {k}\n' for k, v in sorted(impl.items())))
print('closure files', len(impl), 'digest of implementation dict', prov.digest(impl))
for name in sys.argv[3:]:
    print(('IN ' if name in impl else 'OUT'), name, impl.get(name, '')[:12])
tops = {}
for k in impl:
    tops[k.split('/')[0]] = tops.get(k.split('/')[0], 0) + 1
print('by top folder', json.dumps(tops, sort_keys=True))
try:
    sys.path.insert(0, str(tree))
    import student_pilot.s1_pool as pool
    own = pool.implementation()
    print('s1_pool.implementation() ran:', len(own), 'files; equal to the direct call:', own == impl)
except Exception as error:
    print('s1_pool import failed, direct call stands:', type(error).__name__, str(error)[:160])
