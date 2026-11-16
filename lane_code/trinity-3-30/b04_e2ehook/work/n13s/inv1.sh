hostname -s; date -u +%FT%TZ; df -h /dev/shm /scratch | tail -2; free -g | head -2
cd /dev/shm/jjyeung && ls -la; for d in exports exports/m544 b05 b05/stage b11_presence; do echo "== $d"; ls -la $d 2>&1 | head -40; done
echo "== b05/stage depth2"; for d in /dev/shm/jjyeung/b05/stage/*/; do echo "-- $d"; ls $d | head -15; done
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
ls /scratch/jjyeung/envs; ls /scratch/jjyeung | head -30
tmux ls 2>&1 | head
