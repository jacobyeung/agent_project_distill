#!/bin/bash
set -euo pipefail
arm=$1
gpu=$2
export CUDA_VISIBLE_DEVICES="$gpu"
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
export HF_HOME=/data2/jjyeung/cache/huggingface HUGGINGFACE_HUB_CACHE=/data2/jjyeung/cache/huggingface/hub
export TORCH_HOME=/data2/jjyeung/cache/torch PIP_CACHE_DIR=/data2/jjyeung/cache/pip
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4
export AGENT_COORD_DIR=/data2/jjyeung/agent_project/.coord AGENT_ID=student-shakedown-20260918
export TMPDIR=/data2/jjyeung/agent_project_data/student_shakedown_20260918/tmp
export TRITON_CACHE_DIR=/data2/jjyeung/agent_project_data/student_shakedown_20260918/cache/triton
export XDG_CACHE_HOME=/data2/jjyeung/agent_project_data/student_shakedown_20260918/cache
repo=/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/trainer_repo
out=/data2/jjyeung/agent_project_data/student_shakedown_20260918
py=/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/venv/bin/python
work_id="student__shakedown_${arm}__diag73__s17__2b7032f417"
cd "$repo"
"$py" -B -u -m student_pilot.shakedown train --arm "$arm"
"$py" -B -u -m student_pilot.shakedown evaluate --arm "$arm"
if [ "$arm" = answer_only ]; then
  "$py" -B -u -m student_pilot.shakedown evaluate --arm base
fi
"$py" -B /home/jjyeung/agent_project/agent/coord.py complete "$work_id" --result "$out/$arm/evaluation_complete.json"
printf '0\n' > "$out/$arm/exit_code"
