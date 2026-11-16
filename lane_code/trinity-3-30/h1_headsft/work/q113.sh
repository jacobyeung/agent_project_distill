set -u
hostname -s; date -u +%FT%TZ
free -g | head -2; nproc
df -h /scratch | tail -1; df -h /dev/shm | tail -1
echo "== shm"; ls -la /dev/shm/jjyeung 2>&1 | head -30
for d in /dev/shm/jjyeung/*; do [ -d "$d" ] && echo "$d: $(ls "$d" | head -8 | tr '\n' ' ')"; done 2>/dev/null | head -30
echo "== exports"; ls -la /dev/shm/jjyeung/exports 2>&1 | head; ls /dev/shm/jjyeung/exports/* 2>&1 | head -20
echo "== envs"; ls /scratch/jjyeung/envs 2>&1 | head -30
echo "== gpus"; nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>&1
