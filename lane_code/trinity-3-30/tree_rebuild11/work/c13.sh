date -u +%TZ; P=$(tmux list-panes -t tr11_b21 -F '#{pane_pid}')
t(){ echo $1; for c in $(pgrep -P $1); do t $c; done; }
L=$(t $P | sort -u | tr '\n' ' '); renice -n 10 -p $L >/dev/null 2>&1; ps -o pid,ni,pcpu,rss,comm -p $(echo $L | tr ' ' ',') | sort -k3 -nr | head -8
