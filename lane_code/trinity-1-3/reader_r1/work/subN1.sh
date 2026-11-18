# Submit job 1 (tower dev-S1, b9ef552934627; ORCH GO 1720Z + ANSWER 0049Z). Only after local checks: no ORCH HOLD, newest INBOX asks no hold.
set -euo pipefail
export TZ=UTC
P=/project/community/jjyeung/b9ef552934627
cd "$P"
test ! -e a/8.txt || { echo "ALREADY SUBMITTED $(cat a/8.txt)"; exit 3; }
# CPU receipt pass check (package OPERATIONS step 2)
/usr/bin/python3 -I -s -B - "$P" <<'PYCODE'
import hashlib,json,sys,tarfile
from pathlib import Path
p=Path(sys.argv[1]);c=json.loads((p/'a/c/CPU.json').read_text());v=json.loads((p/'0.json').read_text())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert c['passed'] is True and c['bundle_guard_passed'] is True and c['entry_sequence_passed'] is True
assert c['payload']==v['payload_sha256'] and c['plan']==v['plan_sha256']
assert c['operator_sha256']==sha(p/'a/6.py') and c['inputs']==sha(p/'a/1.json')
g=c['bundle_guard']
assert g['passed'] is True and g['path']=='7.py' and g['guard_target']=='6.py' and g['action']=='test'
assert g['operator_sha256']==sha(p/'a/6.py') and g['batch_sha256']==sha(p/'BATCH.sh')
e=c['entry_sequence'];root=Path(c['root'])
assert e['passed'] is True and e['entry_sequence_passed'] is True
assert e['events']==['guard_installed','write_test','operator_dispatch']
assert e['operator_sha256_before']==e['operator_sha256_after']==c['operator_sha256']
assert e['path']=='7.py' and e['guard_target']=='6.py' and e['action']=='test'
assert e['operator_sha256']==c['operator_sha256'] and e['batch_sha256']==sha(p/'BATCH.sh')
assert e['pool']==str(root/'wpool') and e['token']==v['token']
w=e['write_test']
assert type(w['bytes']) is int and w['bytes']==4*1024**2
assert isinstance(w['sha256'],str) and len(w['sha256'])==64 and all(ch in '0123456789abcdef' for ch in w['sha256'])
with tarfile.open(p/'0.tgz') as archive:
    guard_sha=hashlib.sha256(archive.extractfile('orchard_h10/vendor/return_io.py').read()).hexdigest()
assert e['guard_target_sha256']==guard_sha
assert {k:v for k,v in e.items() if k!='entry_sequence_passed'}==g
assert e['requested_argv'][-2:]==[str(root/'a/5.py'),str(root/'a/1.json')]
assert e['dispatched_argv']==e['requested_argv'][:-2]+[str(root/'7.py'),str(root/'a/1.json')]
m=c['memory']
assert m==json.loads((p/'a/c/MEMORY.json').read_text())
assert m['fits'] is True and m['basis']=='fixed_g3t_shapes'
assert m['perception_memo_modules']==['g3t'] and m['sam_measurement_required'] is False
print('All CPU receipt checks passed')
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
JOB_REPLY=$(/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 05:00:00)
JOB=${JOB_REPLY%%;*}
[[ "$JOB" =~ ^[0-9]+$ ]]
printf '%s\n' "$JOB" > a/8.txt
echo "SUBMITTED $JOB $(date -u +%FT%TZ)"
squeue -j "$JOB" -o '%i %j %P %T %M %l %R'
