#!/usr/bin/env bash
set -euo pipefail
GEO_BAKEOFF_ROOT="$(dirname -- "$(dirname -- "$(realpath -- "${BASH_SOURCE[0]}")")")"
export GEO_BAKEOFF_ROOT
export GEO_BAKEOFF_ASSETS="$GEO_BAKEOFF_ROOT/assets"
export GEO_BAKEOFF_DATA_ROOT="$GEO_BAKEOFF_ROOT/data"
export GEO_BAKEOFF_OUTPUT_ROOT="${GEO_BAKEOFF_OUTPUT_ROOT:-$GEO_BAKEOFF_ROOT/out}"
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PYTHONSAFEPATH=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=8 NUMEXPR_NUM_THREADS=1
export TORCHINDUCTOR_COMPILE_THREADS=1 MAX_JOBS=8 TOKENIZERS_PARALLELISM=false
export TMPDIR="$GEO_BAKEOFF_ROOT/work/tmp"
export XDG_CACHE_HOME="$TMPDIR/cache" XDG_CONFIG_HOME="$TMPDIR/config" MPLCONFIGDIR="$TMPDIR/matplotlib"
export HF_HOME="$TMPDIR/hf" TORCH_HOME="$TMPDIR/torch" TRITON_CACHE_DIR="$TMPDIR/triton"
export TORCH_EXTENSIONS_DIR="$TMPDIR/extensions" NUMBA_CACHE_DIR="$TMPDIR/numba"
export CUDA_CACHE_PATH="$TMPDIR/cuda"
export PYTHONPATH="$GEO_BAKEOFF_ROOT/work:$GEO_BAKEOFF_ROOT/runtime/site"
for repository in "$GEO_BAKEOFF_ASSETS"/*-src; do
    export PYTHONPATH="$PYTHONPATH:$repository:$repository/src"
done
for source_root in "$GEO_BAKEOFF_ASSETS"/*-src/*; do
    if [[ -d "$source_root" ]]; then
        export PYTHONPATH="$PYTHONPATH:$source_root:$source_root/src"
    fi
done
if [[ -d "$GEO_BAKEOFF_ROOT/runtime/base" ]]; then
    export PYTHONHOME="$GEO_BAKEOFF_ROOT/runtime/base"
fi
export PATH="$GEO_BAKEOFF_ROOT/runtime/bin:$GEO_BAKEOFF_ROOT/runtime/base/bin:$PATH"
library_paths="$GEO_BAKEOFF_ROOT/runtime/base/lib:$GEO_BAKEOFF_ROOT/runtime/site/torch/lib"
for directory in "$GEO_BAKEOFF_ROOT/runtime/site"/nvidia/*/lib; do
    [[ ! -d "$directory" ]] || library_paths="$library_paths:$directory"
done
export LD_LIBRARY_PATH="$library_paths"
