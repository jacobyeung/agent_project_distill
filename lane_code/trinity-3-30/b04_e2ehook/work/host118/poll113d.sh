L=/dev/shm/jjyeung/b04/host/b04_e2ehook; R=$L/parity_kit/host_results/cpu_first_c
grep -v "Warning\|warn" $L/work/first_c.log | tail -c 1500; echo; tmux ls 2>/dev/null | grep b04
ps -o pid,etime,rss,pcpu,cmd -u jjyeung | grep -E "parity_kit" | grep -v grep | cut -c1-140; ls $R; wc -l $R/items.jsonl
