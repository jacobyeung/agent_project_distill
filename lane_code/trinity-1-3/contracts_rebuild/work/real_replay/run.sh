#!/usr/bin/env bash
set -euo pipefail
set -o noclobber
L=/scratch/jjyeung/orch_n30/contracts_rebuild
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export XDG_CACHE_HOME=$L/work/.cache CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TMPDIR=$L/work/real_replay/tmp
mkdir -p "$TMPDIR" "$L/out/real_replay"
cd "$L"
exec > "$L/out/real_replay/run_$(date -u +%Y%m%dT%H%M%SZ).log" 2>&1
echo 'Gravity source: G3T tower gravity, not student-head gravity.'
py=/scratch/jjyeung/envs/p1cpu/bin/python
"$py" -I -s -B "$L/work/real_replay/prepare.py"
"$py" -I -s -B "$L/work/real_replay/replay.py" base
"$py" -I -s -B "$L/work/real_replay/replay.py" off
"$py" -I -s -B "$L/work/real_replay/replay.py" on
"$py" -I -s -B "$L/work/real_replay/summarize.py"
