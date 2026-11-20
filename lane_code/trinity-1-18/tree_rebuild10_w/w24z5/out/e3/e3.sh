#!/bin/bash
#SBATCH --partition=preempt
#SBATCH --job-name=a15_cot_ap04edabbeceeb
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --output=/tmp/q_e3_%j.log
#SBATCH --error=/tmp/q_e3_%j.err
# The final pass requires the four o parts while X is full.
set -euo pipefail
umask 077
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1
X=/project/community/jjyeung/okh7/x_22c714e1
D="$X/e3"
N="${SLURM_TMPDIR:-/tmp}/q_e3_${SLURM_JOB_ID:?}"
mkdir -p "$N/tmp" "$N/probe" "$N/logs" "$N/obs" "$N/bin"
export TMPDIR="$N/tmp"
exec >>"$N/logs/e3.log" 2>>"$N/logs/e3.err"
PY=$(command -v python3)
export E3_PY="$PY" E3_N="$N"
export SLURM_JOB_END_TIME="${SLURM_JOB_END_TIME:-$(( $(date +%s) + 3600 ))}"
finish() {
    rc=$?
    trap - EXIT
    if [[ -f "$N/e3.py" ]]; then
        nice -n 10 "$PY" -I -s -B "$N/e3.py" finish "$N" "$X" "$SLURM_JOB_ID" "$rc" || { echo 'E3_FAIL E90'; exit 1; }
    else
        echo 'E3_FAIL E91; local logs retained'
    fi
    exit "$rc"
}
trap finish EXIT
nice -n 10 "$PY" -I -s -B "$D/e3.py" stage "$D" "$N" "$X" "$SLURM_JOB_ID"
if ! nice -n 10 unshare -Urm bash -c 'mount -t tmpfs -o size=1m tmpfs "$E3_N/probe" && test -d "$E3_N/probe"'; then
    nice -n 10 "$PY" -I -s -B "$N/e3.py" fail "$N" E01
    echo 'E3_FAIL E01: unshare -Urm or tmpfs unavailable'
    exit 1
fi
set +e
nice -n 10 unshare -Urm "$PY" -I -s -B "$N/e3.py" run "$N" "$X" "$SLURM_JOB_ID"
rc=$?
set -e
exit "$rc"
