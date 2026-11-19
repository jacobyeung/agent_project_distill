R=/scratch/jjyeung/orch_n30; cd $R; date -u +%TZ; free -g | sed -n 2p; tail -2 sb_queue/codexq.log
tmux has-session -t sb_ph2rev 2>/dev/null && echo ph2rev alive || echo ph2rev ended; ls sb_ph2rev/REVIEW_VERDICT.md 2>/dev/null
pgrep -af 'label sb_cachk' | head -1 | cut -c1-80; echo "@@FILE CACHK_VERDICT.md"; cat sb_cachk/out/CACHK_VERDICT.md 2>/dev/null; cat sb_cachk/out/sb_cachk.tar.sha256 2>/dev/null
echo "@@FILE ktfix2_STATUS.txt"; cat sb_ktfix2/STATUS.md | cut -c1-400
