import base64
import hashlib
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
def load(path):
    x=json.loads(path.read_text())
    if x.get('encoding')=='base64-json':x=json.loads(base64.b64decode(x['payload']))
    return x
seal=load(L/'out/TREE_SEAL.json')
result=[]
for arm in ('a0','a2'):
    root=L/'work/build4/kits'/arm
    actual=load(root/'k/7.json')['files']
    changed=[k for k in set(actual)|set(seal['files']) if actual.get(k)!=seal['files'].get(k)]
    result.append(dict(arm=arm,tree_matches=not changed,different_files=changed))
print(json.dumps(result))
(L/'work/build4/FINAL_IDENTITY.json').write_text(json.dumps(result,indent=2)+'\n')
