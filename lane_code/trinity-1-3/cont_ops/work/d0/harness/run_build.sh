#!/bin/bash
# run_build.sh BINDINGS OUTPUT_DIR : the kit's own launch_s1/build.py, unchanged, inside a private namespace where
# /scratch is a tmpfs holding only the lane folder, the CPU env and the stand-in of the original pin paths.
set -euo pipefail
W=/scratch/jjyeung/orch_n30/cont_ops/work/d0
exec bwrap --ro-bind / / --dev /dev --proc /proc --tmpfs /scratch \
  --bind /scratch/jjyeung/orch_n30/cont_ops /scratch/jjyeung/orch_n30/cont_ops \
  --ro-bind /scratch/jjyeung/envs/p1cpu /scratch/jjyeung/envs/p1cpu --ro-bind /scratch/jjyeung/uv-python /scratch/jjyeung/uv-python \
  --ro-bind $W/standin_orch_cd /scratch/jjyeung/orch_cd \
  --tmpfs /tmp --chdir $W/src \
  /scratch/jjyeung/envs/p1cpu/bin/python -B -m launch_s1.build --base-kit $W/tmpl --output "$2" \
  --pool-receipt $W/base/k/pool_selection.json --bindings "$1"
