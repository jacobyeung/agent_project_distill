R=/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs
head -c 2500 $R/20261121T011611Z_lever3_r4closrev/final_message.md; echo; echo ==== procs
ps -eo pid,etime,args | grep -E "[c]odex.*(r1vpy|r4clos)|[c]odex exec" | cut -c1-200 | head; ps -eo pid,etime,args | grep -c "[c]odex"
stat -c '%y %s' $R/20261121T011052Z_lever3_r1vpy/transcript.log $R/20261121T011126Z_lever3_r1vpy/transcript.log
