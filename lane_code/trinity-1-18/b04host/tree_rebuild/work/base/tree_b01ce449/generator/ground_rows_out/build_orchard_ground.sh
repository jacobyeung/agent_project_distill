#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 RAYON_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false
export PYTHONPATH="$HERE:$HERE/../work/derivgen_v7:${ORCHARD_TREE:-/scratch/jjyeung/orch_cd/orchard_cp2/work/c1mix_ow4}"
exec /scratch/jjyeung/envs/p1cpu/bin/python -B -c '
from student_pilot import carrier_c1_routing as reader
from orchard_ground_adapter import install
install(reader)
reader.main()
' "$@"
