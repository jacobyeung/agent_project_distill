R=/scratch/jjyeung/orch_n30; cd $R; date -u +%TZ; free -g | sed -n 2p
tail -3 sb_queue/codexq.log; cat sb_queue/queue.txt | tr "\n" " "; echo
find sb_cafix -newermt '2026-11-19 11:32:30Z' -type f 2>/dev/null | head -5; cat sb_cafix/cursor.log | tail -c 300; pgrep -f 'claude-opus-5-5-xhigh Read PROMPT.md' | head -2
cat sb_ktfix2/STATUS.md | cut -c1-400; cat sb_ph2gate/STATUS.md 2>/dev/null | cut -c1-400
ps -o pid,etime,rss,cmd -u jjyeung | grep -E 'a0_rerun|codex exec' | grep -v grep | cut -c1-150 | head
