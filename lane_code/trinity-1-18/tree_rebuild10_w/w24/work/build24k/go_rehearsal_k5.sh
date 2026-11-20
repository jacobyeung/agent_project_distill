#!/bin/bash
set -euo pipefail
if [[ "${REHEARSAL_K5_NICED:-0}" != 1 ]]; then
    export REHEARSAL_K5_NICED=1
    exec nice -n 10 bash "$0" "$@"
fi
ulimit -v 19000000
ulimit -f 204800
L=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24k
cd "$L/../.."
[[ "$(hostname -s)" == trinity-1-18 ]] || { echo 'Wrong host'; exit 1; }
[[ $# == 2 ]] || { echo 'Usage: go_rehearsal_k5.sh KIT_PATH FRESH_BUILD24K_REHEARSAL_K5_ROOT'; exit 2; }
kit="$(readlink -f -- "$1")"
export REHEARSAL_K5_ROOT="$(readlink -m -- "$2")"
[[ ! -e "$REHEARSAL_K5_ROOT" && ! -L "$REHEARSAL_K5_ROOT" ]] || { echo 'Fresh root required; no retry'; exit 1; }
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TMPDIR="$REHEARSAL_K5_ROOT/tmp"
export XDG_CACHE_HOME="$TMPDIR/cache" HF_HOME="$TMPDIR/hf" TORCH_HOME="$TMPDIR/torch" TRITON_CACHE_DIR="$TMPDIR/triton"
export TK_JOB_START="$(date +%s)"
py=/scratch/jjyeung/envs/p1cpu/bin/python
"$py" -I -s -B "$L/make_rehearsal_k5.py" "$kit"
status=0
"$py" -I -s -B "$L/rehearsal_runner_k5.py" "$kit" || status=$?
"$py" -I -s -B "$L/check_rehearsal_base_k5.py" || status=1
"$py" -I -s -B "$L/finalise_rehearsal_k5.py" || status=1
exit "$status"
