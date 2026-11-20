F=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24x2/out/rcj/nd.py; sed -n '425,462p' $F | cut -c1-260
D=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173817/173817; cd $D
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json
n=json.load(open('nd.json'))
for k in ('content_bad','extras','content','reader','task_i_detail','metadata_classes'):
    if k in n: print(k, json.dumps(n[k])[:600])
print([k for k in n])
PY
sed -n '1,60p' /scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173754/173754/../../../w24p/out/TASKA_FIELDS_24M4P.md 2>/dev/null | head -40 | cut -c1-300
