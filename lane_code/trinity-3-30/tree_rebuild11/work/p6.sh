W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep -E "tr11|iogov"
tail -c 800 $W/w20/work/build20/STATUS.md 2>&1; free -g | sed -n 2p
echo ---agent; ls -la /scratch/jjyeung/io_governor_serial/ 2>&1 | head; tail -20 /scratch/jjyeung/io_governor_serial/logs/agent.log 2>&1 | cut -c1-250; ls /scratch/jjyeung/io_governor/ 2>&1 | head
pgrep -af node_agent | head -3
