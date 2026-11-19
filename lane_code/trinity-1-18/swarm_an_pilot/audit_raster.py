
import json, os, sys, collections
import numpy as np
W = '/scratch/jjyeung/orch_n30'
inp = json.load(open(W + '/swarm_an_pilot/audit_in.json'))
man = json.load(open(W + '/geo_k1/stage/K1_MANIFEST.arkit_timing.json')); caps = dict((c['canonical'], c) for c in man['captures'])
RAST = [W + '/gt_build/out/dose_pool/out/t1_gt/gt', W + '/gt_build/out/dose_pool/out/arkit_gt/gt', W + '/gt_build2/out/dose_pool/out/arkit_gt/gt']
def norm(l):
    l = str(l).lower().replace('_', ' ').strip(); return {'tv monitor': 'tv', 'television': 'tv'}.get(l, l)
def sing(l): return l[:-1] if l.endswith('s') and not l.endswith('ss') else l
out = {}
for a, v in inp.items():
    c = caps[v['capture']]; assert c['k1_split'] == 'train' and c['split'] == 'train'
    anc = [c['dense_frames'][s]['sha256'] for s in c['anchor_slots']]
    name = os.path.basename(c['gt']['path']); path = [d + '/' + name for d in RAST if os.path.isfile(d + '/' + name)][-1]
    z = np.load(path, allow_pickle=True); inst = z['inst']; n, H, Wd = inst.shape
    ids = [int(x) for x in z['ids']]; labels = [norm(x) for x in z['labels']]
    share = collections.defaultdict(lambda: np.zeros(32))
    for k in range(32):
        u, cnt = np.unique(inst[k], return_counts=True)
        for x, y in zip(u, cnt):
            if x >= 0: share[int(x)][k] = y / float(H * Wd)
    missing = [k + 1 for k in range(32) if float(z['depth'][k].max()) <= 0]
    O = {}
    for o in v['objs']:
        ii = [i for i, l in zip(ids, labels) if l == norm(o) or sing(l) == sing(norm(o))]
        if not ii: O[o] = None; continue
        sc = sum(share[i] for i in ii); vis = [k + 1 for k in range(32) if sc[k] >= 0.002]
        O[o] = dict(n=len(ii), first=vis[0] if vis else 0, nvis=len(vis), share=[round(float(x), 4) for x in sc],
                    inst_first=sorted([min([k + 1 for k in range(32) if share[i][k] >= 0.002] or [0]) for i in ii]))
    out[a] = dict(frames_equal=anc == v['shas'], n_equal=sum(1 for x, y in zip(anc, v['shas']) if x == y), missing=missing, objs=O, labels=sorted(set(labels)))
print('JSONBEGIN'); print(json.dumps(out)); print('JSONEND')

