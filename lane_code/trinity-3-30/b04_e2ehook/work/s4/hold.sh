L=/dev/shm/jjyeung/b04/host2/b04_e2ehook
touch $L/work/HOLD; tmux kill-session -t b04_chain 2>&1; echo "$(date -u +%FT%TZ) HOLD + chain killed by lane (p0 ended early at $(wc -l < $L/parity_kit/gpu_results/own_depth_p0/items.jsonl))" >> $L/work/gpu_launch.log
tail -6 $L/work/gpu_launch.log; tmux ls | grep b04_
pgrep -af run_parity | cut -c1-150
tail -c 3000 $L/work/gpu_own_depth_p0.log | grep -v '^{"key'
ls -la /tmp/terminator/ 2>/dev/null | grep jjyeung | head; ls /data3/shared/scripts/vnice/ ; 
nvidia-smi -i 3 --query-gpu=memory.used --format=csv,noheader
