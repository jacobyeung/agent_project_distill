R=/scratch/jjyeung/orch_n30; cd $R; date -u +%TZ; free -g | sed -n 2p; tail -2 sb_queue/codexq.log
for w in sb_ph2rev; do echo "== $w"; tmux has-session -t $w 2>/dev/null && echo alive || echo ended; find $w -newermt '-10 min' -type f 2>/dev/null | grep -v extract | head -2; ls $w/REVIEW_VERDICT.md 2>/dev/null; done
cat sb_cachk/STATUS.md 2>/dev/null | cut -c1-300; echo; cat sb_ktfix2/STATUS.md | cut -c1-300
