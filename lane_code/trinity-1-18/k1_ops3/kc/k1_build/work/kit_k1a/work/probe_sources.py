import json,gzip,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[2]
for name in ['ground_rows/work/inputs/routing356_scenes.json','dose_pool/out/t1_gt/REGISTRY_H1.json','dose_pool/out/t1_gt/REGISTRY_H2.json','p1c_build/k6/RECEIPT.json']:
 p=R/name;print(name,p.exists())
 if p.exists():
  d=json.loads(p.read_text());print(str(d)[:2000])
p=R/'p1c_build/k6/MAP.jsonl.gz'
with gzip.open(p,'rt') as f:print('MAP',next(f))
p=R/'dose_pool/out/arkit_gt/gt/44358407.npz'
if p.exists():
 with zipfile.ZipFile(p) as z:print('GT ZIP',z.namelist(),p.stat().st_size)
