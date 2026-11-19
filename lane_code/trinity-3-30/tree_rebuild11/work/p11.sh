W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild21 | head -1); ls -la --time-style=+%TZ $d/transcript.log; tail -c 2500 $d/transcript.log | tr -cd '[:print:]\n' | grep -v "^\s*$" | tail -12 | cut -c1-220
P=$(tmux list-panes -t tr11_b21 -F '#{pane_pid}'); t(){ echo $1; for c in $(pgrep -P $1); do t $c; done; }; ps -o pid,ni,etime,pcpu,rss,args -p $(t $P | sort -u | tr '\n' ',' | sed 's/,$//') | sort -k4 -nr | head -5 | cut -c1-220
