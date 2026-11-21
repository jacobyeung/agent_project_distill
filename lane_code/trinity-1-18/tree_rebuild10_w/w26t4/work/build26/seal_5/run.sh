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
X="/scratch/jjyeung/orch_n30/tree_rebuild10_w/w26t4/work/build26/x/s"
ROOT="$X/n"
# One final attempt: 120 s, then at most 15 s for fixed-text fallback.
# KILL deadlines also cover children that inherit ignored TERM/USR1.
finish() {
    local status=$1 left=${2:-0} right=${3:-0} message
    trap - EXIT
    trap '' TERM USR1
    set +e
    # Stop the separate periodic session on every exit; never wait on its IO.
    if [[ -n ${J2_PID:-} ]]; then kill -KILL -- "-$J2_PID" 2>/dev/null || true; fi
    if timeout --signal=KILL 120s python3 -B -I -s "${N:-}/j2.py" "$ROOT" "${N:-}" "$X" "${SLURM_JOB_ID:-0}" "$$" 600 once; then
        :
    else
        # Never copy raw logs here. Only these fixed labels and shell statuses
        # may reach X without the kit's screen(), including setup failures.
        case ${step:-setup} in
            node) message='node directory failed' ;;
            log) message='j2.log redirect failed' ;;
            publisher) message='j2.py creation failed' ;;
            gpu) message='fewer than 4 H100; stop before staging' ;;
            seal) message='v.py refusal' ;;
            resolve)
                if [[ $right != 0 ]]; then message='l.py refusal'
                elif [[ $left != 0 ]]; then message='resolve.py refusal'
                else message='resolve.py/l.py refusal'; fi ;;
            child) message='job.sh exit' ;;
            *) message='wrapper setup failed' ;;
        esac
        timeout --signal=KILL 15s bash -c '
            umask 077
            mkdir -p -- "$1/o/$2" &&
            printf "%s; status=%s\n" "$3" "$4" >> "$1/o/$2/j2.fallback.log"
        ' bash "$X" "${SLURM_JOB_ID:-0}" "$message" "$status" || true
    fi
    exit "$status"
}
trap 'finish "$?" "${PIPESTATUS[@]}"' EXIT
umask 077
export PYTHONDONTWRITEBYTECODE=1
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
step=node
mkdir -p "$N"
step=log
exec >>"$N/j2.log" 2>>"$N/j2.err"
step=publisher
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
        return True
    except Exception as e:
        with (node/'j2.retry.log').open('a') as f:
            f.write(str(int(time.time()))+' '+type(e).__name__+' '+__import__('re').sub(r'https?://[^\s]+','[URL]',str(e))+'\n')
        return False
if len(sys.argv)>7 and sys.argv[7]=='once':raise SystemExit(0 if publish() else 1)
while True:
    publish()
    try:os.kill(int(parent),0)
    except ProcessLookupError:break
    time.sleep(interval)
PYJ2
setsid python3 -B -I -s "$N/j2.py" "$ROOT" "$N" "$X" "$SLURM_JOB_ID" "$$" >>"$N/j2.retry.log" 2>&1 &
J2_PID=$!
step=setup
printf '%s SLURM_TMPDIR=%s free_bytes=' "$(date -u +%FT%TZ)" "${SLURM_TMPDIR:-/tmp}"
python3 -B -I -s -c 'import shutil,sys;print(shutil.disk_usage(sys.argv[1]).free)' "${SLURM_TMPDIR:-/tmp}"
child=''
forward() { if [[ -n "$child" ]]; then kill -"$1" "$child" 2>/dev/null || true; fi; }
trap 'forward TERM' TERM
trap 'forward USR1' USR1
step=gpu
g=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2>&1 | head -4 || true); echo "$(date -u +%FT%TZ) gpus: $g" | tr '\n' ';'; echo
[ "$(nvidia-smi -L 2>/dev/null | grep -c H100)" -ge 4 ] || { echo "$(date -u +%FT%TZ) fewer than 4 H100; stop before staging"; exit 3; }
echo "$(date -u +%FT%TZ) resolve start"
step=seal
python3 -B -I -s "$ROOT/b/v.py" "$ROOT"
step=resolve
OMP_NUM_THREADS=8 python3 -B -I -s "$ROOT/b/resolve.py" --pool "/scratch/jjyeung/orch_n30/tree_rebuild10_w/w26t4/work/build26/pool" --output "$N/r0.json" 2>&1 | python3 -B -I -s "$ROOT/b/l.py" "$ROOT"
echo "$(date -u +%FT%TZ) resolve done; start job.sh"
step=child
bash "$ROOT/job.sh" "$N/r0.json" &
child=$!
set +e
while true; do
    wait "$child"
    status=$?
    kill -0 "$child" 2>/dev/null || break
done
trap '' TERM USR1
# Retrieve the final child status even if the signal interrupted the first wait.
wait "$child"
status=$?
exit "$status"
