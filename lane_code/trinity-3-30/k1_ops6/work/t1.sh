hostname -s; date -u +%FT%TZ
echo "--- pgrep k1_ops5"; pgrep -u jjyeung -af briefs/k1_ops5.md | cut -c1-250
echo "--- pgrep devin/claude"; pgrep -u jjyeung -af 'devin|claude' | cut -c1-200 | head -20
echo "--- tmux"; tmux ls 2>&1
df -h /scratch | tail -1
W=/scratch/jjyeung/orch_n30/k1_ops3
if pgrep -u jjyeung -f briefs/k1_ops5.md >/dev/null; then echo "K1_OPS5_ALIVE"; exit 0; fi
echo "--- lane top"; ls -la --time-style=+%FT%T $W | head -50
echo "--- work"; ls -la --time-style=+%FT%T $W/work | tail -80
echo "--- build"; ls -la --time-style=+%FT%T $W/work/partb/build | head -80
echo "--- packet"; ls -la --time-style=+%FT%T $W/work/partb/build/packet | head -50
echo "--- ledger"; tail -5 $W/work/ORCHARD_LEDGER.jsonl | cut -c1-600
