#!/bin/bash
# Run only after the orchestrator supplies a CPU Python environment with Torch, pytest and safetensors.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${B1_PYTHON:?Set an approved CPU Python executable}"
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TMPDIR="$PWD/work/tmp" XDG_CACHE_HOME="$PWD/work/cache" HF_HOME="$PWD/work/cache/hf"
mkdir -p "$TMPDIR" "$HF_HOME"
"$B1_PYTHON" -B work/test_b1.py
"$B1_PYTHON" -B work/test_select_stubs.py
"$B1_PYTHON" -B out/test_b1_report.py
# The known missing b04 fixtures are reported rather than hidden.
existing_before=0
"$B1_PYTHON" -B work/run_existing.py --baseline || existing_before=$?
existing_after=0
"$B1_PYTHON" -B work/run_existing.py || existing_after=$?
printf "Existing suite exit codes: baseline=%s patched=%s\n" "$existing_before" "$existing_after"
cd work/replay
NP=8 OUT=../../out/replay_patched.jsonl "$B1_PYTHON" -B replay_patched.py
cd ../..
"$B1_PYTHON" -B work/check_replay.py
