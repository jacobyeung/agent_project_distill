set +x
K=/scratch/jjyeung/orch_n30/nvkey1/work; P=/scratch/jjyeung/envs/p1cpu/bin/python; cd $K
cat > $K/kit/score_c0.py <<'PYEOF'
"""nvkey1 C0 scoring: (1) calibration of the census labels against dev-S1 GT rasters (38 captures); (2) the visibility census joined to the
step-544 routed reads (grd_funnel1 items544/objects544); (3) the points file for the GPU ceiling read (cont_ops24 format).
usage: score_c0.py OUT.jsonl  -> work/scores/C0_*.json, work/c0/POINTS_<model>.json"""
import json, re, sys, os, collections, random, hashlib
import numpy as np
K = '/scratch/jjyeung/orch_n30/nvkey1/work'; G = '/scratch/jjyeung/orch_n30/grd_funnel1/work'
sys.path.insert(0, K + '/kit')
man = json.load(open(K + '/c0/C0_MANIFEST.json'))
items = {json.loads(l)['item_id']: json.loads(l) for l in open(G + '/items544.jsonl')}
objs = [json.loads(l) for l in open(G + '/objects544.jsonl')]
from c1_jobs import PROMPT
def parse(t):
    if not t: return None
    t = t.strip(); t = re.sub(r'^```(json)?', '', t).strip(); t = re.sub(r'```$', '', t).strip()
    try: return json.loads(t)
    except Exception:
        i, j = t.find('{'), t.rfind('}')
        try: return json.loads(t[i:j + 1])
        except Exception: return None
def band(s): return 'absent' if s == 0 else ('<0.2%' if s < 0.002 else ('0.2-1%' if s < 0.01 else ('1-5%' if s < 0.05 else '>=5%')))
def get(d, k, n):
    v = (d or {}).get(str(k + 1))
    if not isinstance(v, dict): return 'MISSING'
    return v.get(n, 'MISSING')
lab = collections.defaultdict(dict)   # model -> scene -> parsed
for l in open(sys.argv[1]):
    r = json.loads(l); lab[r['model'].split('/')[-1]][r['meta']['scene']] = parse(r['text'])
