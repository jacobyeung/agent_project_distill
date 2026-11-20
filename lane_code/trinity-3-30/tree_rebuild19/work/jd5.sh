#!/bin/bash
#SBATCH -p preempt
#SBATCH --job-name=a15_cot_ap24d9b8e2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=48
#SBATCH --mem=800G
#SBATCH --time=04:00:00
#SBATCH --no-requeue
#SBATCH --signal=B:TERM@600
#SBATCH --output=/project/community/jjyeung/okh7/x_22c714e1/j/a15_cot_ap24d9b8e2_%j.log
#SBATCH --error=/project/community/jjyeung/okh7/x_22c714e1/j/a15_cot_ap24d9b8e2_%j.err
set -euo pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TK_JOB_START="$(date +%s)"
X="/project/community/jjyeung/okh7/x_22c714e1"
ROOT="$X/qd"
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
O="$X/o/${SLURM_JOB_ID}"
export TMPDIR="$N/tmp" XDG_CACHE_HOME="$N/cache"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME" "$O"
cp "$X/rdiff.py" "$O/rdiff.py"
python3 -B -I -s "$ROOT/b/v.py" "$ROOT"
source "$ROOT/b/ep.sh"
python3 -B -I -s "$ROOT/b/resolve.py" --pool "/project/community/jjyeung/okh7" --output "$N/r0.json" 2>&1 | python3 -B -I -s "$ROOT/b/l.py" "$ROOT" > "$N/q.log"
setsid bash -c 'set -o pipefail; python3 -B -I -s "$1/b/x.py" "$1" "$2" "$3" 2>&1 | python3 -B -I -s "$1/b/l.py" "$1"' bash "$ROOT" "$N/r0.json" "$N" &
TK_WORK_PID=$!
( for i in $(seq 1 240); do sleep 60; test -e "$O/db_bytes.json" && break; if test -s "$O/routing_selection.json"; then nice -n 10 python3 -B -I -s "$X/dbb3.py" "$N" "$O" "$X/u" >> "$O/dbb.log" 2>&1 && break; fi; done ) &
( for i in $(seq 1 240); do sleep 60; if test -s "$O/routing_selection.json" && test -s "$N/dr/p/q/selection/rows.sqlite" && test -s "$N/dr/p/q/base/rows.sqlite" && test ! -e "$O/rd0"; then nice -n 10 python3 -I -s -B "$X/rdiff.py" "$N/dr/p/q/selection/rows.sqlite" "$N/dr/p/q/base/rows.sqlite" --tree "$N/dr/p/s" --removal-manifest "$N/dr/p/q/n.json" --base "$N/dr/p/q" --out "$O/rd0" > "$O/rdiff.log" 2>&1; echo "rdiff exit $?" >> "$O/rdiff.log"; break; fi; done ) &
rc=0; wait "$TK_WORK_PID" || rc=$?
echo "$(date -u +%FT%TZ) work exit $rc"
test -e "$O/db_bytes.json" || nice -n 10 python3 -B -I -s "$X/dbb3.py" "$N" "$O" "$X/u" >> "$O/dbb.log" 2>&1 || echo "dbb none"
for f in $(find "$N" -maxdepth 7 \( -name materialization.json -o -name receipt.json -o -name r.json \) -size -20M 2>/dev/null); do g=$(echo "${f#$N/}" | tr / _); cp "$f" "$O/k_$g" 2>/dev/null || true; done
exit "$rc"
