#!/bin/bash
#SBATCH -p advanced
#SBATCH --job-name=a15_cot_apb2edfac4
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:4
#SBATCH --cpus-per-task=48
#SBATCH --mem=800G
#SBATCH --time=24:00:00
#SBATCH --no-requeue
#SBATCH --signal=B:TERM@600
#SBATCH --output=/tmp/q_22c714e1_%j.log
#SBATCH --error=/tmp/q_22c714e1_%j.err
set -euo pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1
X='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z7/work/build24m4z7/wrapper_signals_a/after_USR1/x'
ROOT="$X/n"
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
mkdir -p "$N"
exec >>"$N/j2.log" 2>>"$N/j2.err"
cat > "$N/j2.py" <<'PYJ2'
import os,sys,time
from pathlib import Path
kit,node,target,job,parent=sys.argv[1:6]
node=Path(node);target=Path(target)/'o'/job
sys.path.insert(0,str(Path(kit)/'b'))
from z import load,screen
words=load(Path(kit)/'k/g.json');hashes=load(Path(kit)/'b/wh.json')
interval=float(sys.argv[6]) if len(sys.argv)>6 else 600
# This process owns no training pipe; failed publication cannot close one.
def publish():
    try:
        target.mkdir(parents=True,exist_ok=True,mode=0o700)
        for name in ('j2.log','j2.err'):
            with (node/name).open('rb') as f:
                f.seek(max(0,os.fstat(f.fileno()).st_size-300000))
                raw=screen(f.read().decode('utf-8','replace'),words,hashes).encode()[-300000:]
            temp=target/(name+'.part')
            with temp.open('wb') as f:f.write(raw)
            os.replace(temp,target/name)
    except Exception as e:
        with (node/'j2.retry.log').open('a') as f:
            f.write(str(int(time.time()))+' '+type(e).__name__+' '+__import__('re').sub(r'https?://[^\s]+','[URL]',str(e))+'\n')
if len(sys.argv)>7 and sys.argv[7]=='once':publish();raise SystemExit(0)
while True:
    publish()
    try:os.kill(int(parent),0)
    except ProcessLookupError:break
    time.sleep(interval)
PYJ2
setsid python3 -B -I -s "$N/j2.py" "$ROOT" "$N" "$X" "$SLURM_JOB_ID" "$$" >>"$N/j2.retry.log" 2>&1 &
printf "%s" "$!" > "$SLURM_TMPDIR/helper_pid"
J2_PID=$!
printf '%s SLURM_TMPDIR=%s free_bytes=' "$(date -u +%FT%TZ)" "${SLURM_TMPDIR:-/tmp}"
python3 -B -I -s -c 'import shutil,sys;print(shutil.disk_usage(sys.argv[1]).free)' "${SLURM_TMPDIR:-/tmp}"
child=''
forward() { if [[ -n "$child" ]]; then kill -"$1" "$child" 2>/dev/null || true; fi; }
trap 'forward TERM' TERM
trap 'forward USR1' USR1
g=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2>&1 | head -4 || true); echo "$(date -u +%FT%TZ) gpus: $g" | tr '\n' ';'; echo
[ "$(nvidia-smi -L 2>/dev/null | grep -c H100)" -ge 4 ] || { echo "$(date -u +%FT%TZ) fewer than 4 H100; stop before staging"; exit 3; }
echo "$(date -u +%FT%TZ) resolve start"
python3 -B -I -s "$ROOT/b/v.py" "$ROOT"
OMP_NUM_THREADS=8 python3 -B -I -s "$ROOT/b/resolve.py" --pool "/project/community/jjyeung/okh7" --output "$N/r0.json" 2>&1 | python3 -B -I -s "$ROOT/b/l.py" "$ROOT"
echo "$(date -u +%FT%TZ) resolve done; start job.sh"
bash "$ROOT/job.sh" "$N/r0.json" &
child=$!
set +e
while true; do
    wait "$child"
    status=$?
    kill -0 "$child" 2>/dev/null || break
done
trap '' TERM USR1
python3 -B -I -s "$N/j2.py" "$ROOT" "$N" "$X" "$SLURM_JOB_ID" "$$" 600 once || true
kill -TERM "$J2_PID" 2>/dev/null || true
wait "$J2_PID" 2>/dev/null || true
exit "$status"
