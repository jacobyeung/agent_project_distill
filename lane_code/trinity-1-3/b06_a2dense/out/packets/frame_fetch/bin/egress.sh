#!/bin/bash
# One ranged GET (64 KiB) of the first ARKit capture's lowres_wide.zip from a compute node, with the k6 venv.
F=$(cd "$(dirname "$0")/.." && pwd); mkdir -p $F/logs
/project/community/jjyeung/cp4tk_fr/venv/bin/python -I - "$F" > $F/logs/egress.${SLURM_JOB_ID:-x}.json 2>&1 <<'PY'
import json, sys, time, socket, urllib.request
F = sys.argv[1]
t = json.load(open(F + '/plan/tasks_a.json')); u = t[sorted(t)[0]]['u']
r = dict(host=socket.gethostname(), t=time.time())
try:
    q = urllib.request.Request(u, headers={'Range': 'bytes=0-65535'})
    with urllib.request.urlopen(q, timeout=60) as h:
        b = h.read(); r.update(status=h.status, bytes=len(b), zip_magic=b[:4] == b'PK\x03\x04')
except Exception as ex:
    r.update(error=repr(ex)[:300])
print(json.dumps(r))
PY
{ df -h /tmp /dev/shm /scratch /local 2>/dev/null; lsblk -d -o NAME,SIZE,TYPE 2>/dev/null; free -g | head -2; } > $F/logs/disk.${SLURM_JOB_ID:-x}.txt 2>&1
