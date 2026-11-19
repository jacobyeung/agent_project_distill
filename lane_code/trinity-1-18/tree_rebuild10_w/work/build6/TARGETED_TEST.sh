#!/bin/bash
set -euo pipefail
BUILD6_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
export TMPDIR="$BUILD6_ROOT/work/tmp" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
export XDG_CACHE_HOME="$TMPDIR/cache" XDG_CONFIG_HOME="$TMPDIR/config" HF_HOME="$TMPDIR/hf" TRITON_CACHE_DIR="$TMPDIR/triton" CONDA_PKGS_DIRS="$TMPDIR/conda" MPLCONFIGDIR="$TMPDIR/mpl" TORCH_HOME="$TMPDIR/torch"
ulimit -f 204800
exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$BUILD6_ROOT/work/build6/targeted.py"
