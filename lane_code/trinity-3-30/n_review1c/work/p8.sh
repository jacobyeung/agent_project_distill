H=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/hash24h1
cat $H/PROVENANCE.md; echo "@@@ VERIFICATION"; cat $H/VERIFICATION.json; echo "@@@ RECOVERY"; cat $H/RECOVERY.json
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json;v=json.load(open('$H/LOOP_HASHES.json'));r=v['rows'];print(len(r));print(json.dumps(r[0])[:600])
"
