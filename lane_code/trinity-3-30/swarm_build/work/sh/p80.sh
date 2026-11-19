R=/scratch/jjyeung/orch_n30
date -u +%TZ; tmux ls -F "#{session_name}" | grep "^sb_" | tr "\n" " "; echo; tail -2 $R/sb_queue/codexq.log; echo Q: $(cat $R/sb_queue/queue.txt | tr "\n" " ")
for t in sb_phrev sb_carev sb_cfrev sb_k1012 sb_rlfix4 sb_ktfix2; do echo "== $t $(head -c 250 $R/$t/STATUS.md 2>/dev/null)"; ls $R/$t/REVIEW_VERDICT.md 2>/dev/null; done
