W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr13
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild_rev23c | head -1); ls $d | tr '\n' ' '; echo; cat $d/final_message.md 2>/dev/null
tail -3 $W/w23/work/build23b/capacity_final_tr13.log | cut -c1-300
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild24 | head -1); tail -c 1500 $d/transcript.log | tr -cd "[:print:]\n" | grep -v "^[ +@-]" | tail -4 | cut -c1-300
