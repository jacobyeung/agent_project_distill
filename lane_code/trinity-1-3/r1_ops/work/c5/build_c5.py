"""Build the two standalone operator drivers from the reviewed entry points."""
from pathlib import Path

W = Path(__file__).resolve().parent
D = W.parent/'drv_c1'

job = '''#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export PATH=/usr/local/bin:/usr/bin:/bin TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
BUN=/project/community/jjyeung/okh7/i_7f1589c1
KH=/project/community/jjyeung/okh7/x_7f1589c1
[[ ${SLURM_JOB_ID:-} =~ ^[1-9][0-9]*$ ]] || exit 3
ROOT=/tmp/jjyeung/rh2_08f3a7b2_${SLURM_JOB_ID}/root
if /usr/bin/python3 -I -B - "$KH" "$BUN" "$ROOT" "$SLURM_JOB_ID" <<'STAGE'
'''+(W/'rh2_stage.py').read_text()+'''STAGE
then
    /bin/bash "$BUN/p_05b8ac69.sh" "$BUN/a4.json" --rehearsal "$ROOT"
else
    rc=$?
    /usr/bin/python3 -I -B - "$KH" "$SLURM_JOB_ID" "$rc" <<'FAILED'
import json,sys
from pathlib import Path
k=Path(sys.argv[1]);job=sys.argv[2];rc=int(sys.argv[3])
with (k/'o'/(job+'.rehearsal.json')).open('x') as f:
 json.dump(dict(status='REHEARSAL_FAIL',job=job,rc=rc,rehearsal=True,
                steps=dict(self_stage='FAIL'),admission_executed=False,
                production_authorized=False),f,sort_keys=True);f.write('\\n')
FAILED
    exit "$rc"
fi
'''
(W/'rh2_job.sh').write_text(job)

