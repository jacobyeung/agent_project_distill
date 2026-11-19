W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; T=$W/w24/work/tree_r1; date -u +%TZ
for f in $W/inputs/p_configs/RUNTIME_CONFIG_171377_673bc60f.json $W/inputs/p_configs/cprime_31abe087.json; do python3 -B -c "
import json,sys
d=json.load(open(sys.argv[1])); r=d.get('r1_training') or {}
print(sys.argv[1][-30:], 'r1' in str(list(d)), {k:r.get(k) for k in ('host_receipt','review')})
print([k for k in d if 'r1' in k or 'host' in k or 'review' in k])
" $f </dev/null; done
sed -n 110,150p $T/launch_r1/entry.py </dev/null | cut -c1-200
grep -n -E "ASSERTIONS *=|loader_audit" $T/launch_r1/entry.py $T/launch_r1/production_proof.py </dev/null | head -10 | cut -c1-200
