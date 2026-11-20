W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls 2>/dev/null | grep -E 'tr19|tr20'; free -g | sed -n 2p; df -h /scratch | tail -1
C=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs; for d in $(ls -d $C/*_tree_rebuild_rev24m4m $C/*_tree_rebuild24m4n 2>/dev/null); do echo "== $d"; ls $d | tr '\n' ' '; echo; test -f $d/final_message.md && head -c 4000 $d/final_message.md; echo; done
ls $W/w24n2/out 2>/dev/null | tr '\n' ' '
