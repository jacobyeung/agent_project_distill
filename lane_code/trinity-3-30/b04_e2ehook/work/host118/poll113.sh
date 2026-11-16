L=/dev/shm/jjyeung/b04/host/b04_e2ehook
tail -2 $L/work/restore.log | cut -c1-300; tail -2 $L/work/manifest.log | cut -c1-300; grep -v "Warning\|warn" $L/work/first.log | tail -c 1500; echo; tmux ls 2>/dev/null | grep b04
ps -o pid,etime,rss,pcpu,cmd -u jjyeung | grep -E "parity_kit" | grep -v grep | cut -c1-140; ls $L/parity_kit/host_results/cpu_first 2>&1 | head; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
