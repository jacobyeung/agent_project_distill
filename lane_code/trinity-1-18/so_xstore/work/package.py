"""Create a pinned additive patch without Git or changes to the input tree."""
from pathlib import Path
import difflib
import hashlib
import json
import os

L = Path(__file__).resolve().parent.parent
base_info = json.loads((L / 'work/BASE.json').read_text())
base, changed = Path(base_info['root']), L / 'work/tree'
files = [
    'student_pilot/preparation_cpu.py',
    'student_pilot/preparation_reads.py',
    'student_pilot/preparation_store.py',
    'scripts/preparation_cpu.py',
    'scripts/compare_preparation_stores.py',
    'tests/test_preparation_native_boundary.py',
    'tests/test_preparation_store.py',
]
inventory = {}
for root, dirs, names in os.walk(base):
    dirs[:] = sorted(d for d in dirs if d not in ('.git', '__pycache__', 'artifacts'))
    for name in sorted(names):
        p = Path(root) / name
        assert not p.is_symlink()
        relative = str(p.relative_to(base))
        raw = p.read_bytes()
        inventory[relative] = hashlib.sha256(raw).hexdigest()
        assert (changed / relative).read_bytes() == raw, 'Existing source changed: ' + relative
base_digest = hashlib.sha256(json.dumps(inventory, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
assert base_digest == base_info['source_seal'], (base_digest, base_info)
parts = []
for name in files:
    assert not (base / name).exists()
    parts.extend(difflib.unified_diff([], (changed / name).read_text().splitlines(True),
                                    fromfile='/dev/null', tofile='b/' + name))
patch_dir = L / 'out/patches'
patch_dir.mkdir(exist_ok=True)
patch_name = '01_native_cpu_and_store_groundwork.diff'
raw = ''.join(parts).encode()
(patch_dir / patch_name).write_bytes(raw)
pin = dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), base=base_info,
           base_tree_sha256=base_digest, base_file_count=len(inventory),
           base_sha256={name: None for name in files},
           files={name:hashlib.sha256((changed / name).read_bytes()).hexdigest() for name in files},
           apply_method='patch --batch --fuzz=0 -p1',
           switches={'TK_NATIVE_CPU_PREPARE': 'OFF', 'TK_XSTORE_EXPERIMENT': 'OFF'},
           status='PARTIAL: no native planner, native portable producer, or GPU adopter',
           default_path='All existing source files byte-identical; no existing importer or wrapper changed.')
(patch_dir / 'manifest.json').write_text(json.dumps({patch_name: pin}, indent=2, sort_keys=True) + '\n')
(L / 'out/evidence/base_inventory.json').write_text(json.dumps(inventory, indent=2, sort_keys=True) + '\n')
print(json.dumps({patch_name:pin}, indent=2))
