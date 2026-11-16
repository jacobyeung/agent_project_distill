#!/bin/bash
# gate_check.sh KIT MODE : the kit's own b/g.py check, in a namespace with a private /tmp (run directory), host python3.
exec bwrap --ro-bind / / --dev /dev --proc /proc --tmpfs /tmp \
  --bind /scratch/jjyeung/orch_n30/cont_ops/work/d0/t2_persist /scratch/jjyeung/orch_n30/cont_ops/work/d0/t2_persist \
  --setenv SLURM_JOB_ID 999001 /scratch/jjyeung/envs/p1cpu/bin/python -I -c 'import sys; sys.path.insert(0, sys.argv[1]+"/b"); import g; print("RESULT", g.check(sys.argv[1], None, sys.argv[2]) and "PASS")' "$1" "$2"
