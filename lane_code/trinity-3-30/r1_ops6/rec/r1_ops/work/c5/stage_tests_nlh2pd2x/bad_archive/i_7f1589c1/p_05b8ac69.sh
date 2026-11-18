#!/bin/bash
set -euo pipefail
[[ "$2" == --rehearsal && "$SLURM_JOB_ID" == 173001 ]]
[[ -f "$3/aws/u/ap/69d2930d/d.db" && -f "$3/c7d31ddd/venvs/rwtrain_torch211_cu129/bin/python" ]]
"/scratch/jjyeung/envs/p1cpu/bin/python" -I -B - "$3" "$KH" <<'P'
import json,sys
from pathlib import Path
root=Path(sys.argv[1]);k=Path(sys.argv[2])
assert list(root.glob('epochs/*/entry.py'))
assert list(root.glob('c7d31ddd/_jobs/*/site_alias.r172467/retained.txt'))
assert not (root/'k').exists()
with (k/'o/173001.rehearsal.json').open('x') as f:json.dump(dict(status='REHEARSAL_OK',rc=0,job='173001',rehearsal=True),f)
P
exit 0
