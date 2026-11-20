W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; I=$W/w24i; P=/scratch/jjyeung/envs/p1cpu/bin/python
$P -I -s -B - <<'PY'
import json,base64,hashlib
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'
s=json.load(open(W+'/w24i/out/kit_n_go/k/s.json')); s=json.loads(base64.b64decode(s['payload'])) if 'payload' in s else s
b=json.loads(base64.b64decode(s['entries']['u/b42c5b02e400d2bd1f0f423bd434c720826e66c17932fe22ac89b62e326b64b8']['payload']))
print('cells0',json.dumps(b['cells'][0])); print('cells16',json.dumps(b['cells'][16]))
print('ncells',len(b['cells']), 'sum vqa', sum(c['rows_per_step'] for c in b['cells'] if c.get('stream')=='vqa'))
for c in b['cells']: print(' ',c.get('stream'),c.get('type'),c.get('rows_per_step'),c.get('ceiling_rows_per_step'))
print('keys',[k for k in b if k!='cells'])
PY
echo "== PREP_FIELDS"; sha256sum $W/w24/out/PREP_FIELDS.md; grep -n -i "r2_sampling\|indices\|population\|row_plan" $W/w24/out/PREP_FIELDS.md | head
echo "== DRAW TABLE"; sha256sum $I/out/DRAW_TABLE_24M4I.md; head -c 9000 $I/out/DRAW_TABLE_24M4I.md
