#!/usr/bin/env bash
set -euo pipefail
if [[ $(hostname -s) != trinity-1-18 ]]; then
  echo 'E-A is allocated on trinity-1-18 only.' >&2
  exit 2
fi
EA_GPU=${1:?Usage: bash out/run_EA_arm.sh GPU ARM [options]}
shift
if [[ $EA_GPU != 7 ]]; then
  echo 'Only physical GPU 7 is assigned to this run.' >&2
  exit 2
fi
export CUDA_VISIBLE_DEVICES=$EA_GPU
EA_LANE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
EA_ROOT=${EA_ROOT:-/scratch/jjyeung/ownenc_EA_r3}
EA_WEIGHTS=${EA_WEIGHTS:-$EA_LANE/out/WEIGHTS.gpu.json}
EA_FEATURES=${EA_FEATURES:-/dev/shm/jjyeung_probe_r3/feats}
EA_RESULTS=${EA_RESULTS:-$EA_ROOT/results}
EA_LEDGER=${EA_LEDGER:-$EA_ROOT/GPU_TIME.json}
EA_ARM=${1:?Usage: bash out/run_EA_arm.sh GPU A1 [--phases smoke,extract,T1,T4]}
shift
case "$EA_ROOT" in /scratch/*) ;; *) echo 'EA_ROOT must be local scratch.' >&2; exit 2;; esac
case "$EA_RESULTS" in /scratch/*) ;; *) echo 'EA_RESULTS must be local scratch.' >&2; exit 2;; esac
case "$EA_FEATURES" in /dev/shm/*) ;; *) echo 'EA_FEATURES must be on the GPU node RAM disk.' >&2; exit 2;; esac
source /scratch/jjyeung/orch_cd/mdg_build/work/c1mix_mdg/scripts/mdg_env.sh
export CUDA_VISIBLE_DEVICES
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
export XDG_CACHE_HOME=$EA_ROOT/cache HF_HOME=$EA_ROOT/hf TRITON_CACHE_DIR=$EA_ROOT/triton
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export PYTHONPATH="$EA_LANE/work:$EA_LANE/out:${PYTHONPATH:-}"
mkdir -p "$EA_RESULTS" "$EA_FEATURES"
cd "$EA_LANE"
EA_EXTRA=()
if [[ -n ${EA_LABELS:-} ]]; then EA_EXTRA+=(--labels "$EA_LABELS"); fi
if [[ -n ${EA_FUSION_ROWS:-} ]]; then EA_EXTRA+=(--fusion-rows "$EA_FUSION_ROWS"); fi
exec /data3/shared/scripts/vnice/vnice.sh nice -n 10 "$MDG_PYTHON" work/run_arm.py \
  --arm "$EA_ARM" --weights "$EA_WEIGHTS" --results "$EA_RESULTS" \
  --feature-root "$EA_FEATURES" --ledger "$EA_LEDGER" --budget-minutes 240 --device cuda:0 "${EA_EXTRA[@]}" "$@"
