"""Retain completed proof evidence before activating neutral slot codes."""
from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];D=L/'work/build22';O=D/'proofs/capacity';A=L/'attic'
def read(p):return json.loads(p.read_text())
result=read(O/'RESULT.json');verified=read(O/'VERIFIED.json')
assert result['complete_native_fixture'] and set(verified)=={'400','600'}
saved=dict(tree=read(L/'out/TREE_SEAL.json'),result=result,verified=verified,
    forwards={s:read(O/s/'q/f.json') for s in verified},
    scope='Completed CPU fixture before the neutral slot-code change; final-tree verification is recorded separately.')
(D/'NAMED_CAPACITY.json').write_text(json.dumps(saved,indent=2)+'\n')
for source,target in ((O/'400',A/'build22_named_capacity_400'),
                      (D/'capacity.log',A/'build22_named_capacity.log'),
                      (D/'kits/q',A/'build22_named_kit'),
                      (D/'KIT_Q_INITIAL.json',A/'build22_named_kit_initial.json')):
 assert source.exists() and not target.exists();source.rename(target)
print('Retained completed named-slot proof and kit; final source can now change')
