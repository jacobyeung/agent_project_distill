R=/scratch/jjyeung/orch_n30
date -u +%TZ; free -g | sed -n 2p; tmux ls -F "#{session_name}" | tr "\n" " "; echo
echo cap=$(cat $R/sb_queue/cap); tail -6 $R/sb_queue/codexq.log; echo Q: $(cat $R/sb_queue/queue.txt | tr "\n" " ")
for t in sb_maskfail sb_ktrev sb_rkdocs sb_nonnull sb_rlfix2s sb_f64rev2 sb_cntfix; do echo "== $t"; ls $R/$t/out 2>/dev/null | tr "\n" " "; ls $R/$t 2>/dev/null | tr "\n" " "; echo; head -c 400 $R/$t/STATUS.md 2>/dev/null; echo; done
wc -c $R/sb_ktrev/cursor.log; head -c 3500 $R/sb_ktrev/REVIEW_VERDICT.md 2>/dev/null
head -c 3000 $R/sb_maskfail/out/FIRST_TABLE.md 2>/dev/null
wc -l $R/codex_local/CODEX_SPEND.log 2>/dev/null || ls $R/codex_local
