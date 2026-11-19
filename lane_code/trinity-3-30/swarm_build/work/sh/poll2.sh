R=/scratch/jjyeung/orch_n30
date -u +%TZ; free -g | sed -n 2p; tmux ls | cut -c1-14 | tr "\n" " "; echo; tail -4 $R/sb_queue/codexq.log; cat $R/sb_queue/queue.txt | tr "\n" " "; echo
for t in sb_framepool sb_rspecrev sb_records; do echo "== $t"; head -c 600 $R/$t/STATUS.md; echo; done; head -15 $R/sb_framepool/out/FRAMEPOOL_REPORT.md 2>/dev/null; head -40 $R/sb_rspecrev/REVIEW_VERDICT.md 2>/dev/null
