echo "HOST $(hostname -s) UTC $(date -u +%FT%TZ)"
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader
echo PROCS; nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader
nvidia-smi --query-gpu=index,uuid --format=csv,noheader
echo DF; df -BG /scratch | tail -1
echo SHM; df -BG /dev/shm | tail -1
