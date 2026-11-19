#!/bin/bash
set -euo pipefail
# exec gives every descendant reduced priority, including setup and shell helpers.
if [[ "${REHEARSAL_K2_NICED:-0}" != 1 ]]; then
    export REHEARSAL_K2_NICED=1
    exec nice -n 10 bash "$0" "$@"
fi
L=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24
cd "$L"
[[ "$(hostname -s)" == trinity-1-18 ]] || { echo 'Wrong host'; exit 1; }
kit="$(readlink -f -- "${1:-$L/out/kit_n_go}")"
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export REHEARSAL_K2_ROOT="${REHEARSAL_K2_ROOT:-$L/work/build24k/rehearsal_k2}"
export TMPDIR="$REHEARSAL_K2_ROOT/tmp"
export XDG_CACHE_HOME="$TMPDIR/cache" HF_HOME="$TMPDIR/hf" TORCH_HOME="$TMPDIR/torch" TRITON_CACHE_DIR="$TMPDIR/triton"
export TK_JOB_START="$(date +%s)"
ulimit -v 19000000
ulimit -f 204800
py=/scratch/jjyeung/envs/p1cpu/bin/python
"$py" -I -s -B work/build24k/make_rehearsal_k2.py "$kit"
status=0
if [[ "${REHEARSAL_K2_PROBE:-0}" == 1 ]]; then
    "$py" -I -s -B work/build24k/rehearsal_runner2.py "$kit" --probe || status=$?
else
    "$py" -I -s -B work/build24k/rehearsal_runner2.py "$kit" || status=$?
fi
"$py" -I -s -B work/build24k/check_rehearsal.py || status=1
exit "$status"
