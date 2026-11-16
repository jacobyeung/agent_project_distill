L=/dev/shm/jjyeung/b04/host/b04_e2ehook
tail -2 $L/work/manifest_b.log | cut -c1-200; grep -v "Warning\|warn" $L/work/first_b.log | tail -c 1500; echo; tmux ls 2>/dev/null | grep b04
ps -o pid,etime,rss,pcpu,cmd -u jjyeung | grep -E "parity_kit" | grep -v grep | cut -c1-140; ls $L/parity_kit/host_results/cpu_first_b 2>&1 | head -20
ls /dev/shm/jjyeung/b05/stage | grep -v '^[0-9a-f][0-9a-f]$'; timeout 30 find /dev/shm/jjyeung/b05/stage/sam3src /dev/shm/jjyeung/b05/cache /dev/shm/jjyeung/b05/lane -maxdepth 3 \( -name '*.pt' -o -name '*.safetensors' -o -iname '*RECEIPT*.json' \) 2>/dev/null | head
