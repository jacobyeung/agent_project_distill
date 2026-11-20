W=/scratch/jjyeung/orch_n30/lever1_c/nogt; cat $W/stage.log; cat $W/STREAM_src.sha; find $W/raw -type f | wc -l; du -sb $W/raw | cut -f1
R=/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs; d=$(ls -d $R/*lever1_r3); stat -c %s $d/transcript.log; grep -v WARN $d/transcript.log | tail -c 700
