R=/scratch/jjyeung/orch_n30
date -u +%TZ; cat $R/sb_queue/queue.txt | tr "\n" " "; echo; tail -2 $R/sb_queue/codexq.log
pgrep -f "codex_dispatch.sh implement $R/sb_" -a | grep -o "label [a-zA-Z0-9_]*" | sort -u | tr "\n" " "; echo
for s in sb_rkrev sb_rlrev2; do echo "$s log=$(wc -c < $R/$s/cursor.log) verdict=$(ls $R/$s/REVIEW_VERDICT.md 2>/dev/null)"; done
for t in sb_kbox3 sb_ktow2 sb_kobj2 sb_rowD7 sb_f64rev; do d=$(ls -d $R/codex_local/agent/scratch/codex_runs/*_$t 2>/dev/null | tail -1); echo "== $t"; [ -f $d/final_message.md ] && head -c 1000 $d/final_message.md; echo; head -c 400 $R/$t/STATUS.md 2>/dev/null; echo; done
grep -n -i "out of view\|in view in frame\|not visible" $R/sb_rowB4/out/READ30.md | head -5 | cut -c1-300
