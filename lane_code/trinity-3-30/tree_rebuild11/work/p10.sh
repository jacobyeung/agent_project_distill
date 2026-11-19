W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr11; tail -c 300 $W/w21/work/build21/STATUS.md; echo
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild21 | head -1); ls -la $d | tail -3; tail -c 3000 $d/transcript.log | tr -cd '[:print:]\n' | grep -v "^\s*$" | tail -20 | cut -c1-200
ls -t $W/w21/work/build21/proofs 2>/dev/null | head; ls $W/w21/work/build21/proofs/native*/ 2>/dev/null | head
