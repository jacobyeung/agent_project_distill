R=/scratch/jjyeung/orch_n30
for f in sb_mfrev/REVIEW_VERDICT.md sb_rlrev3/REVIEW_VERDICT.md sb_f64rev2/out/REVIEW_VERDICT.md sb_cntfix/out/FIX_REPORT.md; do echo "=================== $f"; cat $R/$f; done; cat $R/sb_cntfix/out/sb_cntfix.tar.sha256; head -c 800 $R/sb_cntfix/out/GPU_NEED.json
