# Submit job 2: room-only tower read c3cc59fb4aae0 (ORCH ANSWER 2156Z). Only after job 1 has left general, review_rr2room GO, CPU check passed.
set -euo pipefail
export TZ=UTC
P=/project/community/jjyeung/c3cc59fb4aae0
cd "$P"
test ! -e a/8.txt || { echo "ALREADY SUBMITTED $(cat a/8.txt)"; exit 3; }
/usr/bin/python3 -I -s -B - "$P" <<'PYCODE'
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]);c=json.loads((p/'a/c/CPU.json').read_text());v=json.loads((p/'0.json').read_text())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert c['passed'] is True and c['full_reader_passed'] is True
assert c['full_reader']['passed'] is True and c['full_reader']['device']=='cpu'
assert c['payload']==v['payload_sha256'] and c['plan']==v['plan_sha256']
assert c['operator_sha256']==sha(p/'a/6.py') and c['inputs']==sha(p/'a/1.json')
rows=c['full_reader']['records']
assert [(r['set'],r['item']) for r in rows]==[('dev-S1','room_scene0155_00'),('R0-dev','r0_015bd4aaf6870d79bade')]
assert all(r['passed'] is True and r['record']['complete'] is True and r['record']['output']['finish']=='eos' for r in rows)
print('full_reader_passed=true')
PYCODE
G=$(squeue -u "$USER" -p general -h -o '%j %T')
if [ -n "$G" ]; then echo "GENERAL BUSY: $G"; exit 9; fi
if squeue -u "$USER" -h -o '%j %P %T' | grep -E '^jjy_[^ ]* general' ; then echo "MAIN JOB ON GENERAL"; exit 9; fi
# Return pool okh7/ae71c903 (return_io.py cap 100 MB; write test 4.2 MB at start, archive est 5 MB, worst 15 MB at publish; GCS is the second channel)
POOL_MB=$(/usr/bin/python3 -I -s -B -c "from pathlib import Path;print(round(sum(p.stat().st_size for p in Path('/project/community/jjyeung/okh7/ae71c903').rglob('*') if p.is_file())/1e6,1))")
echo "POOL_MB $POOL_MB"
/usr/bin/python3 -I -s -B -c "import sys;sys.exit(0 if float('$POOL_MB')<=75 else 1)" || { echo "POOL TOO FULL: $POOL_MB MB > 75"; exit 8; }
sinfo -N -h -p general -o '%G' > a/7.txt
/usr/bin/python3 -I -s -B - a/7.txt <<'PYCODE'
import re,sys
from pathlib import Path
rows=[s.strip() for s in Path(sys.argv[1]).read_text().splitlines() if s.strip()]
gpu=[g for row in rows for g in row.split(',') if g.startswith('gpu:')]
assert rows and gpu
assert all(re.fullmatch(r'gpu:(?:[^:]*[Hh]100[^:]*:)?[0-9]+(?:\([^)]*\))?',g) for g in gpu), gpu
PYCODE
squeue -u "$USER" -h -o '%j %P %T' > a/9.txt  # record; main's jjy_* jobs pend on advanced by design, the general check above is the ORCH rule
JOB_REPLY=$(/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 02:30:00)
JOB=${JOB_REPLY%%;*}
[[ "$JOB" =~ ^[0-9]+$ ]]
printf '%s\n' "$JOB" > a/8.txt
echo "SUBMITTED $JOB $(date -u +%FT%TZ)"
squeue -j "$JOB" -o '%i %j %P %T %M %l %R'
