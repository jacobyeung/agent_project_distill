set -u
CARD=${CARD:-5}
S=/dev/shm/jjyeung/b11_presence
date -u +%FT%TZ; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
used=$(nvidia-smi -i $CARD --query-gpu=memory.used --format=csv,noheader,nounits)
[ "$used" -lt 100 ] || { echo "CARD BUSY $used"; exit 5; }
C=$S/cache
tmux new-session -d -s b11direct "$S/bw.sh bash -c 'cd /scratch/jjyeung/orch_n30/b11_presence && export CUDA_VISIBLE_DEVICES=$CARD XDG_CACHE_HOME=$C/.cache HF_HOME=$C/hf TRITON_CACHE_DIR=$C/.triton VLLM_CACHE_ROOT=$C/.cache/vllm HF_HUB_OFFLINE=1 VLLM_USE_FLASHINFER_SAMPLER=0 && /data3/shared/scripts/vnice/vnice.sh /scratch/jjyeung/envs/vllm/bin/python -I code/direct.py read --out out/direct >> work/logs/direct_card5.log 2>&1; echo EXIT=\$? >> work/logs/direct_card5.log'"
sleep 30; tmux ls | grep b11; tail -3 $S/lane/work/logs/direct_card5.log
