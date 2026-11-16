cd /scratch/jjyeung/orch_n30/b05_owngrd/work/x118; tail -c 3000 smoke.log; ls -la; pgrep -af smoke.py | head -3
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader; date -u
