#!/bin/bash
W=/scratch/jjyeung/orch_n30/tree_rebuild_w; R=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261116T103023Z_tree_rebuild6
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild
date -u +%H:%MZ; ls $R | tr '\n' ' '; echo; tmux has-session -t tree_rebuild_b6 2>/dev/null && echo tmux_alive || echo tmux_gone
d=$(ls -t $W/work/build6/proofs | head -1); echo "proof=$d $(cat $W/work/build6/proofs/$d/progress.json 2>/dev/null | cut -c1-200)"
stat -c '%y %n' $W/work/build6/STATUS.md $R/transcript.log | cut -c12-16,36-
ls $W/out | grep -i -E "build6|b6_" ; ls $W/inbox; ls -t $E | grep ORCH | head -2
