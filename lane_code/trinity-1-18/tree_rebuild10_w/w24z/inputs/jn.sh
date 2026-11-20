#!/bin/bash
#SBATCH -p advanced
#SBATCH --job-name=a15_cot_apb2edfac4
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:4
#SBATCH --cpus-per-task=48
#SBATCH --mem=800G
#SBATCH --time=24:00:00
#SBATCH --no-requeue
#SBATCH --signal=B:TERM@600
#SBATCH --output=/project/community/jjyeung/okh7/x_22c714e1/j/a15_cot_apb2edfac4_%j.log
#SBATCH --error=/project/community/jjyeung/okh7/x_22c714e1/j/a15_cot_apb2edfac4_%j.err
set -euo pipefail
set -o pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1
X="/project/community/jjyeung/okh7/x_22c714e1"
ROOT="$X/n"
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
mkdir -p "$N" "$X/o/${SLURM_JOB_ID}"
g=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2>&1 | head -4 || true); echo "$(date -u +%FT%TZ) gpus: $g" | tr '\n' ';'; echo
[ "$(nvidia-smi -L 2>/dev/null | grep -c H100)" -ge 4 ] || { echo "$(date -u +%FT%TZ) fewer than 4 H100; stop before staging"; exit 3; }
echo "$(date -u +%FT%TZ) resolve start"
python3 -B -I -s "$ROOT/b/v.py" "$ROOT"
OMP_NUM_THREADS=8 python3 -B -I -s "$ROOT/b/resolve.py" --pool "/project/community/jjyeung/okh7" --output "$N/r0.json" 2>&1 | python3 -B -I -s "$ROOT/b/l.py" "$ROOT"
echo "$(date -u +%FT%TZ) resolve done; exec job.sh"
exec bash "$ROOT/job.sh" "$N/r0.json"
