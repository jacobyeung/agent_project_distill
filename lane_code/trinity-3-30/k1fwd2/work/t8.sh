tmux ls 2>/dev/null | grep k1fwd2; tail -c 600 /scratch/jjyeung/orch_n30/k1fwd2/rev.log; ls -t /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs | grep k1fwd2 | head -2
d=$(ls -td /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/*_k1fwd2_rev 2>/dev/null | head -1); ls -la $d; cat $d/final_message.md 2>/dev/null
