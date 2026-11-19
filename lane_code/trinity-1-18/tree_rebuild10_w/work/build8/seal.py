"""Refresh the source inventory, textual diff and seal without Git."""
import difflib
import hashlib
import json
from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2]
tree=L/'work/tree_r1';base=L/'work/base/tree_b01ce449'
sys.path.insert(0,str(tree))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
files=inventory(tree);prior=inventory(base)
(L/'out/TREE_FILES.sha256').write_text(''.join(h+'  '+name+'\n' for name,h in sorted(files.items())))
parts=[]
for name in sorted(set(files)|set(prior)):
    a=base/name;b=tree/name
    try:
        old=a.read_text().splitlines(keepends=True) if a.exists() else []
        new=b.read_text().splitlines(keepends=True) if b.exists() else []
    except UnicodeDecodeError:
        if not a.exists() or not b.exists() or a.read_bytes()!=b.read_bytes():
            parts.append('Binary files a/'+name+' and b/'+name+' differ\n')
        continue
    if old!=new:parts.extend(difflib.unified_diff(old,new,fromfile='a/'+name,tofile='b/'+name))
(L/'out/TREE.diff').write_text(''.join(parts))
seal=dict(schema='build8-tree-seal-v1',tree_sha256=digest(files),files=files,
    inventory_sha256=hashlib.sha256((L/'out/TREE_FILES.sha256').read_bytes()).hexdigest(),
    diff_sha256=hashlib.sha256((L/'out/TREE.diff').read_bytes()).hexdigest(),
    base=str(base.relative_to(L)),status='NOT READY FOR PRODUCTION',production_authorized=False)
(L/'out/TREE_SEAL.json').write_text(json.dumps(seal,indent=2)+'\n')
print(json.dumps({k:v for k,v in seal.items() if k!='files'}))
