R=/scratch/jjyeung/orch_n30
date -u +%TZ; tail -3 $R/sb_queue/codexq.log; echo Q: $(cat $R/sb_queue/queue.txt | tr "\n" " ")
echo ===RL; cat $R/sb_rlfix3/out/FIX3_REPORT.md 2>/dev/null | head -60; cat $R/sb_rlfix3/out/sb_rlfix3.tar.sha256 2>/dev/null; wc -c $R/sb_rlfix3/cursor.log
echo ===F64; cat $R/sb_f64rev3/REVIEW_VERDICT.md $R/sb_f64rev3/out/REVIEW_VERDICT.md 2>/dev/null | head -35
echo ===MF; head -c 1500 $R/sb_mffix/out/FIX_NOTES.md; cat $R/sb_mffix/out/sb_mffix.tar.sha256
