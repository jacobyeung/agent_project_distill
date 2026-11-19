import json, sys
from pathlib import Path
J = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(J/'work/tree_r1'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
before = inventory(J/'work/tree_r1')
base = inventory(J/'work/tree_r1_base')
assert before == base
assert len(before) == 940
assert digest(before) == '189df6ac590caf7622354c3bd1f991e599776494ced635a23f0c93eb1b567710'
(J/'out/BEFORE24L.json').write_text(json.dumps(before, indent=2)+'\n')
print(json.dumps(dict(seal=digest(before), count=len(before), bytes=sum((J/'work/tree_r1'/p).stat().st_size for p in before))))
