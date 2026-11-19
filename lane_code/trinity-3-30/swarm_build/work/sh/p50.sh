R=/scratch/jjyeung/orch_n30
date -u +%TZ; tail -c 1500 $R/sb_ktrev/cursor.log; echo; echo ====V; cat $R/sb_ktrev/REVIEW_VERDICT.md 2>/dev/null || ls $R/sb_ktrev $R/sb_ktrev/work
echo ====RL; ls $R/sb_rlfix2/out | tr "\n" " "; echo; head -c 900 $R/sb_rlfix2/STATUS.md; echo; ls $R/sb_rlfix2/out/*.md 2>/dev/null
tail -3 $R/sb_queue/codexq.log
