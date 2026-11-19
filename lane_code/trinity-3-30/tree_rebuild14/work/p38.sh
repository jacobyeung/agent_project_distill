W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ
tmux kill-session -t tr14_b24h && echo KILLED_24H; sleep 2; pgrep -af "tree_rebuild24h" | head -3 | cut -c1-150
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild_rev24f | head -1); echo $d; sed -n 1,12p $d/final_message.md; sed -n '/did not check/,$p' $d/final_message.md | head -8
cat $W/w24/out/BUILD24G_REPORT.md | head -25
