W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; F=$W/w24/work/build24f
date -u +%TZ
ls -la $F | head -60
for f in rehearsal_run4.log rehearsal_run5.log; do echo "@@@ $f $(stat -c %s $F/$f) $(sha256sum < $F/$f | cut -c1-64)"; head -c 6000 $F/$f; echo; echo ...; tail -c 5000 $F/$f; done
