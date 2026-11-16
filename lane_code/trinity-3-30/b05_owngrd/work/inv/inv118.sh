hostname -s; date -u
df -h /scratch /dev/shm | tail -2
ls /scratch/jjyeung/ | head -80
echo ==frames; ls /scratch/jjyeung/k1_frames 2>/dev/null | wc -l; du -sh /scratch/jjyeung/k1_frames 2>/dev/null
echo ==envs; ls /scratch/jjyeung/envs 2>/dev/null
echo ==owngpu; ls -d /scratch/jjyeung/*/own_ground_gpu* /scratch/jjyeung/orch_n30/*/own_ground_gpu* /scratch/jjyeung/own_ground_gpu* 2>/dev/null
ls /scratch/jjyeung/orch_n30 2>/dev/null
echo ==sam3ck; ls -la /scratch/jjyeung/orch_cd/mdg_next/work/data/ 2>/dev/null | head; 
ls /scratch/jjyeung/k1 2>/dev/null
ls /data2/k6tk 2>/dev/null | head -3; ls -d /data2/k6tk 2>&1
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
