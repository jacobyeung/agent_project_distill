R=/scratch/jjyeung/orch_n30
date -u +%TZ; uptime
cat $R/sb_queue/codexq2.sh
# renice every process tree under my sb_* tmux sessions (not sb_codexq loop itself is fine too)
for s in $(tmux ls -F '#{session_name}' | grep '^sb_'); do
  for p in $(tmux list-panes -t "$s" -F '#{pane_pid}'); do
    all="$p $(pgrep -P $p) "; for c in $(pgrep -P $p); do all="$all $(pgrep -P $c)"; for g in $(pgrep -P $c); do all="$all $(pgrep -P $g)"; for h in $(pgrep -P $g); do all="$all $(pgrep -P $h)"; done; done; done
    renice -n 10 -p $all >/dev/null 2>&1; echo "$s: $(echo $all | wc -w) procs reniced"
  done
done
ps -u jjyeung -o ni,pcpu,rss,args --sort=-pcpu | head -15 | cut -c1-150
