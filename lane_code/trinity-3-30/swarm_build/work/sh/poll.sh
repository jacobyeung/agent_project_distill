R=/scratch/jjyeung/orch_n30; date -u +%TZ; free -g | sed -n 2p; df -h /scratch | tail -1; tmux ls | cut -c1-20 | tr "\n" " "; echo
for t in sb_alias2 sb_callrate sb_rlkit sb_evrev sb_f64 sb_ownread; do echo "== $t"; head -c 500 $R/$t/STATUS.md 2>/dev/null | tail -c 400; echo; ls $R/$t/out 2>/dev/null | tr "\n" " "; echo; done
for f in $R/sb_alias2/dispatch.log $R/sb_callrate/dispatch2.log $R/sb_rlkit/dispatch.log; do echo "-- $f"; tail -c 400 $f; done
for f in $R/sb_evrev/cursor.log $R/sb_f64/cursor.log $R/sb_ownread/cursor.log; do echo "-- $f $(stat -c %s $f)"; tail -c 300 $f; done
pgrep -f "agent -p" | wc -l
