#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/ac105d39edf1d
job=$(cat "$P/7.txt"); [[ "$job" =~ ^[0-9]+$ ]]
st=$(TZ=UTC sacct -j "$job" -X -n -P -o State | head -1 | cut -d' ' -f1)
case "$st" in COMPLETED|FAILED|TIMEOUT|CANCELLED|OUT_OF_MEMORY|NODE_FAIL|PREEMPTED|BOOT_FAIL|DEADLINE) ;; *) echo E50 >&2; exit 1;; esac
printf '%s %s\n' "$job" "$st" > "$P/12.txt"
/usr/bin/python3 -I -s -B - "$P" "$job" <<'PY'
import hashlib,json,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1])
r=json.loads((p/"5.1.json").read_text());b=(p/"5.json").read_bytes()
if r["job"]!=sys.argv[2] or r["sha256"]!=hashlib.sha256(b).hexdigest() or r["bytes"]!=len(b):raise ValueError("E42")
with tarfile.open(fileobj=sys.stdout.buffer,mode="w|gz") as t:
    for n in ["12.txt", "5.json", "5.1.json", "4.json", "4.err", "4.out", "4.stderr", "5.err", "5.out", "5.stderr", "6.err"]:
        if (p/n).is_file():t.add(p/n,arcname=n,recursive=False)
PY
