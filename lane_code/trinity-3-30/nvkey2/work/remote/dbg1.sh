K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1; P=/scratch/jjyeung/envs/p1cpu/bin/python
$P -B - <<'PY'
import json, sys
sys.path.insert(0, 'kit')
from score_v1 import parse
for fn in ('out/48_v6p30astra.jsonl', 'out/47_v6p30argmed.jsonl', 'out/45_v6p30.jsonl'):
    n = 0
    for l in open(fn):
        r = json.loads(l); d = parse(r['text'])
        if d is None:
            t = r['text'] or ''
            print(fn, 'UNPARSED', r['id'][:20], len(t), r['finish'], r['usage'], repr(t[:200]), '...', repr(t[-200:]))
            n += 1
            if n >= 2: break
    for l in open(fn):
        r = json.loads(l); d = parse(r['text'])
        if isinstance(d, dict):
            nm = d.get('named') or {}
            print(fn, 'OK', r['id'][:20], 'keys', list(d)[:5], 'named', {k: (v.get('states') if isinstance(v, dict) else v) for k, v in list(nm.items())[:3]})
            inv = d.get('inventory') or []
            print('  inventory n', len(inv), json.dumps(inv[:1])[:300])
            break
PY
