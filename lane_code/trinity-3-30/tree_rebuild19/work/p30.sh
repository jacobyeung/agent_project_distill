W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr19
R=$(ls -td /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*_tree_rebuild_rev24m4k2 | head -1); echo $R; test -f $R/final_message.md && cat $R/final_message.md
tail -3 /scratch/jjyeung/orch_n30/tr19_revC1/cursor.log | cut -c1-300; ls /scratch/jjyeung/orch_n30/tr19_revC1; ls /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24l/out | grep -i 24M4L
