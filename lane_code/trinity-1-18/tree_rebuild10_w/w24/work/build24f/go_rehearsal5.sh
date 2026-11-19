#!/bin/bash
set -euo pipefail
# This wrapper and all descendants run at reduced priority.
if [[ "${REHEARSAL5_NICED:-0}" != 1 ]]; then
    export REHEARSAL5_NICED=1
    exec nice -n 10 bash "$0" "$@"
fi
L=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24
cd "$L"
kit="$(readlink -f -- "${1:-$L/out/kit_n_go}")"
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TMPDIR="$L/work/build24f/rehearsal5/tmp"
export XDG_CACHE_HOME="$TMPDIR/cache" HF_HOME="$TMPDIR/hf" TORCH_HOME="$TMPDIR/torch"
export TK_JOB_START="$(date +%s)" REHEARSAL5_KIT="$kit"
ulimit -v 19000000
ulimit -f 204800
py=/scratch/jjyeung/envs/p1cpu/bin/python
if [[ ! -f work/build24f/rehearsal5/PREPARED.json ]]; then
    "$py" -I -s -B work/build24f/make_rehearsal5.py "$kit"
fi
status=0
"$py" -I -s -B work/build24f/rehearsal_runner5.py "$kit" || status=$?
"$py" -I -s -B work/build24f/check_rehearsal5.py || status=1
exit "$status"
