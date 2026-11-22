date -u +%FT%TZ; cd /scratch/jjyeung/orch_n30/lever8/j1/out/detect || exit 1
tmux has-session -t j1_gpu 2>/dev/null && echo session_alive || echo session_gone
tail -4 EVENTS.jsonl | cut -c1-400; ls; for f in pass_*.log; do tail -3 $f; done 2>/dev/null
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
