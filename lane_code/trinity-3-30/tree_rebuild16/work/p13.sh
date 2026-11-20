W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24/out/kit_qd; date -u +%TZ; grep -n "listing\|add_argument\|'h'\|\"h\"\|/'h'\|k/0\|'0.json'" $K/b/resolve.py $K/b/z.py $K/b/a.py $K/b/pl.py | head -40 | cut -c1-260
grep -n "jd.sh\|listing" $W/w24/work/build24m2c/DISCOVERY_SHELL_TESTS.json 2>/dev/null | head -5 | cut -c1-300; ls $W/w24/work/build24m2c | head -40
