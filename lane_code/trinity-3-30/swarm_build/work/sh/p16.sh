R=/scratch/jjyeung/orch_n30; cd $R; date -u +%TZ; free -g | sed -n 2p; tail -3 sb_queue/codexq.log; cat sb_queue/queue.txt | tr "\n" " "; echo
for w in sb_ktfix2 sb_fhalias sb_fullinv sb_ph2fix; do echo "$w: $(cat $w/STATUS.md 2>/dev/null | cut -c1-200)"; done
ls sb_ktfix2/out/FIX4_REPORT.md sb_ktfix2/out/sb_ktfix4.tar.sha256 2>/dev/null
