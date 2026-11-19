#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_ph2gate/sb_mask_phrase/work/gate_tests/killed_pass_rjtvx0eu
export CUDA_VISIBLE_DEVICES=''
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export PYTHONDONTWRITEBYTECODE=1
export XDG_CACHE_HOME="$PWD/.cache" HF_HOME="$PWD/.cache/hf" TRITON_CACHE_DIR="$PWD/.cache/triton"
export MPLCONFIGDIR="$PWD/.cache/matplotlib" TMPDIR="$PWD/tmp"
case "$(realpath -m -- "${1:-}")" in
  "$PWD/part2/price.py"|"$PWD/part2/sam3_pass.py")
    /scratch/jjyeung/envs/p1cpu/bin/python -B part2/gate.py "${2:-}" ;;
esac
mkdir -p "$TMPDIR" work out
ulimit -v 40000000
exec nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B "$@"
