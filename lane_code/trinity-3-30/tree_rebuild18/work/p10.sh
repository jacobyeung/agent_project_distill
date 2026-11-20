W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; T=$W/w24c/work/tree_r1; date -u +%TZ
sha256sum $T/student_pilot/s1_routing.py $T/student_pilot/routing.py | cut -c1-80
timeout 60 nice -n 10 find $W -maxdepth 6 \( -name '*947cbb9f*' -o -name '*0c38bc96*' -o -name 'ROUTE_DIRECT*' -o -name '*ca0616db*' \) -size +0 2>/dev/null | head -20
grep -l "0c38bc96\|947cbb9f" $W/work/pin_eac5f9f0/ORCHARD_U_LIST.txt $W/work/pin_eac5f9f0/P_SHA256SUMS.txt 2>/dev/null; grep "0c38bc96\|947cbb9f" $W/work/pin_eac5f9f0/*.txt | head
