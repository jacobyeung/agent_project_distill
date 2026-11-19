"""Independent usage split for all distance items from raw gap responses (no reader/scorer imports)."""
import glob, json, re
from collections import Counter
IN = '/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/'
READS = {'A4': (IN + 'A4/ret/metadata/reads/0', 'a'), 'b1r1': (IN + 'bases/b1/work/ret/metadata/reads/1', 'b')}
items = {i['id']: i for i in json.load(open(IN + 'A4/src/items/devs1_routed.json'))['items']}
res = json.load(open('/scratch/jjyeung/orch_n30/sb_crrev2/scratch/out/t0/callrate.json'))['per_item']
FACT = [('centimet', 100.), ('millimet', 1000.), ('feet', 1/.3048), ('foot', 1/.3048), ('inch', 1/.0254), ('meter', 1.), ('metre', 1.)]


def factor(q):
    q = q.lower()
    for w, f in FACT:
        if w in q:
            return f
    raise ValueError(q)


def close(x, y):
    return x == y if y == 0 else abs(x - y) <= .05 * abs(y)


for read, (path, side) in READS.items():
    rows = {}
    for p in sorted(glob.glob(path + '/metadata/journals/*/*/items.jsonl')):
        for line in open(p):
            r = json.loads(line); rows[r['id']] = r
    cats, mism, noresp = Counter(), [], []
    for k, r in sorted(rows.items()):
        if items[k]['question_type'] != 'object_abs_distance':
            continue
        o = r['output']
        gaps = [x for x in o['calls'].get('records', []) if (x.get('call') or '').startswith('<gap') and x.get('served') is not False]
        vals = [float(m[1]) for x in gaps for m in [re.search(r'distance\s+([-\d.]+)\s*m\b', x.get('response') or '')] if m]
        mine = None
        if vals:
            f = factor(items[k]['question'])
            t = o.get('text', '')
            a = re.findall(r'<answer>\s*(.*?)\s*</answer>', t, re.S)
            m = re.fullmatch(r'\s*([-+]?\d+(?:\.\d*)?)\s*', a[-1]) if a else None
            ans = float(m[1]) if m else None
            if ans is not None and close(ans, vals[-1] * f):
                mine = 'follow_converted'
            elif ans is not None and f != 1 and close(ans, vals[-1]):
                mine = 'copied_unconverted'
            else:
                mine = 'other'
            cats[(mine, 'conv' if f != 1 else 'm')] += 1
        v = res[side][k]
        if v['usage_category'] != mine:
            mism.append((k, mine, v['usage_category'], v['usage_reason']))
        if v['call'] and mine is None:
            noresp.append((k, [(x.get('call'), x.get('served'), (x.get('response') or '')[-80:]) for x in o['calls'].get('records', [])]))
    tot = sum(cats.values())
    print(read, 'eligible', tot, dict(cats))
    for c in ('follow_converted', 'copied_unconverted', 'other'):
        n = sum(v for (cc, _), v in cats.items() if cc == c)
        print('  ', c, n, f'{100*n/tot:.2f}')
    conv = sum(v for (_, u), v in cats.items() if u == 'conv')
    print('   conversion_failure', cats[('copied_unconverted', 'conv')], '/', conv)
    print('   mismatches vs reader:', mism)
    print('   called but ineligible:')
    for k, recs in noresp:
        print('    ', k, recs)
