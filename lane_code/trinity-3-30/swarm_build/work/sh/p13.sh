R=/scratch/jjyeung/orch_n30; cd $R; date -u +%TZ; free -g | sed -n 2p; tail -2 sb_queue/codexq.log
for w in sb_ktchk2 sb_ph2chk; do tmux has-session -t $w 2>/dev/null && echo "$w alive" || echo "$w ended"; ls $w/REVIEW_VERDICT.md 2>/dev/null; find $w -newermt '-10 min' -type f 2>/dev/null | grep -v -E 'extract|tmp' | wc -l; done
for w in sb_fullinv sb_fhalias; do echo "$w: $(cat $w/STATUS.md 2>/dev/null | cut -c1-250)"; done
