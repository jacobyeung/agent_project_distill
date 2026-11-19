R=/scratch/jjyeung/orch_n30
date -u +%TZ; free -g | sed -n 2p; tmux ls -F "#{session_name}" | grep ^sb_ | tr "\n" " "; echo
tail -3 $R/sb_queue/codexq.log; echo Q: $(cat $R/sb_queue/queue.txt | tr "\n" " ")
for t in sb_maskfail sb_rkdocs sb_nonnull; do echo "== $t"; ls $R/$t/out 2>/dev/null | tr "\n" " "; echo; head -c 500 $R/$t/STATUS.md 2>/dev/null; echo; done
wc -c $R/sb_ktrev/cursor.log; ls -la $R/sb_ktrev | tail -4; ls -t $R/sb_ktrev/work 2>/dev/null | head -5
ls $R/codex_local/agent/scratch/ 2>/dev/null; ls $R/codex_local/agent/scratch/codex_runs 2>/dev/null | tail -2; ls $R/codex_local/agent/scratch/codex_runs/*SPEND* $R/codex_local/*SPEND* 2>/dev/null
