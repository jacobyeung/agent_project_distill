#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
unset PYTHONPATH PYTHONHOME
ROOT="$(pwd -P)"
mkdir -p jt/home jt/cache jt/temp
export HOME="$ROOT/jt/home" XDG_CACHE_HOME="$ROOT/jt/cache" TMPDIR="$ROOT/jt/temp"
export HF_HOME="$ROOT/jt/cache/hf" TORCH_HOME="$ROOT/jt/cache/torch" TRITON_CACHE_DIR="$ROOT/jt/cache/triton"
export TMP="$TMPDIR" TEMP="$TMPDIR" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
if [[ -e out ]]; then
    mv -- out "out_saved_$(date -u +%Y%m%dT%H%M%S)_$$"
fi
mkdir out
P="$ROOT/runtime/uv/bin/python3.12"
NP=/tmp/b7e31d84/runtime/uv/bin/python3.12
if [[ ! -x "$P" ]]; then
    P=/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12
    NP="$P"
fi
rc=0
nice -n 19 /usr/bin/bwrap --dev-bind / / --bind "$ROOT/jt" /tmp     --bind "$ROOT" /tmp/b7e31d84 --chdir /tmp/b7e31d84     --setenv HOME /tmp/home --setenv XDG_CACHE_HOME /tmp/cache     --setenv TMPDIR /tmp/temp --setenv TMP /tmp/temp --setenv TEMP /tmp/temp     --setenv HF_HOME /tmp/cache/hf --setenv TORCH_HOME /tmp/cache/torch     --setenv TRITON_CACHE_DIR /tmp/cache/triton --die-with-parent     "$NP" -I -s -B /tmp/b7e31d84/rh_prepare.py >out/outer.log 2>&1 || rc=$?
# Collection runs on the host even when the outer namespace never starts.
exec nice -n 19 "$P" -I -s -B rh_prepare.py --collect "$rc"
