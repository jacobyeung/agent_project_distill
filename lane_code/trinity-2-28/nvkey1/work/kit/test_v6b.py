"""nvkey3 dry test of v6b_jobs.py and score_v6b.py with an oracle labeller built from the rasters (writes only under K/v6b/test; sends nothing)."""
import json, os, sys, collections, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import v6b_jobs as J, score_v6b as S
from score_v1 import names_match
K = J.K; T = K + '/v6b/test'; os.makedirs(T, exist_ok=True)
for fn in os.listdir(T): os.replace(os.path.join(T, fn), os.path.join(T, '.old_' + fn))
qa, qn, qi = T + '/A.jsonl', T + '/N.jsonl', T + '/I.jsonl'
J.build(qa, qn, 'first30')
def oracle(t):
    m = t['meta']; R = S.raster(m['canonical']); area = float(R['H'] * R['W']); out = {}
    for k in range(32): out[str(k + 1)] = {}
    for kind in m['kinds']:
        role = m['roles'][kind]
        ids = [i for i, l in zip(R['ids'], R['labels']) if (names_match(kind, l) if role == 'inventory' else l == kind)]
        for k in range(32):
            mk = np.isin(R['inst'][k], ids) if ids else None
            if mk is not None and mk.sum() / area >= 0.002:
                ys, xs = np.nonzero(mk); j = len(ys) // 2; out[str(k + 1)][kind] = [int(1000 * (xs[j] + 0.5) / R['W']), int(1000 * (ys[j] + 0.5) / R['H'])]
            else: out[str(k + 1)][kind] = None
    return json.dumps(out)
def oracle_n(t):
    m = t['meta']; R = S.raster(m['canonical']); area = float(R['H'] * R['W']); inv = []
    for i, l in zip(R['ids'], R['labels']):
        if l in S.STRUCT or l in m['named'] or any(x['name'] == l for x in inv): continue
        if max([float((R['inst'][k] == i).sum()) / area for k in R['valid']] or [0]) >= 0.01: inv.append({'name': l, 'aliases': [l + ' unit', 'thing'], 'look_alike': 'box', 'one_object': True, 'part_of_larger': False, 'group': False})
    inv.append({'name': 'unicorn statue', 'aliases': ['statue', 'figure'], 'look_alike': 'lamp', 'one_object': True, 'part_of_larger': False, 'group': False})
    return json.dumps({'inventory': inv[:25]})
def fake(qf, of, f):
    with open(of, 'w') as o:
        for l in open(qf):
            t = json.loads(l); o.write(json.dumps({'id': t['id'], 'model': t['model'], 'meta': t['meta'], 'text': f(t), 'finish': 'stop'}) + '\n')
fake(qa, T + '/A.out.jsonl', oracle); fake(qn, T + '/N.out.jsonl', oracle_n)
print('chain', J.chain(T + '/N.out.jsonl', 'no_such_job', qi), 'again', J.chain(T + '/N.out.jsonl', 'no_such_job', qi))
fake(qi, T + '/I.out.jsonl', oracle)
A = [json.loads(l) for l in open(qa)]; N = [json.loads(l) for l in open(qn)]; I = [json.loads(l) for l in open(qi)]
print('tasks A', len(A), 'N', len(N), 'I', len(I), 'I per capture', collections.Counter(collections.Counter(t['meta']['canonical'] for t in I).values()))
print('kinds per A', collections.Counter(len(t['meta']['kinds']) for t in A), 'per I', collections.Counter(len(t['meta']['kinds']) for t in I))
print('images per task', collections.Counter(sum(1 for c in t['content'] if 'image' in c) for t in A + N + I))
print('A text:', A[0]['content'][0]['text'][:700].replace('\n', ' | '))
print('N text:', N[0]['content'][0]['text'][:900].replace('\n', ' | '))
print('I meta sample:', json.dumps({k: I[0]['meta'][k] for k in ('kinds', 'roles', 'union_size', 'n_replies', 'label_note')})[:700])
print('ids unique', len(set(t['id'] for t in A + N + I)) == len(A + N + I), 'tags', collections.Counter(t['meta']['tag'] for t in A + N + I))
