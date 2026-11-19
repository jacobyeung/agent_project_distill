R=/scratch/jjyeung/orch_n30
date -u +%TZ; tmux ls -F "#{session_name}" | grep "^sb_" | tr "\n" " "; echo; tail -2 $R/sb_queue/codexq.log
for t in sb_ktrev2 sb_mask_phrase sb_mask_carry sb_cachefix sb_f64fix3; do echo "== $t log=$(wc -c < $R/$t/cursor.log) $(head -c 250 $R/$t/STATUS.md 2>/dev/null)"; done
ls $R/sb_ktrev2/out; head -c 300 $R/sb_mdrev2/STATUS.md
