R=/scratch/jjyeung/orch_n30; cd $R; date -u +%TZ; free -g | sed -n 2p
for w in sb_cafix sb_ktchk sb_ph2rev; do echo "== $w"; tmux has-session -t $w 2>/dev/null && echo alive || echo ended; find $w -newermt '-10 min' -type f 2>/dev/null | grep -v extract | head -2; tail -c 400 $w/cursor.log; ls $w/REVIEW_VERDICT.md $w/out/sb_cafix.tar.sha256 2>/dev/null; done
