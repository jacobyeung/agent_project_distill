"""fix11 static check on the job's own planned bytes: which strings a kit root move from /tmp/q_22c714e1/p to
/tmp/jjyeung/q_22c714e1/p would leave outside the new job folder, and which inputs already name the old q."""
import json, sys
from pathlib import Path
J = Path('/tmp/q_22c714e1_174134')
def strings(v):
    if isinstance(v, dict):
        for k, x in v.items():
            yield from strings(k); yield from strings(x)
    elif isinstance(v, list):
        for x in v: yield from strings(x)
    elif isinstance(v, str): yield v
res = {}
for name in ('r0.json', 'r.json', 'p/plan.json'):
    p = J / name
    if not p.is_file():
        res[name] = 'absent'; continue
    v = json.loads(p.read_text())
    parts = {'plan.json': ('request', 'config')}.get(p.name)
    blobs = {k: v[k] for k in parts} if parts else {'all': v.get('_resolved', v)}
    for k, b in blobs.items():
        s = list(strings(b))
        res[name + ':' + k] = dict(strings=len(s), under_old_q=sum(x.startswith('/tmp/q_22c714e1/p/q/') for x in s),
            under_ns_not_q=sorted({x for x in s if x.startswith('/tmp/q_22c714e1/') and not x.startswith('/tmp/q_22c714e1/p/q/')})[:5],
            n_under_ns_not_q=sum(x.startswith('/tmp/q_22c714e1/') and not x.startswith('/tmp/q_22c714e1/p/q/') for x in s),
            under_q_job=sum(x.startswith('/tmp/q_22c714e1_174134/') for x in s))
print('RESULT ' + json.dumps(res))
