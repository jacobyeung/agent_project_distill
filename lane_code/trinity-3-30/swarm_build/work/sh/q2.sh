set -u
R=/scratch/jjyeung/orch_n30
grep -v -x -e sb_framepool -e sb_rspecrev -e sb_rowF $R/sb_queue/queue.txt > $R/sb_queue/q.tmp; cat $R/sb_queue/q.tmp > $R/sb_queue/queue.txt
cat $R/sb_queue/queue.txt; tail -2 $R/sb_queue/codexq.log
for t in sb_owrev sb_rowB2 sb_rowD2 sb_rowT sb_rarev; do echo "== $t"; ls $R/$t/out 2>/dev/null | head -5; done; head -30 $R/sb_owrev/REVIEW_VERDICT.md; head -30 $R/sb_rarev/REVIEW_VERDICT.md
