#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
[[ $(hostname -s) == trinity-1-3 ]] || { echo 'REFUSED: run on trinity-1-3'; exit 3; }
W=/scratch/jjyeung/orch_n30/r1_ops/work/drv
cd "$W"
OUT=$W/sess_26cc98b7.json
[[ ! -e "$OUT" && ! -L "$OUT" && ! -e "$W/mint.started" ]] || { echo 'REFUSED: existing mint attempt; no retry'; exit 3; }
: > "$W/mint.started"
# The H1 helper uses authenticated GCS create-only resumable sessions.
if ! /usr/bin/python3 -I /scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/mint.py "$OUT" 8865619b 26cc98b7 m100 m200 mstop mstopB mstopC > "$W/mint.private.log" 2>&1; then
 echo 'FAILED mint; inspect locally without exposing capabilities; no automatic retry' >&2; exit 4
fi
chmod 600 "$OUT"
/usr/bin/python3 -I - "$OUT" "$W/e.txt" <<'PYCODE'
import json,sys
from pathlib import Path
d=json.loads(Path(sys.argv[1]).read_text());want=set(Path(sys.argv[2]).read_text().split())
assert set(d)==want and len(d)==20 and len(set(d.values()))==20
assert all(v.startswith('https://storage.googleapis.com/upload/') for v in d.values())
print('PASS 20 fresh create-only sessions; mode 0600; URI contents withheld')
PYCODE
