from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build20';K=B/'kits/q'
if not (B/'RESTAGED.json').exists():
    size=sum(p.stat().st_size for p in K.rglob('*') if p.is_file())
    K.rename(B/'retained_q')
    (B/'KIT_Q_INITIAL.json').rename(B/'KIT_Q_INITIAL_RETAINED.json')
    (B/'RESTAGED.json').write_text(json.dumps(dict(from_empty=True,retained_bytes=size,GO=False)))
