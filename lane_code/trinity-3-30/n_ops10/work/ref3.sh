X=/project/community/jjyeung/okh7/x_22c714e1; D=$X/o/174113; echo "REF3 $(date -u +%FT%TZ)"
python3 - $D/q0.json <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
f=d.get('forward'); print("forward type", type(f).__name__); print(json.dumps(f)[:3000])
s=d.get('steps'); print("steps:", json.dumps(s)[:2500])
PY
cat $D/q.steps | tail -12 | cut -c1-300
