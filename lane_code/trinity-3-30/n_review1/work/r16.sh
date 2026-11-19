W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; M=/scratch/jjyeung/orch_n30/n_review; T=$W/w24/work/tree_r1; K=$W/w24/out/kit_n_go
echo "== identity hidden view"
nice -n 10 bwrap --ro-bind / / --tmpfs /home --tmpfs /data --tmpfs /data2 --tmpfs /data3 --tmpfs /scratch/jjyeung \
  --ro-bind /scratch/jjyeung/envs/p1cpu /scratch/jjyeung/envs/p1cpu --tmpfs /x --ro-bind $T /x/tree --ro-bind $M/x/k /x/k --ro-bind $M/x/u /x/u --ro-bind $M/ident.py /x/ident.py \
  --dev /dev --proc /proc --tmpfs /tmp --unshare-net --chdir /x env -i PATH=/usr/bin:/bin OMP_NUM_THREADS=2 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /x/ident.py > $M/ident_out.json 2>&1; cat $M/ident_out.json; sha256sum $M/ident_out.json
echo "== r1_components"; cat $T/student_pilot/r1_components.py
echo "== r2_policy 125-165"; sed -n 125,165p $T/student_pilot/r2_policy.py
echo "== tests"; grep -rln "COMPONENT_EVIDENCE_DEFERRED" $T --include=*.py | head; grep -rn "COMPONENT_EVIDENCE_DEFERRED" $T --include=*.py | grep -i test | head -10
echo "== who calls r1_components.deferred"; grep -rn "r1_components" --include=*.py $T | grep -v "/tests/" | head -20
