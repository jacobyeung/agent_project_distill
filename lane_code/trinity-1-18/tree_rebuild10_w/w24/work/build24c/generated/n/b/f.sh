#!/bin/bash
set -eu
umask 077
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
ROOT="$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")"
N="${1:?}.h"
export TMPDIR="$N/tmp" XDG_CACHE_HOME="$N/cache"
export HF_HOME="$N/cache/hf" TORCH_HOME="$N/cache/torch" TRITON_CACHE_DIR="$N/cache/triton"
export CUDA_CACHE_PATH="$N/cache/cu" MPLCONFIGDIR="$N/cache/plot"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
cd "$N"
exec python3 -B -I -s "$ROOT/b/a.py" p "$1"
