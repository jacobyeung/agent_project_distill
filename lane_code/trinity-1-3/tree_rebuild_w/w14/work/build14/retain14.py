"""Retain digests for completed early CPU tensor fixtures; keep final proofs intact."""
from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build14';sys.path.insert(0,str(L/'work/n1fix2'))
from compact_tmp import compact
records=[]
for name in ('tests','focused'):
    root=B/'proofs'/name
    files={str(p):p.stat().st_size for p in root.rglob('*') if p.is_file()
           and p.suffix in ('.pt','.safetensors','.bin') and p.stat().st_size>512}
    records.extend(compact(root,files=files))
(B/'RETAINED_CPU_PRODUCTS.json').write_text(json.dumps(dict(records=records,
    scope='Completed early CPU tensor fixtures only. Final focused proofs, native databases, source, receipts and test observations remain intact.'),indent=2))
print(json.dumps({'files':len(records),'original_bytes':sum(r['bytes'] for r in records)}))
