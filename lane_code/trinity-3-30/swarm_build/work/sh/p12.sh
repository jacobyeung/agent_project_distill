R=/scratch/jjyeung/orch_n30; W=$R/tree_rebuild10_w; cd $R; date -u +%TZ
cat $W/w21/out/BUILD21H_REPORT.md
ls $W/w21/out | head -40
cat sb_ph2fix/out/PH2FIX2_REPORT.md 2>/dev/null; cat sb_ph2fix/out/sb_ph2fix2.tar.sha256 2>/dev/null
tmux has-session -t sb_ktchk2 2>/dev/null && echo ktchk2 alive || echo ktchk2 ended
