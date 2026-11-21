W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24z12/out/kit_n_go
date -u +%TZ
grep -n "check('" $W/w24z14/out/admit_test.py < /dev/null | cut -c1-200
grep -n 'def finish' -A 25 $W/w24z14/out/admit_test.py < /dev/null | cut -c1-200
grep -n 'def encoded' -A 6 $K/b/rv.py < /dev/null; grep -n 'def location' -A 14 $K/b/rv.py < /dev/null
ls -la $W/work/d173881/173881/live < /dev/null
ls $W/work < /dev/null | tr '\n' ' '; echo
for d in $W/work/d173661 $W/work/d173626 $W/work/d173912/173912; do ls $d < /dev/null 2>&1 | head -30; done
ls $W/w24z14/work/build24m4z14 < /dev/null | head -30
