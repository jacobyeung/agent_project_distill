#!/bin/bash
# TEMPLATE ONLY: no submission was run by so_read.
#SBATCH --partition=preempt
#SBATCH --time=2-00:00:00
#SBATCH --array=0-3%4
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --requeue
#SBATCH --signal=B:USR1@900
set -euo pipefail
: "${READ_PYTHON:?Set the staged GPU interpreter}"
: "${READ_SOURCE_ROOT:?Set the patched staged payload source root}"
: "${READ_ARRAY_CONFIG:?Set the immutable array configuration}"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
# Stage the pinned input archives before this entry. The paths must be identical
# on every attempt. journal_root must survive node loss and be shared by attempts.
exec nice -n 10 "$READ_PYTHON" -I -s -B - "$READ_SOURCE_ROOT" "$READ_ARRAY_CONFIG" <<'PY'
import sys
from pathlib import Path
root=Path(sys.argv[1]);config=sys.argv[2]
sys.path[:0]=[str(root),str(root/'tree'),str(root/'b')]
sys.argv=['array_worker',config,'--enable-array']
from h1eval.h10.array_worker import main
raise SystemExit(main())
PY
