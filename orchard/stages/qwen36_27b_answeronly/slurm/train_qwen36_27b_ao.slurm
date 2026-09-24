#!/usr/bin/env bash
#SBATCH -A mt01
#SBATCH -p advanced
#SBATCH -q adv_4gpu_qos
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:4
#SBATCH --cpus-per-task=32
#SBATCH --mem=384G
#SBATCH --time=1-00:00:00
#SBATCH --no-requeue
#SBATCH --output=/project/community/jjyeung/distill/logs/%x-%j.log
set -euo pipefail
export WORLD_SIZE="${WORLD_SIZE:-4}"
exec bash "${ORCH_DEPLOY:?Use the frozen answer-only deployment}/scripts/orchard/run_train.sh" qwen36_27b "${1:?dataset root}" "${2:?run ID}"
