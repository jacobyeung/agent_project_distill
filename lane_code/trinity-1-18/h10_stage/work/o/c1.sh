O=/project/community/jjyeung/okh7/e6fc152498/r2/sj/h10sub_b01ec87a6f29b00029a87
python3 - "$O/curve.json" <<'PY'
import json,sys
c=json.load(open(sys.argv[1]))
print(json.dumps({k:c[k] for k in ('export_sha256','item_set_sha256','evaluator_code_sha256','bootstrap','item_count')}))
pt=c['per_type']
print(json.dumps(pt)[:6000])
PY
