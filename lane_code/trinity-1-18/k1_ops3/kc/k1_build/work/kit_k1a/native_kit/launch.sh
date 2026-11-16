#!/usr/bin/env bash
set -euo pipefail
: "${O3_PYTHON:?Set the existing native model Python}"
: "${O3_MANIFEST:?Set the validated manifest}"
: "${O3_OUTPUT:?Set a fresh local output directory}"
: "${CUDA_VISIBLE_DEVICES:?Set exactly one allocated GPU}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export XDG_CACHE_HOME="$O3_OUTPUT/runtime_cache" HF_HOME="$O3_OUTPUT/runtime_cache/hf" TRITON_CACHE_DIR="$O3_OUTPUT/runtime_cache/triton"
KIT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
exec "$O3_PYTHON" -I -s -B "$KIT_DIR/watchdog.py" --python "$O3_PYTHON" --manifest "$O3_MANIFEST" --out "$O3_OUTPUT" --max-seconds "${O3_MAX_SECONDS:-14400}" --max-bytes "${O3_MAX_BYTES:-10000000000}"
