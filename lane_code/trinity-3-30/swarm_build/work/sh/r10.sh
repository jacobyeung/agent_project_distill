R=/scratch/jjyeung/orch_n30
head -25 $R/sb_crrev2/REVIEW_VERDICT.md
for t in sb_rowT sb_rowB2 sb_rowD2; do echo "== $t"; d=$(ls -d $R/codex_local/agent/scratch/codex_runs/*_$t | tail -1); head -c 900 $d/final_message.md; echo; done
