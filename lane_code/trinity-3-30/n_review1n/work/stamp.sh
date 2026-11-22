#!/bin/bash
# Refresh STATUS header time + last-check line, copy to events folder.
L=/scratch/jjyeung/orch_n30/n_review1n; B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
T=$(date -u +%H:%MZ); sed -i "1s/— .*/— $T $(date -u +%F)/" $L/STATUS.md
grep -q '^- Last check' $L/STATUS.md && sed -i "s|^- Last check.*|- Last check $T: $1|" $L/STATUS.md || sed -i "/^## Owed/i - Last check $T: $1\n" $L/STATUS.md
cp $L/STATUS.md $B/events/n_review/STATUS.md
