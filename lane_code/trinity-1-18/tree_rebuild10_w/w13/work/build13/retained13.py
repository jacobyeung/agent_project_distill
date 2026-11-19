"""Replace superseded owned kit copies with digest receipts in place."""
from pathlib import Path
import sys,json
L=Path(__file__).resolve().parents[2];B=L/'work/build13';sys.path.insert(0,str(L/'work/n1fix2'))
from compact_tmp import compact
records=[]
for parent in (B,B/'proofs/final/package/frozen/work/build13'):
    for folder in sorted(parent.glob('retained_kits*')):
        if folder.is_dir():records.extend(compact(folder))
(B/'RETAINED_KIT_RECEIPTS.json').write_text(json.dumps(records,indent=2))
print(json.dumps(dict(files=len(records),original_bytes=sum(v['bytes'] for v in records))))
