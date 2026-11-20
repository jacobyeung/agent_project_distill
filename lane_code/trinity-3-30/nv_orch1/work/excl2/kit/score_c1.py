"""nvkey1: score fat presence-and-point labels against K1 raster truth at the 32 anchors.
usage: score_c1.py OUT.jsonl [more.jsonl ...] -> prints a table per (model, nframes, side) and writes work/scores/C1_<tag>.json
Truth: visible = class share >= 0.2% in a valid frame; absent = 0 pixels; slivers and invalid frames are not scored.
Point: inside the class mask at raster resolution (exact pixel, and with a 1-pixel tolerance). Intervals: capture-clustered bootstrap, 2,000 draws."""
import json, re, sys, os, collections, random
import numpy as np
K = '/scratch/jjyeung/orch_n30/nvkey1/work'
man = json.load(open(K + '/c1/C1_MANIFEST.json'))
def parse(t):
    if not t: return None
    t = t.strip(); t = re.sub(r'^```(json)?', '', t).strip(); t = re.sub(r'```$', '', t).strip()
    try: return json.loads(t)
    except Exception:
        i, j = t.find('{'), t.rfind('}')
        try: return json.loads(t[i:j + 1])
        except Exception: return None
def band(s):
    return 'absent' if s == 0 else ('<0.2%' if s < 0.002 else ('0.2-1%' if s < 0.01 else ('1-5%' if s < 0.05 else '>=5%')))
truth = {}
for a in man:
    z = np.load(K + '/c1/%s.npz' % a, allow_pickle=True); H, W = [int(x) for x in z['shape']]
    mask = np.unpackbits(z['mask'], axis=-1)[..., :W].astype(bool)
    truth[a] = dict(classes=[str(c) for c in z['classes']], share=z['share'], mask=mask, missing=z['missing'], H=H, W=W)
rows = []
for fn in sys.argv[1:]:
    for l in open(fn):
        r = json.loads(l); m = r['meta']; a = m['alias']; T = truth[a]; d = parse(r['text'])
        key = (r['model'].split('/')[-1], m['n'], m.get('side', 640))
        for ci, c in enumerate(T['classes']):
            for k in range(32):
                if T['missing'][k]: continue
                s = float(T['share'][ci, k]); b = band(s)
                if b == '<0.2%': continue
                lab = str(m['slots'][k] + 1) if m['n'] == 64 else str(k + 1)
                v = None if d is None else (d.get(lab) or {}).get(c, 'MISSING') if isinstance(d.get(lab), dict) else 'MISSING'
                if v == 'MISSING' or d is None: said = None
                else: said = v is not None and isinstance(v, (list, tuple)) and len(v) == 2
                hit = hit1 = None
                if said and b != 'absent':
                    x = min(T['W'] - 1, max(0, int(float(v[0]) / 1000.0 * T['W']))); y = min(T['H'] - 1, max(0, int(float(v[1]) / 1000.0 * T['H'])))
                    mk = T['mask'][ci, k]; hit = bool(mk[y, x]); hit1 = bool(mk[max(0, y - 1):y + 2, max(0, x - 1):x + 2].any())
                rows.append(dict(key=key, alias=a, cls=c, k=k, pos=(m['slots'][k] if m['n'] == 64 else k) / float(m['n']), ci=ci, nk=len(T['classes']),
                                 band=b, truth=b != 'absent', said=said, hit=hit, hit1=hit1, parsed=d is not None, ds=man[a]['dataset']))
def boot(sub, f, n=2000):
    caps = sorted(set(r['alias'] for r in sub)); by = collections.defaultdict(list)
    for r in sub: by[r['alias']].append(r)
    rng = random.Random(7); vals = []
    for _ in range(n):
        s = [r for c in (rng.choice(caps) for _ in caps) for r in by[c]]
        v = f(s)
        if v is not None: vals.append(v)
    vals.sort(); return (round(vals[int(0.025 * len(vals))], 1), round(vals[int(0.975 * len(vals)) - 1], 1)) if vals else None
def acc(s):
    s = [r for r in s if r['said'] is not None]; return 100.0 * sum(r['said'] == r['truth'] for r in s) / len(s) if s else None
def ptin(s, f='hit'):
    s = [r for r in s if r['truth'] and r['said']]; return 100.0 * sum(bool(r[f]) for r in s) / len(s) if s else None
res = collections.OrderedDict()
for key in sorted(set(r['key'] for r in rows)):
    R = [r for r in rows if r['key'] == key]; out = collections.OrderedDict()
    out['captures'] = len(set(r['alias'] for r in R)); out['facts'] = len(R); out['unparsed_facts'] = sum(1 for r in R if r['said'] is None)
    out['presence_all'] = (acc(R), boot(R, acc))
    for b in ('>=5%', '1-5%', '0.2-1%', 'absent'):
        S = [r for r in R if r['band'] == b]; out['presence_' + b] = (acc(S), boot(S, acc), len(S))
    S = [r for r in R if r['band'] in ('>=5%', '1-5%')]; out['presence_>=1%'] = (acc(S), boot(S, acc), len(S))
    for b in ('>=5%', '1-5%', '0.2-1%'):
        S = [r for r in R if r['band'] == b]; out['point_' + b] = (ptin(S), boot(S, ptin), sum(1 for r in S if r['said']))
    S = [r for r in R if r['band'] in ('>=5%', '1-5%')]; out['point_>=1%'] = (ptin(S), boot(S, ptin), sum(1 for r in S if r['said'])); out['point_>=1%_tol1'] = (ptin(S, 'hit1'),)
    for q in range(4):
        S = [r for r in R if int(r['pos'] * 4) == q]; out['presence_pos_q%d' % (q + 1)] = acc(S)
    S1 = [r for r in R if r['ci'] < r['nk'] / 2.0]; S2 = [r for r in R if r['ci'] >= r['nk'] / 2.0]; out['presence_first_half_kinds'] = acc(S1); out['presence_second_half_kinds'] = acc(S2)
    for ds in ('arkitscenes', 'scannet', 'scannetpp'):
        S = [r for r in R if r['ds'] == ds]; out['presence_' + ds] = acc(S)
    res['%s|f%d|s%d' % key] = out
    print('%s f%d s%d' % key, json.dumps(out))
os.makedirs(K + '/scores', exist_ok=True)
tag = os.path.basename(sys.argv[1]).replace('.jsonl', '')
json.dump(res, open(K + '/scores/C1_%s.json' % tag, 'w'), indent=1)
