"""Seal the final tree and compare it to the supplied immutable base without Git."""
import difflib
import hashlib
import json
from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';B=L/'work/base/tree_b01ce449';O=L/'out'
sys.path.insert(0,str(T))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from student_pilot import trace_grammar as grammar, r2_grammar as wrapper
original,current=inventory(B),inventory(T)
assert digest(original)=='b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99'
with (O/'TREE.diff').open('w') as handle:
    for name in sorted(original.keys()|current.keys()):
        if original.get(name)==current.get(name):continue
        old=(B/name).read_text().splitlines(keepends=True) if name in original else []
        new=(T/name).read_text().splitlines(keepends=True) if name in current else []
        handle.writelines(difflib.unified_diff(old,new,fromfile='a/'+name if name in original else '/dev/null',tofile='b/'+name))
(O/'TREE_FILES.sha256').write_text(''.join(f'{value}  {name}\n' for name,value in sorted(current.items())))
seal=dict(schema='build2-source-inventory-v1',tree_sha256=digest(current),files=current,
          base_tree_sha256=digest(original),base_unchanged=True,
          changed_files=[n for n in sorted(current) if original.get(n)!=current[n]],
          diff_sha256=hashlib.sha256((O/'TREE.diff').read_bytes()).hexdigest())
(O/'TREE_SEAL.json').write_text(json.dumps(seal,indent=2)+'\n')
(O/'GRAMMAR_RULES.json').write_text(json.dumps(dict(shared_sha256=wrapper.SHARED_SHA256,
      rules=grammar.RULES,wrapper_sha256=hashlib.sha256(Path(wrapper.__file__).read_bytes()).hexdigest()),indent=2)+'\n')
print(seal['tree_sha256'])
