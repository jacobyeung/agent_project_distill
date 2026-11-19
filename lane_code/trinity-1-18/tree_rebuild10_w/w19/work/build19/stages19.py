from pathlib import Path
import json,sqlite3
L=Path(__file__).resolve().parents[2];O=L/'work/build19/proofs/native'
for step in (400,600):
    p=O/str(step)/'q/RESULT.json'
    if p.exists():print(step,json.loads(p.read_text()).get('refusal'))
    for p in (O/str(step)/'q/p').glob('attempt_*/prepare/*/receipt.json'):
        v=json.loads(p.read_text());print(str(p.relative_to(O)),{k:v.get(k) for k in ('count','refused','types','per_type')})
    for p in (O/str(step)/'q/p').rglob('composed/receipt.json'):
        v=json.loads(p.read_text());print(str(p.relative_to(O)),{k:v.get(k) for k in ('count','refused','per_source')})
    for p in (O/str(step)/'q/p').rglob('routing/materialization.json'):
        v=json.loads(p.read_text());print({k:x for k,x in v.items() if k not in ('inputs','legacy','base_model','division','source_scene_exclusions','frame_audit','frames')})
