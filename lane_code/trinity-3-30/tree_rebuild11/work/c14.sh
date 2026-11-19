cd /scratch/jjyeung/io_governor_serial || exit 1; date -u +%TZ; ls code | head -20; tail -3 logs/agent.log | cut -c1-200; tail -5 logs/agent.out 2>/dev/null | cut -c1-200
bash code/stop.sh agent-only 2>&1 | tail -5; sleep 5; tmux ls | grep iogov; pgrep -af node_agent | head -3
bash code/start_agent.sh 2>&1 | tail -5; sleep 40; tmux ls | grep iogov; pgrep -af node_agent | head -3; tail -5 logs/agent.log | cut -c1-200
