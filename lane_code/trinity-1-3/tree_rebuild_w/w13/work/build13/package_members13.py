from pathlib import Path
import json,tarfile
L=Path(__file__).resolve().parents[2];B=L/'work/build13'
old=set(json.loads((B/'proofs/final/package/frozen/package_members.json').read_text()))
with tarfile.open(L/json.loads((B/'DELIVERY.json').read_text())['path']) as f:new={m.name for m in f.getmembers() if m.isfile()}
missing=sorted(old-new)
(B/'PACKAGE_MEMBER_REVIEW.json').write_text(json.dumps(missing,indent=2))
print(json.dumps(missing))
