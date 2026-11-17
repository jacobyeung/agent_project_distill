import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9'
p=B/'proofs/recovery/recovery_rows/RESULT.json';v=json.loads(p.read_text())
with (B/'DECISIONS.md').open('a') as f:
    f.write('\n- Real published slices overlap sealed scene exclusions. Options: bypass exclusions to force the requested admission totals, or preserve exclusions and distinguish text-gate counts from full intake. Default: preserve all exclusions. Full-intake all-row acceptance remains blocked by BOUND_SLICE_SEALED_SCENE_EXCLUSIONS. The metadata proof supplies explicit pose/depth fixture bindings; it does not establish production head ownership.\n')
with (B/'STATUS.md').open('a') as f:
    f.write('\nItem 1: status scope repaired. Native admission and reader checks completed; full intake retains sealed scene exclusions. Evidence: `work/build9/proofs/recovery/recovery_rows/RESULT.json`.\n')
print(json.dumps({k:v['counts'] for k,v in v['families'].items()}))
