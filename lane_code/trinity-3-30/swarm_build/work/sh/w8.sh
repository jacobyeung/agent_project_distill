R=/scratch/jjyeung/orch_n30
for f in sb_harev/out/REVIEW_VERDICT.md sb_brev3/REVIEW_VERDICT.md sb_afrev/REVIEW_VERDICT.md sb_recrev/REVIEW_VERDICT.md sb_rowD5/out/REPORT.md sb_regenscope/out/REGEN_SCOPE.md; do echo "=================== $f"; cat $R/$f; done
