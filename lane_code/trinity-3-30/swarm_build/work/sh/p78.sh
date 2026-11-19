R=/scratch/jjyeung/orch_n30
date -u +%TZ; tmux ls -F "#{session_name}" | grep "^sb_" | tr "\n" " "; echo; tail -3 $R/sb_queue/codexq.log
cat $R/sb_rlrev4/REVIEW_VERDICT.md 2>/dev/null || cat $R/sb_rlrev4/out/REVIEW_VERDICT.md
echo ===KT; cat $R/sb_ktrev2/REVIEW_VERDICT.md 2>/dev/null | head -40
