W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls 2>/dev/null | grep -E 'tr20'; free -g | sed -n 2p
C=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs; d=$(ls -d $C/*_tree_rebuild24m4o2 | tail -1); ls $d | tr '\n' ' '; echo; test -f $d/final_message.md && head -c 3000 $d/final_message.md; ls $W/w24o2/out | grep -E '24M4O|173680|ROUTES'; test -f $W/w24o2/out/BUILD24M4O_REPORT.md && cat $W/w24o2/out/BUILD24M4O_REPORT.md
tail -c 2500 $d/transcript.log | tr -cd "[:print:]\n" | tail -25
