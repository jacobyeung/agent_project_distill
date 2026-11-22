#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/c8b836b4ae536
test ! -e "$P/a/70.txt"
/usr/bin/python3 -I -s -B - "$P" <<'PY'
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]);h=lambda n:hashlib.sha256((p/n).read_bytes()).hexdigest()
c=json.loads((p/'a/c/CPU.json').read_text());z=json.loads((p/'0.json').read_text());k=json.loads((p/'2.json').read_text())
ok=(c.get('passed') is True and c.get('entry_sequence_passed') is True and c.get('bundle_guard_passed') is True
    and c.get('cpu_reads_passed') is True and c['operator_sha256']==h('a/6.py') and c['payload']==z['payload_sha256']
    and c['plan']==z['plan_sha256'] and c['inputs']==h('a/1.json') and k.get('passed') is True
    and k.get('gpus')==1 and k.get('time')=='02:30:00' and k.get('plan')==z['plan_sha256'])
if not ok:raise SystemExit('E52')
PY
q=$(squeue -u jjyeung -p general -h)
test -z "$q"
pool=$(du -sm /project/community/jjyeung/okh7/ae71c903 | cut -f1)
test "$pool" -le 75
cd "$P"
out=$(A_N=1 A_T=02:30:00 bash SUBMIT.cmd)
job=$(printf '%s\n' "$out" | sed -n 1p); job=${job%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
(set -C; printf '%s\n' "$job" > "$P/a/70.txt")
printf '%s %s\n' "$job" "$pool"
