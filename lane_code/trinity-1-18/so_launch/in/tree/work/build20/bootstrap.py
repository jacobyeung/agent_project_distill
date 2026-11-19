from pathlib import Path
import json, os
L=Path(__file__).resolve().parents[2]; B=L/'work/build20'; T=L/'work/tree_r1'
def size(root):
    return sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())
B.mkdir(exist_ok=True)
(B/'STORAGE_START.json').write_text(json.dumps(dict(workspace=size(L),temporary=size(L/'work/tmp')),indent=2))
for name in ('run.sh','test19.py'):
    s=(L/'work/build19'/name).read_text().replace("B=L/'work/build19'","B=L/'work/build20'").replace('B19_PROOF','B20_PROOF')
    (B/name.replace('19','20')).write_text(s)
for name in ('r1_handover.py','r1_training.py','r1_components.py','r2_contract.py','carrier_c1_run.py'):
    p=B/'base'/name;p.parent.mkdir(exist_ok=True);p.write_bytes((T/'student_pilot'/name).read_bytes())
(B/'STATUS.md').write_text('GO=false. Item 1 is in progress. The host is trinity-1-18; all writes stay inside this workspace.\n')
print((B/'STORAGE_START.json').read_text())
