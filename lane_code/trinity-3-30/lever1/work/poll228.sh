C=/scratch/jjyeung/orch_n30/lever1_c; R=/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs
tmux ls 2>/dev/null | grep l1_; for f in $C/r3_run.log $C/r2c_run.log $C/r1_run.log $C/r5_run.log $C/r6_run.log; do [ -f $f ] && { echo "-- $f"; cat $f; }; done
echo "-- arch"; tail -2 $C/arch/arch_run.log; head -c 400 $C/arch/COPY_RECEIPT.json; echo
echo "-- nogt"; tail -2 $C/nogt/stage.log; du -s --block-size=1M $C/nogt/raw
ls $C/r3/out $C/r2/out 2>/dev/null | head
for d in $(ls -td $R/*lever1_* 2>/dev/null | head -3); do echo "== $d $(stat -c %s $d/transcript.log)"; ls $d | tr '\n' ' '; echo; tail -c 300 $d/transcript.log | tr -d '\r' | grep -v WARN; echo; done
uptime
