#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/b15_vla/navrun
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
export XDG_CACHE_HOME="$PWD/out/cache" NUMBA_CACHE_DIR="$PWD/out/cache/numba"
export PYTHONPATH="$PWD:/scratch/jjyeung/orch_n30/b15_vla/work/orchard_kit/kit/ext_where:/scratch/jjyeung/orch_n30/b15_vla/work/orchard_kit/kit/ext_v2/vla_heads${PYTHONPATH:+:$PYTHONPATH}"
export HABITAT_SIM_LOG=quiet MAGNUM_LOG=quiet
exec nice -n 19 /scratch/jjyeung/envs/nav_habitat024/bin/python "$@"
