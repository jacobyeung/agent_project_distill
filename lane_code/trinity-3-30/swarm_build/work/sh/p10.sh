R=/scratch/jjyeung/orch_n30; cd $R; date -u +%TZ; free -g | sed -n 2p; tail -2 sb_queue/codexq.log
tmux has-session -t sb_ktchk2 2>/dev/null && echo ktchk2 alive || echo ktchk2 ended; ls sb_ktchk2/REVIEW_VERDICT.md 2>/dev/null; find sb_ktchk2 -newermt '-10 min' -type f 2>/dev/null | grep -v -E 'extract|tmp' | head -2
cat sb_ph2fix/STATUS.md | cut -c1-300
