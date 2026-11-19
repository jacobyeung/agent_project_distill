W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ
cat $W/w24/out/PRODUCTION_BLOCKERS.md
K=$W/w24/out/kit_n_go; sed -n 1,60p $K/b/a.py </dev/null | cut -c1-230
python3 -B /tmp/tr14_dec.py $K/k/h.json missing,proof,request,binaries </dev/null | cut -c1-400 | head
