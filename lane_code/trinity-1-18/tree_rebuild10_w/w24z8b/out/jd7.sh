#!/bin/bash
#SBATCH -p preempt
#SBATCH --job-name=a15_cot_ap0fd6c118b37d
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=48
#SBATCH --mem=800G
#SBATCH --time=04:00:00
#SBATCH --no-requeue
#SBATCH --signal=B:TERM@600
#SBATCH --output=/tmp/q_22c714e1_%j.log
#SBATCH --error=/tmp/q_22c714e1_%j.err
set -euo pipefail
if [[ "${J7_NICE:-0}" != 1 ]]; then export J7_NICE=1; exec nice -n 10 /bin/bash "$0" "$@"; fi
umask 077
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TK_JOB_START="$(date +%s)"
X="/project/community/jjyeung/okh7/x_22c714e1"
ROOT="$X/qp_11386117"
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
O="$X/o/${SLURM_JOB_ID}"
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
    except OSError as e:
        with (node/'j2.retry.log').open('a') as f:
            f.write(str(int(time.time()))+' E'+str(e.errno)+'\n')
while True:
    publish()
    try:os.kill(int(parent),0)
    except ProcessLookupError:break
    time.sleep(interval)
PYJ2
if [[ "${J7_INNER:-0}" != 1 ]]; then
setsid python3 -B -I -s "$N/j2.py" "$ROOT" "$N" "$X" "$SLURM_JOB_ID" "$$" >>"$N/j2.retry.log" 2>&1 &
mkdir -p "$N/ev" "$O"
BW=$(python3 -B -I -s "$X/j7.py" b "$ROOT")
rc=0
J7_INNER=1 "$BW" --bind / / --dev-bind /dev /dev --proc /proc --bind "$N/ev" "$O" /bin/bash "$0" || rc=$?
python3 -B -I -s "$X/j7.py" p "$N" "$O" "$ROOT" "$rc" || rc=1
python3 -B -I -s "$N/j2.py" "$ROOT" "$N" "$X" "$SLURM_JOB_ID" 999999999 >>"$N/j2.retry.log" 2>&1 || true
exit "$rc"
fi
export TMPDIR="$N/tmp" XDG_CACHE_HOME="$N/cache"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME" "$O"
cp "$X/rdiff.py" "$O/rdiff.py"
python3 -B -I -s "$ROOT/b/v.py" "$ROOT"
source "$ROOT/b/ep.sh"
python3 -B -I -s "$ROOT/b/resolve.py" --pool "/project/community/jjyeung/okh7" --output "$N/r0.json" 2>&1 | python3 -B -I -s "$ROOT/b/l.py" "$ROOT" > "$N/q.log"
setsid bash -c 'set -o pipefail; python3 -B -I -s "$1/b/x.py" "$1" "$2" "$3" 2>&1 | python3 -B -I -s "$1/b/l.py" "$1"' bash "$ROOT" "$N/r0.json" "$N" &
TK_WORK_PID=$!
( for i in $(seq 1 240); do sleep 60; test -e "$O/db_bytes.json" && break; if test -s "$O/routing_selection.json"; then nice -n 10 python3 -B -I -s "$X/dbb3.py" "$N" "$O" "$X/u" >> "$O/dbb.log" 2>&1 && break; fi; test ! -e "$N/j7.done" || break; done ) &
J7_DBB=$!
( for i in $(seq 1 240); do sleep 60; if test -s "$O/routing_selection.json" && test -s "$N/dr/p/q/selection/rows.sqlite" && test -s "$N/dr/p/q/base/rows.sqlite" && test ! -e "$O/rd0"; then python3 -B -I -s "$X/j7.py" m "$N/dr/p/q/n.json" "$N/dr" "$N/rdm.json" && nice -n 10 python3 -I -s -B "$X/rdiff.py" "$N/dr/p/q/selection/rows.sqlite" "$N/dr/p/q/base/rows.sqlite" --tree "$N/dr/p/s" --removal-manifest "$N/rdm.json" --base "$N/dr/p/q" --out "$O/rd0" > "$O/rdiff.log" 2>&1; echo "rdiff exit $?" >> "$O/rdiff.log"; break; fi; test ! -e "$N/j7.done" || break; done ) &
J7_RD=$!
rc=0; wait "$TK_WORK_PID" || rc=$?
touch "$N/j7.done"
echo "$(date -u +%FT%TZ) work exit $rc"
wait "$J7_DBB" || true
wait "$J7_RD" || true
test -e "$O/db_bytes.json" || nice -n 10 python3 -B -I -s "$X/dbb3.py" "$N" "$O" "$X/u" >> "$O/dbb.log" 2>&1 || echo "dbb none"
for f in $(find "$N" -maxdepth 7 \( -name materialization.json -o -name receipt.json -o -name r.json \) -size -20M 2>/dev/null); do g=$(echo "${f#$N/}" | tr / _); cp "$f" "$O/k_$g" 2>/dev/null || true; done
python3 -B -I -s "$N/j2.py" "$ROOT" "$N" "$X" "$SLURM_JOB_ID" 999999999 >>"$N/j2.retry.log" 2>&1 || true
exit "$rc"
