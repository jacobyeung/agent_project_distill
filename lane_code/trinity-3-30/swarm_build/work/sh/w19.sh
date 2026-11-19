R=/scratch/jjyeung/orch_n30
date -u +%TZ; cat $R/sb_queue/queue.txt | tr "\n" " "; echo; tail -2 $R/sb_queue/codexq.log
pgrep -f "codex_dispatch.sh implement $R/sb_" -a | grep -o "label [a-zA-Z0-9_]*" | sort -u | tr "\n" " "; echo
for s in sb_drev6 sb_brev4 sb_pfrev sb_rkrev sb_rlrev2 sb_f64; do echo "$s log=$(wc -c < $R/$s/cursor.log) verdict=$(ls $R/$s/REVIEW_VERDICT.md 2>/dev/null)"; done
for f in sb_pfrev/REVIEW_VERDICT.md sb_drev6/REVIEW_VERDICT.md sb_brev4/REVIEW_VERDICT.md sb_rkrev/REVIEW_VERDICT.md; do [ -f $R/$f ] && { echo "=================== $f"; cat $R/$f; }; done
