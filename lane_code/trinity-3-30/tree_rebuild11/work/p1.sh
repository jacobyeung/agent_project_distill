W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep -E "tr10|tr11|iogov"
tail -c 1500 $W/w19/work/build19/STATUS.md 2>&1; ls -la $W/w19/out 2>&1 | tail -5; tail -5 $W/work/build19_dispatch.log
free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1; du -sh $W 2>/dev/null
