#!/bin/bash
# The child applies the resource limits before importing the sealed launch tree.
set -euo pipefail
J=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14
if [[ $# != 2 ]]; then echo 'usage: admit_test.sh <v.json> <fresh_out_dir_under_J>' >&2; exit 2; fi
exec nice -n 10 /bin/bash -c '
  set -euo pipefail
  ulimit -v 14680064
  ulimit -c 0
  ulimit -f 262144
  export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
  export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
  export VECLIB_MAXIMUM_THREADS=1 BLIS_NUM_THREADS=1 STUDENT_IO_THREADS=1 TOKENIZERS_PARALLELISM=false
  export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
  export TMPDIR="$1/work/build24m4z14/tmp" XDG_CACHE_HOME="$1/work/build24m4z14/tmp/cache"
  export HF_HOME="$TMPDIR/hf" TORCH_HOME="$TMPDIR/torch" TRITON_CACHE_DIR="$TMPDIR/triton"
  exec /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$1/out/admit_test.py" "$2" "$3"
' admit-test "$J" "$1" "$2"
