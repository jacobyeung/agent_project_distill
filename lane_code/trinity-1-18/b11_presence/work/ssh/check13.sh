hostname -s; date -u +%T
df -h /dev/shm /scratch | tail -2; free -g | head -2
du -sh /dev/shm/jjyeung/* 2>/dev/null
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader | head
which bwrap; bwrap --version
mkdir -p /dev/shm/jjyeung/b11_presence /dev/shm/jjyeung/exports
bwrap --dev-bind / / --bind /dev/shm/jjyeung/b11_presence /tmp/b11test true 2>&1 | head -2; mkdir -p /tmp/b11t && bwrap --dev-bind / / --bind /dev/shm/jjyeung/b11_presence /tmp/b11t ls /tmp/b11t && echo BWRAP_OK
ls -d /scratch/jjyeung/envs/vllm /scratch/jjyeung/orch_n30 2>&1
tmux ls 2>&1 | head
