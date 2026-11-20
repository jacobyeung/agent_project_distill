date -u +%TZ; tmux ls 2>/dev/null | grep -E 'tr20'; free -g | sed -n 2p
C=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs; for d in $(ls -d $C/*_tree_rebuild_rev24m4p $C/*_tree_rebuild24m4q 2>/dev/null); do echo "== $d"; test -f $d/final_message.md && head -c 3000 $d/final_message.md; echo; done
