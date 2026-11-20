"""C0 cross-check on the GT subset: labeller visible frames V, GT visible frames G (share >= 0.2% and >= 1%), reader frames R; items by group."""
import json, re, collections, numpy as np, sys
K = '/scratch/jjyeung/orch_n30/nvkey1/work'; G = '/scratch/jjyeung/orch_n30/grd_funnel1/work'
man = json.load(open(K + '/c0/C0_MANIFEST.json')); objs = [json.loads(l) for l in open(G + '/objects544.jsonl')]
items = {json.loads(l)['item_id']: json.loads(l) for l in open(G + '/items544.jsonl')}
def parse(t):
    t = (t or '').strip(); t = re.sub(r'^```(json)?', '', t).strip(); t = re.sub(r'```$', '', t).strip()
    try: return json.loads(t)
    except Exception:
        i, j = t.find('{'), t.rfind('}')
        try: return json.loads(t[i:j + 1])
        except Exception: return None
lab = collections.defaultdict(dict)
for l in open(K + '/out/20_c0census32.jsonl'):
    r = json.loads(l); lab[r['model'].split('/')[-1]][r['meta']['scene']] = parse(r['text'])
gts = {}
for sc, m in man.items():
    if m['gt']:
        z = np.load(K + '/c0/' + m['gt'], allow_pickle=True); gts[sc] = ({str(n): i for i, n in enumerate(z['names'])}, z['share'], z['missing'])
def b(v): return '0' if v == 0 else ('1-2' if v < 3 else '3+')
for model, per in lab.items():
    rows = []
    for o in objs:
        sc = o['scene']
        if sc not in gts or o['name'] not in gts[sc][0]: continue
        idx, sh, miss = gts[sc]; ci = idx[o['name']]; d = per.get(sc) or {}
        V = sum(1 for k in range(32) if isinstance((d.get(str(k + 1)) or {}).get(o['name']), list))
        G2 = sum(1 for k in range(32) if not miss[k] and sh[ci, k] >= 0.002); G10 = sum(1 for k in range(32) if not miss[k] and sh[ci, k] >= 0.01)
        rows.append(dict(V=V, G2=G2, G10=G10, R=o.get('selected_frame_count') or 0, item=o['item_id']))
    sp = [r for r in rows if r['R'] < 3]
    print(model, 'GT-subset objects', len(rows), 'with R<3', len(sp))
    print('  R<3: labeller V', dict(collections.Counter(b(r['V']) for r in sp)), '| GT >=0.2%', dict(collections.Counter(b(r['G2']) for r in sp)), '| GT >=1%', dict(collections.Counter(b(r['G10']) for r in sp)))
    print('  R>=3: labeller V', dict(collections.Counter(b(r['V']) for r in rows if r['R'] >= 3)), '| GT >=0.2%', dict(collections.Counter(b(r['G2']) for r in rows if r['R'] >= 3)))
    print('  labeller V bucket x GT>=0.2% bucket', dict(collections.Counter((b(r['V']), b(r['G2'])) for r in rows)))
    byi = collections.defaultdict(list)
    for r in rows: byi[r['item']].append(r)
    grp = collections.defaultdict(list)
    for i, rs in byi.items():
        if len(rs) < 2: continue
        sparse = [r for r in rs if r['R'] < 3]
        g = 'both R>=3' if not sparse else ('sparse, GT>=3' if all(r['G2'] >= 3 for r in sparse) else ('sparse, GT 0' if any(r['G2'] == 0 for r in sparse) else 'sparse, GT 1-2'))
        grp[g].append(items[i].get('gap_score'))
    print('  items with both objects in GT', {g: (len(v), round(float(np.mean([x for x in v if x is not None])), 1)) for g, v in sorted(grp.items())})
