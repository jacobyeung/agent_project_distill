#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
[[ $(hostname -s) == trinity-1-3 ]] || { echo 'REFUSED: run on trinity-1-3'; exit 3; }
W=/scratch/jjyeung/orch_n30/r1_ops/work/drv_p5
cd "$W"
/scratch/jjyeung/envs/p1cpu/bin/python -B -c 'import packet_config; print("PASS frozen packet "+packet_config.PINS["archive"])'
OUT=$W/sess_673bc60f.json
[[ ! -e "$W/mint_673bc60f.private.log" && ! -L "$W/mint_673bc60f.private.log" && ! -e "$OUT" && ! -L "$OUT" && ! -e "$W/mint_673bc60f.started" && ! -L "$W/mint_673bc60f.started" ]] || { echo 'REFUSED: existing mint attempt; no retry'; exit 3; }
(set -o noclobber; : > "$W/mint_673bc60f.started")
# The H1 helper uses authenticated GCS create-only resumable sessions.
if ! /scratch/jjyeung/envs/p1cpu/bin/python -I "$W/mint_fresh.py" "$OUT" 8865619b 673bc60f m100 m200 mstop mstopB mstopC > "$W/mint_673bc60f.private.log" 2>&1; then
 echo 'FAILED mint; inspect locally without exposing capabilities; no automatic retry' >&2; exit 4
fi
chmod 600 "$OUT"
/scratch/jjyeung/envs/p1cpu/bin/python -I - "$OUT" "$W/e.txt" <<'PYCODE'
import json,sys
from pathlib import Path
d=json.loads(Path(sys.argv[1]).read_text());want=set(Path(sys.argv[2]).read_text().split())
assert set(d)==want and len(d)==20 and len(set(d.values()))==20
assert all(v.startswith('https://storage.googleapis.com/upload/') for v in d.values())
print('PASS 20 fresh create-only sessions; mode 0600; URI contents withheld')
PYCODE
