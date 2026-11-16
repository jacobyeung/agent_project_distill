"""Inventory, immutable-base verification and unified diff without Git."""
import difflib
import hashlib
import json
from pathlib import Path
import sys

lane = Path(__file__).resolve().parents[2]
tree, base = lane/'work/tree_r1', lane/'work/base/tree_b01ce449'
sys.path.insert(0, str(tree))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from student_pilot.trace_grammar import RULES, SOURCE_SHA256

original, current = inventory(base), inventory(tree)
expected = 'b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99'
if digest(original) != expected:
    raise ValueError('Read-only base no longer matches the supplied seal')
out = lane/'out'
with (out/'TREE.diff').open('w') as handle:
    for name in sorted(original.keys() | current.keys()):
        if original.get(name) == current.get(name):
            continue
        old = (base/name).read_text().splitlines(keepends=True) if name in original else []
        new = (tree/name).read_text().splitlines(keepends=True) if name in current else []
        handle.writelines(difflib.unified_diff(old, new, fromfile='a/'+name if name in original else '/dev/null', tofile='b/'+name))
(out/'TREE_FILES.sha256').write_text(''.join(f'{value}  {name}\n' for name,value in sorted(current.items())))
seal = dict(schema='build1-source-inventory-v1', tree_sha256=digest(current), files=current,
            base_tree_sha256=digest(original), base_unchanged=True,
            changed_files=[name for name in sorted(current) if original.get(name) != current[name]],
            inventory_function='student_pilot.source_seal.inventory', digest_function='student_pilot.p3_provenance.digest',
            diff_sha256=hashlib.sha256((out/'TREE.diff').read_bytes()).hexdigest())
(out/'TREE_SEAL.json').write_text(json.dumps(seal, indent=2)+'\n')
(out/'GRAMMAR_RULES.json').write_text(json.dumps(dict(SOURCE_SHA256=SOURCE_SHA256, rules=RULES), indent=2)+'\n')
print(json.dumps({key:value for key,value in seal.items() if key != 'files'}, indent=2))
