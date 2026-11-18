#!/bin/bash
# review_cprime private view: my writable copy of cp at r1_pkt; everything of r1_ops6 read-only
exec bwrap --dev-bind / / --tmpfs /scratch/jjyeung/orch_n30 --bind /scratch/jjyeung/orch_n30/review_cprime /scratch/jjyeung/orch_n30/review_cprime --ro-bind /scratch/jjyeung/orch_n30/r1_ops6 /scratch/jjyeung/orch_n30/r1_ops6 \
  --bind /scratch/jjyeung/orch_n30/review_cprime/cpcopy /scratch/jjyeung/orch_n30/r1_pkt \
  --ro-bind /scratch/jjyeung/orch_n30/r1_ops6/rec/r1_ops /scratch/jjyeung/orch_n30/r1_ops \
  --ro-bind /scratch/jjyeung/orch_n30/r1_ops6/snapm/snap_9dd2fbb7 /scratch/jjyeung/orch_n30/r1_ops/work/snap_9dd2fbb7 \
  --ro-bind /scratch/jjyeung/orch_n30/r1_ops6/snapm/snap_08f3a7b2 /scratch/jjyeung/orch_n30/r1_ops/work/snap_08f3a7b2 \
  --ro-bind /scratch/jjyeung/orch_n30/r1_ops6/rec/cont_ops /scratch/jjyeung/orch_n30/cont_ops \
  --ro-bind /scratch/jjyeung/orch_n30/r1_ops6/rec/tree_rebuild_w /scratch/jjyeung/orch_n30/tree_rebuild_w \
  --ro-bind /scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7 /scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7 \
  --chdir /scratch/jjyeung/orch_n30/r1_pkt "$@"
