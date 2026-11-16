hostname; date -u; df -h /scratch /dev/shm | tail -2; ls /dev/shm | head; du -sh /dev/shm/* 2>/dev/null | head
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader
nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader | head; free -g | sed -n 2p; nproc
