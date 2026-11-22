#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/c8b836b4ae536
job=$(cat "$P/a/70.txt"); [[ "$job" =~ ^[0-9]+$ ]]
q=$(squeue -j "$job" -h -o '%i' 2>&1 | sed -n '/^[0-9]/p' || true)
test -z "$q"
st=$(TZ=UTC sacct -j "$job" -X -n -P -o State,NodeList,Elapsed | sed -n 1p)
case "${st%%|*}" in COMPLETED|FAILED|TIMEOUT|CANCELLED*|OUT_OF_MEMORY|NODE_FAIL|PREEMPTED|BOOT_FAIL|DEADLINE) ;; *) echo E50 >&2; exit 1;; esac
printf '%s %s\n' "$job" "$st" > "$P/a/120.txt"
/usr/bin/python3 -I -s -B - "$P" "$job" <<'PY'
import hashlib,json,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);job=int(sys.argv[2])
z=json.loads((p/'0.json').read_text())
src=Path('/project/community/jjyeung/okh7/ae71c903')/(z['token']+format(job,'08x'))
ok='E44'
try:
    e=json.loads((src/'EXIT.json').read_text())
    ok='ok' if hashlib.sha256((src/'result.tar.gz').read_bytes()).hexdigest()==e['archive_sha256'] else 'E43'
except Exception:
    pass
print(ok,file=sys.stderr)
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as t:
    t.add(p/'a/120.txt',arcname='120.txt',recursive=False)
    for n in ['EXIT.json','RETURN_RECEIPT.json','result.tar.gz']:
        if (src/n).is_file() and (src/n).stat().st_size<=19000000:t.add(src/n,arcname=n,recursive=False)
PY
