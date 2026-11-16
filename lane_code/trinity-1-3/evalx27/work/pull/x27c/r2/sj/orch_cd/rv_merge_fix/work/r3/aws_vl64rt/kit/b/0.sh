#!/bin/bash
#SBATCH --job-name=a15_cot_ap67e3f300
#SBATCH --nodes=1
#SBATCH --gres=gpu:8
#SBATCH --mem=640G
#SBATCH --cpus-per-task=32
#SBATCH --partition=batch
#SBATCH --qos=normal
#SBATCH --time=04:00:00
#SBATCH --chdir=/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/c4b50b5f
#SBATCH --output=/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/c4b50b5f/o/%j.out
#SBATCH --error=/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/c4b50b5f/o/%j.err
set -euo pipefail
export PATH=/usr/local/bin:/usr/bin:/bin
R=/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/c4b50b5f
J=/tmp/c4b50b5f/${SLURM_JOB_ID:?}
mkdir -p "$J" "$J/cache" "$J/tmp"
# Keep the tails of the node-local logs after the job ends (opaque names).
trap 'for n in 0 1; do [ -f "$J/$n.log" ] && tail -c 20000 "$J/$n.log" > "$R/o/${SLURM_JOB_ID}.t$n" || true; done' EXIT
for key in $(compgen -e); do
    case "$key" in *_API_KEY|*_SECRET*|*_TOKEN|*_CREDENTIAL*) unset "$key" ;; esac
done
source /lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/1742c666/b/c2.sh > "$J/0.log" 2>&1
export HOME="$J" TMPDIR="$J/tmp" XDG_CACHE_HOME="$J/cache"
export HF_HOME="$J/cache/hf" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export VLLM_NO_USAGE_STATS=1 DO_NOT_TRACK=1 VLLM_USE_FLASHINFER_SAMPLER=0 PYTHONDONTWRITEBYTECODE=1
cd "$J"
/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/19252904/e/bin/python -B "$R/b/1.py" "$R" "$J" > "$J/1.log" 2>&1
