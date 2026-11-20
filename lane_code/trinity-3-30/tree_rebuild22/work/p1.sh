W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; free -g | sed -n 2p; df -h /scratch | tail -1; tmux ls 2>/dev/null
C=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs; d=$(ls -d $C/*_tree_rebuild24m4v | tail -1); echo $d; ls -la $d | tail -3; ls -lt $W/w24v/out | head -12
