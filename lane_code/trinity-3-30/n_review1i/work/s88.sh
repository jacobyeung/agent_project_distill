W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; J=$W/w24z15/work/build24m4z15/j.sh
date -u +%TZ
grep -n "bind\|n_root\|okh7\|x_22c714e1\|live" $J < /dev/null | cut -c1-300 | head -40
grep -n "bind\|live\|ev" $W/w24z12/out/jd7.sh < /dev/null | cut -c1-250 | head -20
