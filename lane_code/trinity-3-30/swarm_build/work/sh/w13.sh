R=/scratch/jjyeung/orch_n30
for f in sb_arev2/REVIEW_VERDICT.md sb_fprev/REVIEW_VERDICT.md sb_rlrev/REVIEW_VERDICT.md; do echo "=================== $f"; cat $R/$f; done
for t in sb_kbox sb_auditfix2; do d=$(ls -d $R/codex_local/agent/scratch/codex_runs/*_$t | tail -1); echo "=================== $t"; cat $d/final_message.md 2>/dev/null | head -c 2500; echo; tail -c 600 $R/$t/dispatch_$t.log; done
echo ==f64; tail -c 300 $R/sb_f64/cursor.log