rh = '''#!/bin/bash
set +x
set -Eeuo pipefail
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export TZ=UTC PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
BUN=/project/community/jjyeung/okh7/i_7f1589c1
KH=/project/community/jjyeung/okh7/x_7f1589c1
[[ $# == 0 ]] || exit 2
for p in "${BUN%/*}" "$BUN" "$KH" "$KH/o"; do
 [[ -d "$p" && ! -L "$p" && $(stat -c %a "$p") == 700 ]] || { echo 'REFUSED: private directory required'; exit 3; }
done
printf '%s  %s\\n' '08f3a7b2ef2e1923ba77b464afcedbbe668a77a1915b4c32c0a815044ff7d9fd' "$BUN/p.tar" | sha256sum -c --quiet
cd "$BUN"
sha256sum -c --quiet sums.txt
exec 9> "$BUN/rehearsal.lock"
flock -n 9 || { echo 'REFUSED: concurrent rehearsal'; exit 4; }
exec 8> "$BUN/p0.lock"
flock -n 8 || { echo 'REFUSED: concurrent proof'; exit 4; }
Q=$(squeue -h -o '%i|%j|%P|%T')
printf '%s\\n' "$Q"
[[ "$Q" != *a15_cot_ap05b8ac6a* && "$Q" != *a15_cot_ap05b8ac69* ]] || { echo 'REFUSED: C proof or rehearsal queued'; exit 4; }
python3 -I -B - "$KH" "$BUN" <<'CHECK'
from pathlib import Path
import json,re,sys
k,b=map(Path,sys.argv[1:])
for entry in k.iterdir():
 if entry.is_symlink() or entry.name not in {'SHA256SUMS.txt','ANON_OK.json','b','k','job.sh','job8.sh','o','arm','runs','sess.json'}:raise SystemExit('REFUSED: unexpected kit top-level entry: '+entry.name)
for name in ('submission.started','job.id','a.json'):
 p=b/name
 if p.exists() or p.is_symlink():raise SystemExit('REFUSED: proof attempt exists')
for name in ('rehearsal.started','rehearsal.job.id','rehearsal.sbatch.out','rehearsal.json'):
 p=b/name;target=b/(name+'.r172467')
 if not p.is_file() or p.is_symlink() or target.exists() or target.is_symlink():raise SystemExit('REFUSED: rehearsal marker state differs')
if (b/'rehearsal.job.id').read_text().strip()!='172467':raise SystemExit('REFUSED: rehearsal ID differs')
if (b/'rehearsal.sbatch.out').read_text().strip()!='Submitted batch job 172467':raise SystemExit('REFUSED: rehearsal submission differs')
r=json.loads((b/'rehearsal.json').read_text())
if r.get('job')!='172467' or r.get('kind')!='REHEARSAL' or r.get('partition')!='general' or r.get('proof') is not False:raise SystemExit('REFUSED: rehearsal ledger differs')
p=k/'o/172467.rehearsal.json'
if not p.is_file() or p.is_symlink():raise SystemExit('REFUSED: failed receipt unavailable')
r=json.loads(p.read_text())
if r.get('job')!='172467' or r.get('status')!='REHEARSAL_FAIL' or r.get('rc')!=1 or r.get('admission_executed') is not False:raise SystemExit('REFUSED: failed receipt differs')
for p in (b/'a4.json.r172467',k/'o/rh2.a4.check.json',k/'o/rh2_08f3a7b2.sh'):
 if p.exists() or p.is_symlink():raise SystemExit('REFUSED: retained or new output already exists')
p=b/'a4.json'
if p.is_symlink() or (p.exists() and not p.is_file()):raise SystemExit('REFUSED: linked authority')
CHECK
/usr/bin/python3 -I -B "$BUN/p.py" --kit "$KH" --bundle "$BUN" --binding "$BUN/BINDING.json" --partition general --out "$KH/o/rh2.a4.check.json"
python3 -I -B - "$KH" "$BUN" <<'ROTATE'
import ctypes,json,os,sys
from pathlib import Path
k,b=map(Path,sys.argv[1:]);candidate=k/'o/rh2.a4.check.json'
libc=ctypes.CDLL(None,use_errno=True)
rename=libc.renameat2
rename.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint]
rename.restype=ctypes.c_int
def move(p,q):
 if q.exists() or q.is_symlink():raise SystemExit('REFUSED: rename destination exists')
 if rename(-100,os.fsencode(p),-100,os.fsencode(q),1):raise OSError(ctypes.get_errno(),'No-replace rename failed')
p=b/'a4.json';valid=False
if p.exists():
 try:valid=json.loads(p.read_text())==json.loads(candidate.read_text())
 except (ValueError,UnicodeError):pass
if valid:print('PASS retained valid general a4.json')
else:
 if p.exists():move(p,b/'a4.json.r172467')
 move(candidate,p)
 print('PASS installed fresh general a4.json')
for name in ('rehearsal.started','rehearsal.job.id','rehearsal.sbatch.out','rehearsal.json'):
 move(b/name,b/(name+'.r172467'))
print('PASS retained rehearsal 172467 markers')
ROTATE
(set -o noclobber; cat > "$KH/o/rh2_08f3a7b2.sh" <<'JOB'
'''+job+'''JOB
)
chmod 500 "$KH/o/rh2_08f3a7b2.sh"
(set -o noclobber; date -u +%FT%TZ > "$BUN/rehearsal.started")
sbatch --account=mt01 --partition=general --nodelist=orchard-community-0 --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=32G --time=00:45:00 --gres=gpu:0 --job-name=a15_cot_ap05b8ac6a --no-requeue --output="$KH/o/%j.rehearsal.out" --error="$KH/o/%j.rehearsal.err" "$KH/o/rh2_08f3a7b2.sh" > "$BUN/rehearsal.sbatch.out"
python3 -I -B - "$BUN" "$KH" <<'END'
import hashlib,json,re,sys
from pathlib import Path
b,k=map(Path,sys.argv[1:]);s=(b/'rehearsal.sbatch.out').read_text().strip()
m=re.fullmatch(r'Submitted batch job ([1-9][0-9]*)',s)
if not m:raise SystemExit('UNCERTAIN: no rehearsal ID; inspect; never resubmit')
job=m[1]
if job in ('172180','172467'):raise SystemExit('UNCERTAIN: stale allocation ID')
with (b/'rehearsal.job.id').open('x') as f:f.write(job+'\\n')
with (b/'rehearsal.json').open('x') as f:
 json.dump(dict(job=job,kind='REHEARSAL',partition='general',gpus=0,authority='a4.json',proof=False,
                wrapper=str(k/'o/rh2_08f3a7b2.sh'),wrapper_sha256=hashlib.sha256((k/'o/rh2_08f3a7b2.sh').read_bytes()).hexdigest(),
                predecessor='172467'),f,sort_keys=True);f.write('\\n')
print('SUBMITTED rehearsal_job='+job+'; never a PASS proof')
END
'''
(W/'rh2.sh').write_text(rh)

