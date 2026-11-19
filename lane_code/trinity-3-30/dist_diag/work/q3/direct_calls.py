"""Q3: call syntax in the direct reads. Step 200: h1read a8102c3207b (172646) dev-S1 main (1,339) + R0-dev a7 (1,781), full-generation arm
(items_a0.jsonl, 16k); step 544: e193 dev-S1 main (1,525, B2048) and R0-dev adff67f7ae9 (if present). Counts traces with tool-call tags."""
import json, re, os, glob
from collections import Counter, defaultdict
CALL = re.compile(r'<(?:ground|gap|move|turn|room|size|tool_call|tool_response)\b')
SRC = {
 '200_devS1_full': '/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build/a8102c3207b/fetched/x/main/a0/results/0/items_a0.jsonl',
 '200_R0dev_full': '/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build/a8102c3207b/fetched/x/a7/a0/results/0/items_a0.jsonl',
 '544_devS1_B2048': '/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl',
}
r0 = glob.glob('/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build/adff67f7ae9/fetched/x/a7/a0/results/0/items_a0.jsonl')
if r0: SRC['544_R0dev_full'] = r0[0]
out = {}
for name, p in SRC.items():
    if not os.path.exists(p): out[name] = 'missing'; continue
    c = defaultdict(lambda: [0, 0]); ex = {}
    for l in open(p):
        r = json.loads(l); t = r.get('raw_generation') or r.get('token_text') or ''
        k = r.get('question_type') or r.get('task_type'); c[k][0] += 1
        if CALL.search(t):
            c[k][1] += 1; ex.setdefault(k, t[:300])
    out[name] = dict(path=p, by_type={k: dict(items=v[0], with_call_syntax=v[1]) for k, v in sorted(c.items())}, examples=ex)
    print(name, {k: '%d/%d' % (v[1], v[0]) for k, v in sorted(c.items())})
json.dump(out, open('DIRECT_CALL_SYNTAX.json', 'w'), indent=1)
