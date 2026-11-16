hostname; date -u; du -sh /dev/shm/jjyeung 2>/dev/null; ls /dev/shm/jjyeung 2>/dev/null; df -h /dev/shm /scratch | tail -2; free -g | head -2
ls /scratch/jjyeung/envs 2>/dev/null; ls -la /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python 2>&1; cat /scratch/jjyeung/envs/sam3_capretry_native_v1/pyvenv.cfg 2>&1 | head -3
nvidia-smi --query-gpu=index,name,memory.used,utilization.gpu --format=csv,noheader; nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader | head
tmux ls 2>&1 | head
