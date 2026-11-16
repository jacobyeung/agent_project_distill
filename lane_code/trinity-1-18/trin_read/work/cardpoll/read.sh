hostname -s; date -u +%FT%TZ; df -B1 --output=avail /scratch | tail -1
nvidia-smi --query-gpu=index,uuid,memory.used --format=csv,noheader
echo APPS; nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader
for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader); do ps -o pid=,user=,etime=,comm= -p $p; done
