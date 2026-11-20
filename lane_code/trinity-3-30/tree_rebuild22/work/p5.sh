W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; free -g | sed -n 2p; tmux ls 2>/dev/null | grep tr2
C=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs; d=$(ls -d $C/*_tree_rebuild24m4w | tail -1); echo $d; ls -la $d | tail -2; ls -lt $W/w24w/out | head -6
R=/scratch/jjyeung/orch_n30/tr21_revT; ls -la $R; tail -c 600 $R/cursor.log; test -f $R/REVIEW_VERDICT.md && cat $R/REVIEW_VERDICT.md