res = collections.OrderedDict()
for model, per in lab.items():
    out = collections.OrderedDict(); rows = []
    for sc, d in per.items():
        m = man[sc]
        if not m['gt']: continue
        z = np.load(K + '/c0/' + m['gt'], allow_pickle=True); H, W = [int(x) for x in z['shape']]
        mask = np.unpackbits(z['mask'], axis=-1)[..., :W].astype(bool)
        for ci, n in enumerate([str(x) for x in z['names']]):
            for k in range(32):
                if z['missing'][k]: continue
                s = float(z['share'][ci, k]); b = band(s)
                if b == '<0.2%': continue
                v = get(d, k, n); said = None if (v == 'MISSING' or d is None) else (isinstance(v, (list, tuple)) and len(v) == 2)
                hit = None
                if said and b != 'absent':
                    x = min(W - 1, max(0, int(float(v[0]) / 1000.0 * W))); y = min(H - 1, max(0, int(float(v[1]) / 1000.0 * H))); hit = bool(mask[ci, k][max(0, y - 1):y + 2, max(0, x - 1):x + 2].any()); hit0 = bool(mask[ci, k][y, x])
                rows.append(dict(cap=sc, band=b, truth=b != 'absent', said=said, hit=hit))
    def acc(S):
        S = [r for r in S if r['said'] is not None]; return round(100.0 * sum(r['said'] == r['truth'] for r in S) / len(S), 1) if S else None
    def pt(S):
        S = [r for r in S if r['truth'] and r['said']]; return round(100.0 * sum(bool(r['hit']) for r in S) / len(S), 1) if S else None
    def boot(S, f):
        caps = sorted(set(r['cap'] for r in S)); by = collections.defaultdict(list)
        for r in S: by[r['cap']].append(r)
        rng = random.Random(11); v = []
        for _ in range(2000):
            x = f([r for c in (rng.choice(caps) for _ in caps) for r in by[c]])
            if x is not None: v.append(x)
        v.sort(); return [v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]] if v else None
    cal = collections.OrderedDict(facts=len(rows), captures=len(set(r['cap'] for r in rows)))
    cal['presence_all'] = [acc(rows), boot(rows, acc)]
    for b in ('>=5%', '1-5%', '0.2-1%', 'absent'):
        S = [r for r in rows if r['band'] == b]; cal['presence_' + b] = [acc(S), boot(S, acc), len(S)]
    for b in ('>=5%', '1-5%', '0.2-1%'):
        S = [r for r in rows if r['band'] == b]; cal['point_tol1_' + b] = [pt(S), boot(S, pt), sum(1 for r in S if r['said'])]
    out['calibration_devS1_gt'] = cal
    # census
    cen = []; 
    for o in objs:
        sc = o['scene']; d = per.get(sc)
        if d is None: continue
        v = [get(d, k, o['name']) for k in range(32)]; vis = [isinstance(x, (list, tuple)) and len(x) == 2 for x in v]
        it = items[o['item_id']]
        cen.append(dict(item=o['item_id'], op=o['operand'], name=o['name'], V=sum(vis), R=o.get('selected_frame_count') or 0, state=o.get('state'),
                        gap=it.get('gap_score'), score=it.get('score'), group=it.get('group'), parsed=d is not None,
                        unanswered=sum(1 for x in v if x == 'MISSING')))
    tab = collections.Counter(('V0' if c['V'] == 0 else 'V1-2' if c['V'] < 3 else 'V3+', 'R<3' if c['R'] < 3 else 'R3+') for c in cen)
    out['census_objects'] = len(cen); out['census_V_by_R'] = {'%s|%s' % k: v for k, v in sorted(tab.items())}
    out['census_V_hist'] = dict(collections.Counter(min(c['V'], 10) for c in cen))
    # items: worst object
    byi = collections.defaultdict(list)
    for c in cen: byi[c['item']].append(c)
    grp = collections.defaultdict(list)
    for i, cs in byi.items():
        sparse = [c for c in cs if c['R'] < 3]
        if not sparse: g = 'reader>=3 on both'
        elif all(c['V'] >= 3 for c in sparse): g = 'reader<3 but labeller sees >=3 (proposal/selection limit)'
        elif any(c['V'] == 0 for c in sparse): g = 'reader<3 and labeller sees 0 (absent from the 32 frames)'
        else: g = 'reader<3 and labeller sees 1-2 (frame-count limit)'
        grp[g].append(cs[0])
    out['items_by_group'] = {g: dict(n=len(v), gap_mean=round(float(np.mean([c['gap'] for c in v if c['gap'] is not None])), 2) if any(c['gap'] is not None for c in v) else None,
                                     answer_mean=round(float(np.mean([c['score'] for c in v if c['score'] is not None])), 2) if any(c['score'] is not None for c in v) else None)
                             for g, v in sorted(grp.items())}
    res[model] = out
    print(model, json.dumps(out))
    # points for the GPU ceiling read
    P = {}
    for iid, it in items.items():
        sc = it['scene']; d = per.get(sc)
        if d is None: continue
        src = it['source_frame_indices']; P[iid] = {}
        for n in it['names']:
            P[iid][n] = {str(src[k]): ([round(float(v[0]) / 1000.0, 4), round(float(v[1]) / 1000.0, 4)] if isinstance(v, (list, tuple)) and len(v) == 2 else None)
                         for k, v in ((k, get(d, k, n)) for k in range(32))}
    shas = {sc: [os.path.basename(f).split('.')[0] for f in man[sc]['frames']] for sc in per}
    psha = {sc: hashlib.sha256(PROMPT.format(n=32, kinds=json.dumps(man[sc]['names']), k0=man[sc]['names'][0]).encode()).hexdigest() for sc in per}
    json.dump({'model': model, 'route': 'https://inference-api.nvidia.com/v1/chat/completions', 'frames': '32 read anchors per capture, 640x480 JPEG q90, each after a text label "Frame k"',
               'prompt_template_sha256': hashlib.sha256(PROMPT.encode()).hexdigest(), 'prompt_sha256_by_scene': psha, 'frame_sha256_by_scene': shas,
               'format': '{item_id: {object_name: {source_index: [x_norm, y_norm] or null}}}; x right, y down, in [0, 1] of the anchor frame; null = not visible',
               'points': P},
              open(K + '/c0/POINTS_%s.json' % model, 'w'))
os.makedirs(K + '/scores', exist_ok=True); json.dump(res, open(K + '/scores/C0_census32.json', 'w'), indent=1)
PYEOF
wc -l out/20_c0census32.jsonl
$P -B kit/score_c0.py out/20_c0census32.jsonl 2>&1 | cut -c1-3000
ls -la c0/POINTS_*.json
$P - <<'PY'
import json, collections
K='/scratch/jjyeung/orch_n30/nvkey1/work'
# agreement between the two models on per-frame presence
def parse(t):
    import re
    t=(t or '').strip(); t=re.sub(r'^```(json)?','',t).strip(); t=re.sub(r'```$','',t).strip()
    try: return json.loads(t)
    except Exception:
        i,j=t.find('{'),t.rfind('}')
        try: return json.loads(t[i:j+1])
        except Exception: return None
L=collections.defaultdict(dict)
for l in open(K+'/out/20_c0census32.jsonl'):
    r=json.loads(l); L[r['meta']['scene']][r['model'].split('/')[-1]]=(parse(r['text']), r['meta']['kinds'])
ag=0; n=0; both=0; onlyA=0; onlyB=0
for sc,d in L.items():
    if len(d)<2: continue
    (a,ka),(b,kb)=d['gemini-4-argon'],d['gpt-6.2-astra']
    for k in range(1,33):
        for name in ka:
            va=((a or {}).get(str(k)) or {}).get(name,'M'); vb=((b or {}).get(str(k)) or {}).get(name,'M')
            if va=='M' or vb=='M': continue
            pa=isinstance(va,list); pb=isinstance(vb,list); n+=1; ag+=pa==pb; both+=pa and pb; onlyA+=pa and not pb; onlyB+=pb and not pa
print('model agreement on per-frame presence', round(100*ag/max(1,n),1), 'n', n, 'both yes', both, 'argon only', onlyA, 'astra only', onlyB)
PY
