python3 - <<'PY'
import json
for l in open('/project/community/jjyeung/okh7/x_3fdda0fb/runs/17c4ffa4/metrics_170710.jsonl'):
    if not l.startswith('{'): continue
    r=json.loads(l)
    if r['step'] in (49,50,51):
        rs=r['ranks']; print(r['step'], json.dumps(rs[0]['h1_answer_stop']), [x['h1_answer_counts'] for x in rs][0])
PY
