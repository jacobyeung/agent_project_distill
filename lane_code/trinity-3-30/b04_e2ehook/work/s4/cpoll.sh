L=/dev/shm/jjyeung/b04/host2/b04_e2ehook; G=$L/parity_kit/gpu_results
tail -3 $L/work/gpu_launch.log; tmux ls 2>&1 | grep b04_ | cut -d: -f1 | tr '\n' ' '; echo
for p in 0 1 2; do f=$G/own_depth_p$p/items.jsonl; [ -f $f ] && echo "p$p $(wc -l < $f)"; done
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | tr '\n' ';'; echo
grep -i "error\|traceback" $L/work/gpu_own_depth_p*.log | grep -v -i warn | tail -3
