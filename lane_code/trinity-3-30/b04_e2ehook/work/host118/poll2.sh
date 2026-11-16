L=/scratch/jjyeung/orch_n30/b04host/b04_e2ehook
tail -2 $L/work/manifest2.log; tail -c 1200 $L/work/first2.log; echo; cat $L/work/stage113.log; tmux ls 2>/dev/null | grep b04
ps -o pid,etime,rss,pcpu,cmd -u jjyeung | grep -E "parity_kit" | grep -v grep | cut -c1-140; ls $L/parity_kit/host_results/cpu_first2 2>&1
