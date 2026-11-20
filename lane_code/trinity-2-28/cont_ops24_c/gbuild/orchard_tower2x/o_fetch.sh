#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/ae27b6409c13f
job=$(cat "$P/7.txt"); [[ "$job" =~ ^[0-9]+$ ]]
q=$(squeue -j "$job" -h -o '%i')
test -z "$q"
/usr/bin/python3 -I -s -B - "$P" "$job" <<'PY'
import hashlib,json,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads((p/'5.1.json').read_text());b=(p/'5.json').read_bytes()
if r['job']!=sys.argv[2] or r['sha256']!=hashlib.sha256(b).hexdigest() or r['bytes']!=len(b):raise ValueError('E42')
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as t:
    for n in ('5.json','5.1.json'):t.add(p/n,arcname=n,recursive=False)
PY
