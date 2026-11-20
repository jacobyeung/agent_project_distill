#!/bin/bash
#SBATCH -p preempt
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=02:00:00
#SBATCH --no-requeue
#SBATCH --job-name=JOBNAME_PLACEHOLDER
#SBATCH --output=/project/community/jjyeung/okh7/x_22c714e1/j/%j.log
#SBATCH --error=/project/community/jjyeung/okh7/x_22c714e1/j/%j.err
set -euo pipefail
umask 077
ROOT=/project/community/jjyeung/okh7/x_22c714e1/qd
H=/project/community/jjyeung/okh7/x_22c714e1/rcj
MODE="${1:-b}"
[[ "$MODE" == b || "$MODE" == r ]] || exit 2
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
mkdir "$N"
export TMPDIR="$N/tmp" XDG_CACHE_HOME="$N/cache"
export HF_HOME="$N/cache/hf" TORCH_HOME="$N/cache/torch" TRITON_CACHE_DIR="$N/cache/triton" MPLCONFIGDIR="$N/cache/plot"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export CUDA_VISIBLE_DEVICES= HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
if [[ "$MODE" == r ]]; then
    export R1_OPAQUE_LOGS=1 Q_E1=1 Q_E2=orchard Q_E5=6d38613965 Q_E6=1
    export R1_MODEL_DIR=a32330d0 PYTHONNOUSERSITE=1 HF_HUB_DISABLE_TELEMETRY=1 WANDB_DISABLED=true C1_EXPECT_FLA=1
    export R1_MOUNT=/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b
    export Q_E3=/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/models
    export Q_E4='{"/data2":"/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/data2root"}'
fi
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
cd "$ROOT"
finish() {
    local rc="$?"
    trap - EXIT
    nice -n 10 python3 -I -s -B "$H/x.py" publish "$ROOT" "$N" "$SLURM_JOB_ID" "$rc" || exit 1
    exit "$rc"
}
trap finish EXIT
nice -n 10 python3 -I -s -B "$H/x.py" stage "$ROOT" "$N" "$SLURM_JOB_ID" "$MODE" 2>&1 | nice -n 10 python3 -I -s -B "$ROOT/b/l.py" "$ROOT"
nice -n 10 python3 -I -s -B "$H/x.py" launch "$ROOT" "$N" "$SLURM_JOB_ID" 2>&1 | nice -n 10 python3 -I -s -B "$ROOT/b/l.py" "$ROOT"
