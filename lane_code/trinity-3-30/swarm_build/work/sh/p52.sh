R=/scratch/jjyeung/orch_n30
cd $R; ls -la sb_maskfail/out/sb_maskfail.tar sb_rkdocs/out/sb_rkdocs.tar sb_rlfix2/out/sb_rlfix2.tar | awk '{print $5, $9}' >&2
tar cf - sb_maskfail/out/MASKFAIL_REPORT.md sb_maskfail/out/SPLITS.md sb_maskfail/RULES.md sb_maskfail/out/ATTRIBUTION.json sb_maskfail/out/sb_maskfail.tar.sha256 sb_nonnull/out/NONNULL_NOTE.md sb_nonnull/out/COUNTS.txt sb_ktrev/REVIEW_VERDICT.md sb_rkdocs/out/DOCS_FIX.md sb_rkdocs/out/GPU_NEED.json sb_rkdocs/out/ROOMKIT_REPORT.md sb_rkdocs/out/sb_rkdocs.tar.sha256 sb_rlfix2/out/REPORT.md sb_rlfix2/out/SHA256SUMS
