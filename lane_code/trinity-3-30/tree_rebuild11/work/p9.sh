W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep -E "tr11"; tail -c 400 $W/w21/work/build21/STATUS.md 2>&1; echo; du -sh $W/w21 2>/dev/null; free -g | sed -n 2p
