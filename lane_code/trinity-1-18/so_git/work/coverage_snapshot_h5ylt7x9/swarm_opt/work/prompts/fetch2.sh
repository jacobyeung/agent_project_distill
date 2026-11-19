cd /scratch/jjyeung/orch_n30 && tar cf - so_step/out/REPORT.md so_step/work/STATUS.md so_rv_read 2>/dev/null --exclude='*.log' | base64 -w0; echo
R=$(ls -d /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/*_so_rv_read | tail -1); cp $R/final_message.md /scratch/jjyeung/orch_n30/so_rv_read/REVIEW_VERDICT.md
