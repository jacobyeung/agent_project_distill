#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/c8b836b4ae536
job=$(cat "$P/a/6.txt"); [[ "$job" =~ ^[0-9]+$ ]]
q=$(squeue -j "$job" -h -o '%i' 2>&1 | sed -n '/^[0-9]/p' || true)
test -z "$q"
st=$(TZ=UTC sacct -j "$job" -X -n -P -o State,NodeList,Elapsed | sed -n 1p)
case "${st%%|*}" in COMPLETED|FAILED|TIMEOUT|CANCELLED*|OUT_OF_MEMORY|NODE_FAIL|PREEMPTED|BOOT_FAIL|DEADLINE) ;; *) echo E50 >&2; exit 1;; esac
printf '%s %s\n' "$job" "$st" > "$P/a/11.txt"
/usr/bin/python3 -I -s -B - "$P" <<'PY'
import sys,tarfile
from pathlib import Path
p=Path(sys.argv[1])
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as t:
    for n in ['a/11.txt','a/4.out','a/4.stderr','a/c/0.log','a/c/1.log','a/c/CPU.json','a/c/MEMORY.json','a/c/REHEARSAL.json','2.json']:
        if (p/n).is_file() and (p/n).stat().st_size<=8000000:t.add(p/n,arcname=n,recursive=False)
PY
