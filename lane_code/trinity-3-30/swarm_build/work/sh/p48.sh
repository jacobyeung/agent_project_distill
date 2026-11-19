R=/scratch/jjyeung/orch_n30
cat $R/sb_ktrev/cursor.log; echo; echo =====MF; cat $R/sb_maskfail/out/MASKFAIL_REPORT.md; cat $R/sb_maskfail/out/sb_maskfail.tar.sha256
echo =====NN; cat $R/sb_nonnull/out/NONNULL_NOTE.md
echo =====RK; head -c 2500 $R/sb_rkdocs/out/DOCS_FIX.md; echo; cat $R/sb_rkdocs/out/sb_rkdocs.tar.sha256; head -c 1500 $R/sb_rkdocs/out/GPU_NEED.json
echo; awk -F'\t' 'END{print NR}' $R/codex_local/agent/scratch/codex_runs/CODEX_SPEND.log; tail -2 $R/codex_local/agent/scratch/codex_runs/CODEX_SPEND.log
