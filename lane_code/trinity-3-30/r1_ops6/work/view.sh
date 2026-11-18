#!/bin/bash
# Run a command inside a private mount view that shows lane r1_ops6's recovered copies at the
# original trinity-1-3 absolute paths (read-write lane folder; other orch_n30 lanes hidden).
L=/scratch/jjyeung/orch_n30/r1_ops6
O=/scratch/jjyeung/orch_n30
exec bwrap --dev-bind / / --tmpfs $O --bind $L $L \
  --bind $L/cp $O/r1_pkt \
  --bind $L/rec/r1_ops $O/r1_ops \
  --bind $L/snapm/snap_9dd2fbb7 $O/r1_ops/work/snap_9dd2fbb7 \
  --bind $L/snapm/snap_08f3a7b2 $O/r1_ops/work/snap_08f3a7b2 \
  --ro-bind $L/store/a2_vqa_v7 $O/rows_r1/out/a2_vqa_v7 \
  --chdir "${VIEW_CWD:-$O/r1_pkt}" "$@"
