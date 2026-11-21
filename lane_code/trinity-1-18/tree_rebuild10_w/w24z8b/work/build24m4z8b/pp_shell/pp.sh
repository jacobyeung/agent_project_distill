#!/bin/bash
#SBATCH -p preempt
#SBATCH --job-name=a15_cot_ap8ad01bf06cd3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --output=/tmp/p_22c714e1_%j.log
#SBATCH --error=/tmp/p_22c714e1_%j.err
set -euo pipefail
if [[ "${J7_NICE:-0}" != 1 ]]; then export J7_NICE=1; exec nice -n 10 /bin/bash "$0" "$@"; fi
umask 077
ulimit -v 14680064
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export CUDA_VISIBLE_DEVICES=""
X=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z8b/work/build24m4z8b/pp_shell/x
ROOT="$X/qp_11386117"
N="${SLURM_TMPDIR:-/tmp}/p_22c714e1_${SLURM_JOB_ID:?}"
O="$X/o/$SLURM_JOB_ID"
mkdir -p "$N"
export TMPDIR="$N/tmp" XDG_CACHE_HOME="$N/cache" HF_HOME="$N/cache/hf"
export TORCH_HOME="$N/cache/torch" TRITON_CACHE_DIR="$N/cache/triton"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
cd "$N"
mkdir -p "$N/a" "$N/ev" "$O"
rc=0
BW=$(python3 -B -I -s "$X/j7.py" b "$ROOT" 2>"$N/p1.log") || rc=$?
if [[ "$rc" == 0 ]]; then
    "$BW" --bind / / --dev-bind /dev /dev --proc /proc --bind "$N/ev" "$O" python3 -B -I -s "$X/j7.py" q "$ROOT" "$N/a" /project/community/jjyeung/okh7 >"$N/p0.log" 2>&1 || rc=$?
fi
if [[ ! -f "$N/a/p0.json" ]]; then printf '{"mode":"q","completed":false,"error":"E00"}\n' >"$N/a/p0.json"; fi
test "$(stat -c %s "$N/a/p0.json")" -lt 100000
cp "$N/a/p0.json" "$O/p0.json"
exit "$rc"
