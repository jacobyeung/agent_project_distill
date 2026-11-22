"""T1's first-pass repeat bound in rotation and translation (camera differences only, no score)."""
import sys, json
from pathlib import Path
import numpy as np
sys.path.insert(0, '/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild')
sys.path.insert(0, '/scratch/jjyeung/orch_n30/lever6/k5b/kit')
from gpkg.capture_io import Records
import score_k5 as sk
CAP = Path('/scratch/jjyeung/orch_n30/cont_ops24_c/cap')
by = {}
for row in Records(CAP/'t1.gz', CAP/'t1ret/CAPTURE.json'):
    g = row.get('geometry')
    if not g: continue
    by.setdefault(row['capture'], []).append((row['pass_index'], g['camera_to_world_metric']))
out = {}
for cap, rows in by.items():
    if len(rows) < 2: continue
    p0 = [c for p, c in rows if p == 0]
    if not p0: continue
    base = p0[0]
    reps = [c for p, c in rows[1:]] if len(p0) == 1 else [c for p, c in rows if p != 0] + p0[1:]
    reps = [c for c in [c for _, c in rows][1:]]
    out[cap] = dict(n=len(rows), pass_indices=sorted(set(p for p, _ in rows)),
                    rot_deg=[sk.rot_deg(base, c) for c in reps], trans_m=[sk.trans_m(base, c) for c in reps])
print(json.dumps(out, indent=1))
