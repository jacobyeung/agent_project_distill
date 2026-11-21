#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/ac105d39edf1d
job=$(cat "$P/6.txt"); [[ "$job" =~ ^[0-9]+$ ]]
st=$(TZ=UTC sacct -j "$job" -X -n -P -o State | head -1 | cut -d' ' -f1)
case "$st" in COMPLETED|FAILED|TIMEOUT|CANCELLED|OUT_OF_MEMORY|NODE_FAIL|PREEMPTED|BOOT_FAIL|DEADLINE) ;; *) echo E50 >&2; exit 1;; esac
printf '%s %s\n' "$job" "$st" > "$P/11.txt"
/usr/bin/python3 -I -s -B - "$P" "$job" <<'PY'
import hashlib,json,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1])
with tarfile.open(fileobj=sys.stdout.buffer,mode="w|gz") as t:
    for n in ["11.txt", "4.json", "4.1.json", "4.err", "4.out", "4.stderr"]:
        if (p/n).is_file():t.add(p/n,arcname=n,recursive=False)
PY