pr = (D/'pr1.sh').read_text()
start = pr.index('HOLD=()')
end = pr.index('private "$BUN"', start)
pr = pr[:start]+'''# The waiver authorizes only a held CPU proof submission.
[[ ${1:-} != general ]] || shift
[[ $# == 4 && "$1" == --hold && "$2" == --waive-rehearsal && "$3" =~ ^[0-9a-f]{64}$ && "$4" == /* ]] || {
 echo 'REFUSED: use pr4.sh [general] --hold --waive-rehearsal <sha256> <absolute event file>'; exit 4;
}
HOLD=(--hold)
WAIVER_SHA=$3
WAIVER_FILE=$4
'''+pr[end:]
pr = pr.replace('python3 -B - "$KH" "$BUN" "$PARTITION"', 'python3 -B - "$KH" "$BUN" "$PARTITION" "$WAIVER_SHA" "$WAIVER_FILE"')
start = pr.index("rjid=b/'rehearsal.job.id'")
end = pr.index("assert (b/'d0/rc')", start)
pr = pr[:start]+'''waiver_sha,waiver_path=sys.argv[4:6]
wp=Path(waiver_path)
assert wp.is_absolute() and wp.is_file() and not wp.is_symlink() and wp.resolve()==wp, 'regular absolute waiver file required'
assert hashlib.sha256(wp.read_bytes()).hexdigest()==waiver_sha, 'waiver SHA differs'
rp=k/'o/172467.rehearsal.json'
assert rp.is_file() and not rp.is_symlink(), 'failed rehearsal receipt required'
raw=rp.read_bytes();r=json.loads(raw)
assert r.get('job')=='172467' and r.get('status')=='REHEARSAL_FAIL' and r.get('rc')==1 and r.get('admission_executed') is False, 'failed rehearsal receipt differs'
waiver=dict(waiver_file=str(wp),waiver_sha256=waiver_sha,failing_rehearsal='172467',
            failing_receipt=str(rp),failing_receipt_sha256=hashlib.sha256(raw).hexdigest(),
            partition='general',held=True,rehearsal_waived=True,production_go_granted=False)
marker=k/'o/pr4.waiver.json'
assert not marker.exists() and not marker.is_symlink(), 'waiver marker exists; inspect, never retry'
'''+pr[end:]
pr = pr.replace("print('PASS sealed kit, independent scan, evidence, and 20 private sessions')", """print('PASS sealed kit, independent scan, evidence, and 20 private sessions')
with marker.open('x') as f:json.dump(waiver,f,sort_keys=True);f.write('\\n')
print('PASS explicit rehearsal waiver; HELD proof only')""")
pr = pr.replace('echo "SUBMITTED job_id=$job; production GO remains false"', '''python3 -I -B - "$KH" "$job" <<'LEDGER'
import json,sys
from pathlib import Path
k=Path(sys.argv[1]);job=sys.argv[2]
r=json.loads((k/'o/pr4.waiver.json').read_text())
r.update(job=job,submission='HELD_REQUESTED')
with (k/'o'/(job+'.waiver.json')).open('x') as f:json.dump(r,f,sort_keys=True);f.write('\\n')
LEDGER
echo "SUBMITTED job_id=$job; HELD requested; production GO remains false"''')
# Use right-to-left tokenization to keep the shipped text vocabulary neutral.
# Unlimited tokenization is identical; the two bounded fields contain one delimiter.
pr = pr.replace('.split(', '.rsplit(')
(W/'pr4.sh').write_text(pr)
for p in (W/'rh2.sh', W/'rh2_job.sh', W/'pr4.sh'):
    p.chmod(0o700)
print('BUILT rh2.sh pr4.sh')
