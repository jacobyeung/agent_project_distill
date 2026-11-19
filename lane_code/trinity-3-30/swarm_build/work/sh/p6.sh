R=/scratch/jjyeung/orch_n30; cd $R; date -u +%TZ; free -g | sed -n 2p
tail -2 sb_queue/codexq.log; cat sb_queue/queue.txt | tr "\n" " "; echo
echo "cafix:"; ls -la --time-style=+%H:%M sb_cafix/out/ | tail -4; find sb_cafix -newermt '-10 min' -type f | head -3; tail -c 200 sb_cafix/cursor.log
echo "ktchk:"; ls --time-style=+%H:%M -la sb_ktchk | tail -4; find sb_ktchk -newermt '-10 min' -type f | grep -v extract | head -3; tail -c 300 sb_ktchk/cursor.log
echo "ph2fix:"; cat sb_ph2fix/STATUS.md 2>/dev/null | cut -c1-300
awk -F'|' '{s+=$6; n++} END {print n, s}' $R/codex_local/agent/scratch/codex_runs/CODEX_SPEND.log
