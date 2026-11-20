#!/bin/bash
# Print new event/inbox files since the last poll (names only).
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; M=/scratch/jjyeung/orch_n30/fb_pack3/work/.poll_mark
[ -f $M ] || touch -d '-10 min' $M
date -u +%H%MZ
for d in $B/events/fb_pack /scratch/jjyeung/orch_n30/fb_pack3/inbox; do find $d -maxdepth 1 -type f -newer $M ! -name STATUS.md -printf '%f\n'; done
find $B/events/tree_rebuild -maxdepth 1 -type f -newer $M -name '*fb_pack*' -printf 'TR %f\n'
touch $M
