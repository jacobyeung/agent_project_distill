date -u; du -sh /dev/shm/jjyeung /dev/shm/jjyeung/* 2>/dev/null; df -h /dev/shm | tail -1
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader; ls -d /scratch/jjyeung/k1_frames 2>&1
