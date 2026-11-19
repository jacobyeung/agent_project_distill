W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep -E "tr10|tr11"
tail -c 1500 $W/w19/work/build19/STATUS.md; ls -la $W/w19/out | tail -3; free -g | sed -n 2p
T=$W/w18/work/tree_r1; wc -l $T/student_pilot/r2_policy.py; grep -n "evidence\|record\|manifest\|def \|SLOTS\|slot" $T/student_pilot/r2_policy.py | head -60 | cut -c1-220
ls -la /data3/jjyeung/distill_src_archive/ | head -20
