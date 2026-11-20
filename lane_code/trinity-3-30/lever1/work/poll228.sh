C=/scratch/jjyeung/orch_n30/lever1_c; R=/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs
tmux ls 2>/dev/null | grep l1_ | cut -c1-40; for f in $C/r*_run.log; do tail -1 $f | sed "s#^#$(basename $f): #"; done
echo "-- nogt $(tail -1 $C/nogt/stage.log 2>/dev/null) $(du -s --block-size=1M $C/nogt/raw | cut -f1) MB"
for d in $(ls -td $R/*lever1_* 2>/dev/null | head -4); do echo "== $(basename $d) $(stat -c %s $d/transcript.log) final=$([ -f $d/final_message.md ] && echo y || echo n)"; grep -v WARN $d/transcript.log | tail -c 500 | tr -d '\r'; echo; done
uptime
