#!/bin/bash
#SBATCH --partition=general
#SBATCH --gres=gpu:h100:1
#SBATCH --time=12:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=200G
#SBATCH --job-name=a15_cot_ap5b97d3c2e8a10
set -euo pipefail
# This wrapper runs inside the read lane's authenticated logical-root namespace.
K=${K:?Set K to the staged opaque overlay directory}
P=${P:?Set P to the sealed unpacked package root}
S=${S:?Set S to the prepared read settings file}
O=${O:?Set O to a fresh local output directory}
: "${SLURM_JOB_ID:?allocation required}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
cd "$K"
# Check the blocked policy before touching the model environment.
/usr/bin/python3 -B -c 'import json,sys; p=json.load(open(sys.argv[1])); sys.exit(0 if p.get("status")=="APPROVED" else "BLOCKED: reviewed parity policy and step-specific source pins required")' "$K/policy.json"
"/scratch/jjyeung/b01ec87a6f29b/d/v/py" -B "$K/run.py" \
  --package "$P" --settings "$S" --out "$O" "$@"
