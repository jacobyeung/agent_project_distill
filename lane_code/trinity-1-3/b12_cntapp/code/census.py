import json, os, glob, collections, sys, itertools
sys.path.insert(0, os.path.dirname(__file__))
from gtvis import *
W = '/scratch/jjyeung/orch_n30/b12_cntapp/work'
am = json.load(open('/scratch/jjyeung/orch_n30/rows_a2/work/alias_map.json'))
pins = json.load(open(W + '/v5_scene_pins.json'))
dv = json.load(open(W + '/d0_vocab.json')); bv = json.load(open(W + '/bench_vocab.json'))
DSN = {'d1': 'scannet', 'd2': 'scannetpp', 'd3': 'arkitscenes'}
vocab = {}
for ds, bn in DSN.items():
    v = set()
    for k, c in dv.items():
        if k.endswith('|' + ds): v |= {norm(x) for x in c}
    for k, c in bv.items():
        if k.endswith('|' + bn): v |= {norm(x) for x in c}
    vocab[ds] = v - DENY
roots = sys.argv[1:] or ['/scratch/jjyeung/orch_n30/rows_a2/work/k1r']
R = {}
for r in roots:
    for f in glob.glob(r + '/**/*.npz', recursive=True): R.setdefault(os.path.basename(f)[:-4], f)
def key(c):
    ds, i = c.split('/')
    return i if ds == 'arkitscenes' else c.replace('scannetpp/', 'scannetppv2/').replace('/', '__')
st = collections.Counter(); per = {}
for a, p in sorted(pins.items()):
    ds = a[:2]; c = am.get(a)
    if not c: st[(ds, 'no canonical')] += 1; continue
    k = key(c)
    if k not in R: st[(ds, 'no raster yet')] += 1; continue
    rs = load_raster(R[k])
    if rs['fi'] != p[0]: st[(ds, 'raster pins differ')] += 1; continue
    st[(ds, 'raster ok')] += 1
    by = categories(rs); labels = set(by)
    cnt = collections.Counter(); app = {}; fsr = 0; elig = []
    for cat, ids in by.items():
        if cat in DENY: cnt['deny'] += 1; continue
        invocab = cat in vocab[ds]
        amb = ambiguous(cat, labels)
        fs = [first_seen(rs, i) for i in ids]
        allvis = all(f is not None for f in fs)
        anyvis = any(f is not None for f in fs)
        if not invocab: cnt['not in vocab'] += 1; continue
        if amb: cnt['ambiguous sibling label'] += 1; continue
        if len(ids) >= 2:
            cnt['pairs n>=2'] += 1
            if allvis: cnt['count eligible (n>=2, all visible)'] += 1; elig.append([cat, len(ids)])
        if anyvis:
            app[cat] = min(f for f in fs if f is not None)
    # appearance: 4-subsets with pairwise first-seen gap >= 2
    cats = sorted(app); n4 = 0
    for comb in itertools.combinations(cats, 4):
        fr = sorted(app[x] for x in comb)
        if all(b - a >= 2 for a, b in zip(fr, fr[1:])): n4 += 1
    per[a] = dict(canonical=c, ds=ds, count_eligible=cnt['count eligible (n>=2, all visible)'], app_cats=len(app), elig=elig, app=app, app_4sets=n4, cnt=dict(cnt))
    st[(ds, 'count eligible pairs')] += cnt['count eligible (n>=2, all visible)']; st[(ds, 'pairs n>=2 (vocab, unambiguous)')] += cnt['pairs n>=2']
    st[(ds, 'appearance categories (vocab, unambiguous, visible)')] += len(app); st[(ds, 'appearance 4-sets gap>=2')] += min(n4, 10**9)
    st[(ds, 'scenes with >=1 appearance 4-set')] += n4 > 0
for k, v in sorted(st.items()): print(k, v)
json.dump(per, open(W + '/CENSUS_PER_SCENE.json', 'w'), indent=0)
