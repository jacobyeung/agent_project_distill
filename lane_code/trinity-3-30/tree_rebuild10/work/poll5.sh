W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr10; tail -c 600 $W/w15/work/build15/STATUS.md; ls $W/w15/out | grep -i 15
C=/scratch/jjyeung/n30_mirror/rows_r2/work/chk; grep -nE "/scratch|/data|4d4736cf|bdb5d402|634820b4|969cdb56" $C/drop_k1.py $C/excl_check.py | cut -c1-300 | head -20
for p in $(grep -hoE "/(scratch|data[0-9]?)/[A-Za-z0-9_./-]+" $C/drop_k1.py $C/excl_check.py | sort -u); do [ -e $p ] && echo "OK $p" || echo "MISSING $p"; done
