S=/dev/shm/jjyeung/b11_presence
cat > $S/lane/code/debug_parity.py
used=$(nvidia-smi -i 5 --query-gpu=memory.used --format=csv,noheader,nounits); [ "$used" -lt 100 ] || { echo BUSY; exit 5; }
C=$S/cache
$S/bw.sh bash -c "cd /scratch/jjyeung/orch_n30/b11_presence && export CUDA_VISIBLE_DEVICES=5 XDG_CACHE_HOME=$C/.cache HF_HOME=$C/hf TRITON_CACHE_DIR=$C/.triton VLLM_CACHE_ROOT=$C/.cache/vllm HF_HUB_OFFLINE=1 VLLM_USE_FLASHINFER_SAMPLER=0 && timeout 600 /data3/shared/scripts/vnice/vnice.sh /scratch/jjyeung/envs/vllm/bin/python -I code/debug_parity.py > work/logs/debug_parity.log 2>&1"
grep -E '^(LEN|EXP|OBS)' $S/lane/work/logs/debug_parity.log | cut -c1-1600; tail -3 $S/lane/work/logs/debug_parity.log | cut -c1-300
