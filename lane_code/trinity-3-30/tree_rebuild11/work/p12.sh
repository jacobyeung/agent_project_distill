W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr11; tail -c 500 $W/w21/work/build21/STATUS.md; echo; du -sh $W/w21
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild21b | head -1); ls -la --time-style=+%TZ $d | tail -3; grep -c "at capacity" $d/transcript.log
