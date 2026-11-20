"""Compare per-test outcomes between sandboxed runs; write TESTS_COMPARE.json."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

W = Path(__file__).resolve().parent
T = W/'tests_out'


def load(name):
    return json.loads((T/(name+'.json')).read_text())


def norm(m):
    return re.sub(r'\b[0-9a-f]{8}\b|tmp[a-z0-9_]{6,}|\d+\.\d+s', '#', m or '')


def compare(x, y):
    a, b = load(x)['rows'], load(y)['rows']
    common = sorted(set(a) & set(b))
    changed = [dict(test=k, **{x: a[k], y: b[k]}) for k in common
               if [[s, norm(m)] for s, m in a[k]] != [[s, norm(m)] for s, m in b[k]]]
    only_y = sorted(set(b) - set(a))
    only_x = sorted(set(a) - set(b))
    return dict(common=len(common), changed=changed, only_in=dict({x: only_x, y: only_y}),
                only_status={y: dict(Counter(s for k in only_y for s, _ in b[k])),
                             x: dict(Counter(s for k in only_x for s, _ in a[k]))})


def causes(name):
    c = Counter()
    for k, v in load(name)['rows'].items():
        for s, m in v:
            if s in ('fail', 'error'):
                c[(s, norm(m)[:160])] += 1
    return [dict(status=s, cause=m, rows=n) for (s, m), n in c.most_common()]


out = dict(inputs_sha256={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(T.glob('*.json'))})
for name in ('full_base', 'full_a2', 'full2_base', 'full2_a2', 'full_live_base', 'full_live_a2', 'focused_base.v1', 'focused_a2.v1',
             'focused_live_base.v1', 'focused_live_a2.v1'):
    d = load(name)
    out.setdefault('counts', {})[name] = d['counts']
    out.setdefault('denied', {})[name] = dict(Counter(e[0] for e in d['denied']))
for x, y in (('full_base', 'full_a2'), ('full2_base', 'full2_a2'), ('full_live_base', 'full_live_a2'), ('full_base', 'full_live_base'),
             ('full_a2', 'full_live_a2'), ('focused_base.v1', 'focused_a2.v1'), ('focused_live_base.v1', 'focused_live_a2.v1')):
    out[x+'_vs_'+y] = compare(x, y)
out['preexisting_causes_full_base'] = causes('full_base')
out['preexisting_causes_full2_base'] = causes('full2_base')
(W/'TESTS_COMPARE.json').write_text(json.dumps(out, indent=1)+'\n')
for k, v in out.items():
    if '_vs_' in k:
        print(k, 'common', v['common'], 'changed', len(v['changed']), 'only', {a: len(b) for a, b in v['only_in'].items()},
              v['only_status'])
        for c in v['changed'][:10]:
            print('   ', json.dumps(c)[:400])
print(json.dumps(out['counts']))
print(json.dumps(out['denied']))
for key in ('preexisting_causes_full_base', 'preexisting_causes_full2_base'):
    print(key)
    for c in out[key][:25]:
        print(c['rows'], c['status'], c['cause'][:150])
