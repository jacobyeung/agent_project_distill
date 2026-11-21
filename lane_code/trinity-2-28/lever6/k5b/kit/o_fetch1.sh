#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/adba6b82bdb9d
job=$(cat "$P/71.txt"); [[ "$job" =~ ^[0-9]+$ ]]
q=$(squeue -j "$job" -h -o '%i' 2>&1 | sed -n '/^[0-9]/p' || true)
test -z "$q"
st=$(TZ=UTC sacct -j "$job" -X -n -P -o State,NodeList,Elapsed | sed -n 1p)
case "${st%%|*}" in COMPLETED|FAILED|TIMEOUT|CANCELLED*|OUT_OF_MEMORY|NODE_FAIL|PREEMPTED|BOOT_FAIL|DEADLINE) ;; *) echo E50 >&2; exit 1;; esac
printf '%s %s\n' "$job" "$st" > "$P/121.txt"
/usr/bin/python3 -I -s -B - "$P" "$job" 1 <<'PY'
import hashlib,json,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);g=sys.argv[3]
try:
    r=json.loads((p/("5"+g+".1.json")).read_text());b=(p/("5"+g+".json")).read_bytes()
    ok=r["job"]==sys.argv[2] and r["sha256"]==hashlib.sha256(b).hexdigest() and r["bytes"]==len(b)
except Exception:
    ok=False
print("ok" if ok else "E42",file=sys.stderr)
with tarfile.open(fileobj=sys.stdout.buffer,mode="w|gz") as t:
    for n in ["51.json", "51.1.json", "51.err", "51.out", "51.stderr", "61.err", "121.txt"]:
        if (p/n).is_file() and (p/n).stat().st_size<=8000000:t.add(p/n,arcname=n,recursive=False)
PY
