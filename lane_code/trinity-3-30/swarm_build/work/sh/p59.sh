R=/scratch/jjyeung/orch_n30
cat $R/sb_mdrev/REVIEW_VERDICT.md 2>/dev/null || cat $R/sb_mdrev/out/REVIEW_VERDICT.md; echo =====F64; cat $R/sb_f64fix2/out/FIX2_REPORT.md; cat $R/sb_f64fix2/out/sb_f64fix2.tar.sha256
