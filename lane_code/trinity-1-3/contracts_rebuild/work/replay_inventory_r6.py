from pathlib import Path
from collections import Counter
import json
L=Path(__file__).resolve().parents[1];R=L/'work/real/x_geo'
paths=sorted(R.glob('*/*/*.npz'));js=sorted(R.rglob('*.json'))
captures=[p for p in js if '__' in p.stem]
result=dict(gravity_source='G3T tower gravity, not student-head gravity',source=str(R),
 archive_source=str(L/'work/real/geometry_8c58df1547371bdb.tar'),npz_count=len(paths),capture_json_count=len(captures),
 npz_by_dataset=dict(Counter(p.stem.split('__')[0] for p in paths)),json_by_dataset=dict(Counter(p.stem.split('__')[0] for p in captures)),
 missing_npz=[str(p) for p in captures if not p.with_suffix('.npz').exists()],missing_json=[str(p) for p in paths if not p.with_suffix('.json').exists()],
 noncapture_json=[str(p) for p in js if p not in captures],paths=list(map(str,paths)))
with (L/'out/real_replay_r6/CAPTURE_INVENTORY.json').open('x') as f:json.dump(result,f,indent=2)
