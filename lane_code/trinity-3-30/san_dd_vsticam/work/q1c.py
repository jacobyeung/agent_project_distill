# Q1 reading, per type: trace features of right vs wrong items at step 200 (accuracy within each feature value), and letter-form lines
import sys, json, random
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_vsticam/work'); from common import *
D = dev(); by = {(d['id'], d['step']): d for d in D}
Q = json.load(open(T + '/q1_rules.json'))
mode = sys.argv[1] if len(sys.argv) > 1 else 'table'
def feats(d):
    v = Q['%s|200' % d['id']]; a = v['a']; fs = d['fs']; k = d['k']
    f = {}
    x = fs.get(a)
    f['answered fs'] = '>32' if x > 32 else ('=k' if x == k else ('<k' if x < k else '>k'))
    f['any fs > 32'] = any(y > 32 for y in fs.values())
    f['any fs = k'] = any(y == k for y in fs.values())
    f['answered = earliest fs'] = a == v['r']['early'][0]
    f['order = fs order'] = d['order'] == sorted(d['opts'], key=lambda z: (fs.get(z, 99), d['opts'].index(z)))
    f['answer = 544 answer'] = a == by[(d['id'], 544)]['opts'][ord(by[(d['id'], 544)]['pred']) - 65]
    f['answer = room pick'] = 'abstain' if v['r']['room'][0] is None else a == v['r']['room'][0]
    f['answer = largest'] = a == v['r']['large'][0]
    return f
if mode == 'table':
    for t in CAM:
        c = defaultdict(Counter)
        for d in D:
            if d['step'] == 200 and d['type'] == t:
                for n, val in feats(d).items(): c[(n, val)][d['score'] == 1] += 1
        print('==', t[-2:])
        for key in sorted(c, key=str):
            print('  %-40s right %3d wrong %3d acc %5.1f' % (str(key), c[key][True], c[key][False], 100 * c[key][True] / (c[key][True] + c[key][False])))
else:
    want = mode; L = 'ABCD'
    its = [d for d in D if d['step'] == 200 and d['type'] in CAM and ((d['score'] == 1) == (want == 'right'))]
    if want == 'right': random.Random(5).shuffle(its); its = its[:60]
    lo, hi = int(sys.argv[2]), int(sys.argv[3])
    for d in its[lo:hi]:
        o = by[(d['id'], 544)]
        print('%s %s k%-2d fs %-15s M %-4s T %s 544 %s %s' % (d['id'][:6], d['type'][-1], d['k'], ','.join(str(d['fs'][z]) for z in d['opts']),
              ''.join(L[d['opts'].index(z)] for z in d['order']), d['gt'], o['pred'], ' '.join('%.1f' % o['dist'][z] for z in d['opts'])))
