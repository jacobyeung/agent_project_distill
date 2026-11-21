#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/adba6b82bdb9d
job=$(cat "$P/6.txt"); [[ "$job" =~ ^[0-9]+$ ]]
q=$(squeue -j "$job" -h -o '%i' 2>&1 | sed -n '/^[0-9]/p' || true)
test -z "$q"
st=$(TZ=UTC sacct -j "$job" -X -n -P -o State,NodeList,Elapsed | sed -n 1p)
case "${st%%|*}" in COMPLETED|FAILED|TIMEOUT|CANCELLED*|OUT_OF_MEMORY|NODE_FAIL|PREEMPTED|BOOT_FAIL|DEADLINE) ;; *) echo E50 >&2; exit 1;; esac
printf '%s %s\n' "$job" "$st" > "$P/11.txt"
/usr/bin/python3 -I -s -B - "$P" <<'PY'
import sys,tarfile
from pathlib import Path
p=Path(sys.argv[1])
with tarfile.open(fileobj=sys.stdout.buffer,mode="w|gz") as t:
    for n in ["11.txt","4.json","4.1.json","4.err","4.out","4.stderr"]:
        if (p/n).is_file() and (p/n).stat().st_size<=2000000:t.add(p/n,arcname=n,recursive=False)
PY
