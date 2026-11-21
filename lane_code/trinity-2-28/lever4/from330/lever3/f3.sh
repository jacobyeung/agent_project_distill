R=/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs; C=/scratch/jjyeung/orch_n30/lever1_c
tail -2 $C/r1vpy_run.log $C/r1vpyrev_run.log 2>&1 | cut -c1-200
for d in $R/20261121T011126Z_lever3_r1vpy $(ls -d $R/*lever3_r1vpyrev 2>/dev/null); do echo "== $d"; cat $d/final_message.md 2>/dev/null | head -c 3000; echo; done
