"""Scorer determinism: two independent runs of scorer.py on the same 10 captures; reports max |logit diff| per arm."""
import json, sys
from pathlib import Path
a, b = Path(sys.argv[1]), Path(sys.argv[2])
res = {}
for sub in ('V', 'IY'):
    for p in sorted((a / sub).glob('*.jsonl')):
        q = b / sub / p.name
        ra = [json.loads(l) for l in open(p) if '"timing"' not in l]
        rb = [json.loads(l) for l in open(q) if '"timing"' not in l]
        assert [(r['arm'], r['obj'], r['frame']) for r in ra] == [(r['arm'], r['obj'], r['frame']) for r in rb], p.name
        for x, y in zip(ra, rb):
            d = res.setdefault(x['arm'], dict(n=0, max_abs=0.0, sign_flips=0, top_diff=0))
            d['n'] += 1; d['max_abs'] = max(d['max_abs'], abs(x['logit'] - y['logit']))
            d['sign_flips'] += (x['logit'] > 0) != (y['logit'] > 0); d['top_diff'] += x['top'] != y['top']
res['pass'] = bool(res) and all(v['max_abs'] < 0.25 and v['sign_flips'] == 0 for k, v in res.items() if k != 'pass')
print(json.dumps(res))
Path(sys.argv[3]).write_text(json.dumps(res, indent=1) + '\n')
