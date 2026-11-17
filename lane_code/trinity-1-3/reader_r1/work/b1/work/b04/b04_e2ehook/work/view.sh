#!/bin/bash
# Run a command in the 1-18 view: b04host3 copies mapped onto the 3-30 lane paths the code names.
H=/scratch/jjyeung/orch_n30/b04host3
exec bwrap --dev-bind / / --bind $H/b04_e2ehook /scratch/jjyeung/orch_n30/b04_e2ehook \
  --bind $H/tree_rebuild /scratch/jjyeung/orch_n30/tree_rebuild \
  --bind /scratch/jjyeung/k1 /scratch/jjyeung/n30_mirror/k1_ops3 "$@"
