set +x
K=/scratch/jjyeung/orch_n30/nvkey1/work; P=/scratch/jjyeung/envs/p1cpu/bin/python
cat > $K/kit/c0_build.py <<'PYEOF'
"""nvkey1 C0: visibility census inputs for the 150 dev-S1 routed-distance items (step 544 read; 60 captures, 300 objects).
Reads grd_funnel1's items544/objects544, the staged read anchors (c0stage/devs1_r2 manifests, c0stage/devs1_frames) and the staged dev-S1 GT
rasters (c0stage/orch_cd/...). Writes work/c0/C0_MANIFEST.json and work/c0/<cap>.npz (masks of GT labels matched to each asked name).
dev-S1 is a held-out development set: nothing here becomes a training row."""
import json, os, collections
import numpy as np
K = '/scratch/jjyeung/orch_n30/nvkey1/work'; S = K + '/c0stage'; G = '/scratch/jjyeung/orch_n30/grd_funnel1/work'
items = [json.loads(l) for l in open(G + '/items544.jsonl')]; objs = [json.loads(l) for l in open(G + '/objects544.jsonl')]
gt = dict((c, p) for c, p in json.load(open(K + '/c0_gt.json')))
ALIAS = {'tv': ['tv', 'television', 'tv monitor', 'monitor'], 'refrigerator': ['refrigerator', 'fridge', 'mini fridge'], 'trash can': ['trash can', 'trash bin', 'garbage bin', 'wastebasket'],
         'sofa': ['sofa', 'couch'], 'heater': ['heater', 'radiator'], 'computer mouse': ['computer mouse', 'mouse'], 'stove': ['stove', 'cooktop', 'oven'],
         'nightstand': ['nightstand', 'night stand', 'bedside table'], 'table': ['table'], 'bed': ['bed']}
def norm(s): return str(s).lower().replace('_', ' ').strip()
os.makedirs(K + '/c0', exist_ok=True)
byc = collections.OrderedDict()
for it in items: byc.setdefault(it['scene'], []).append(it)
man = collections.OrderedDict(); st = collections.Counter()
for sc, its in byc.items():
    name = sc.replace('/', '__'); mp = None
    for g in ('g3s32', 'g3s64'):
        p = '%s/devs1_r2/anchors/%s/%s/A_MANIFEST.json' % (S, g, name)
        if os.path.exists(p): mp = p; break
    sel = json.load(open(mp))['selections'][0]
    assert sel['frame_indices'] == its[0]['source_frame_indices'], sc
    frames = ['%s/devs1_frames/%s' % (S, f['path']) for f in sel['frames']]
    present = sum(os.path.exists(f) for f in frames); st['frames complete' if present == 32 else 'frames incomplete'] += 1
    names = []
    for it in its:
        for n in it['names']:
            if n not in names: names.append(n)
    ent = dict(scene=sc, room=its[0]['room'], frames=frames, frames_present=present, names=names, items=[it['item_id'] for it in its], gt=None, matched={})
    gp = gt.get(sc); lp = gp and (S + '/' + gp[len('/scratch/jjyeung/'):])
    if lp and os.path.exists(lp):
        z = np.load(lp, allow_pickle=True); inst = z['inst']; labels = [norm(x) for x in z['labels']]; ids = [int(x) for x in z['ids']]
        valid = z['valid'] if 'valid' in z.files else np.ones(32, bool)
        fi = [int(x) for x in z['frame_indices']] if 'frame_indices' in z.files else None
        if fi is not None and fi != sel['frame_indices']: st['gt frame grid differs'] += 1
        else:
            masks = []; mnames = []; shares = []
            for n in names:
                cand = ALIAS.get(norm(n), [norm(n)]); ii = [i for i, l in zip(ids, labels) if l in cand]
                if not ii: st['name without gt label'] += 1; continue
                m = np.isin(inst, ii); masks.append(m); mnames.append(n); shares.append(m.reshape(inst.shape[0], -1).mean(1))
                ent['matched'][n] = sorted(set(l for i, l in zip(ids, labels) if i in ii)) + ['instances=%d' % len(ii)]
            if masks:
                np.savez_compressed(K + '/c0/%s.npz' % name, names=np.array(mnames), share=np.stack(shares).astype(np.float32), mask=np.packbits(np.stack(masks), axis=-1),
                                    shape=np.array(inst.shape[1:]), missing=~valid.astype(bool))
                ent['gt'] = name + '.npz'; st['captures with gt truth'] += 1; st['names with gt truth'] += len(mnames)
    man[sc] = ent
json.dump(man, open(K + '/c0/C0_MANIFEST.json', 'w'), indent=0)
print(dict(st), 'captures', len(man), 'names', sum(len(v['names']) for v in man.values()))
PYEOF
cat > $K/kit/c0_jobs.py <<'PYEOF'
"""nvkey1 C0: fat presence-and-point census tasks for the dev-S1 routed-distance captures (one call = every asked name x the 32 read frames).
usage: c0_jobs.py OUT.jsonl MODEL EFFORT [max_side] ; C1_EXTRA env adds request fields (e.g. Claude thinking)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
K = '/scratch/jjyeung/orch_n30/nvkey1/work'
from c1_jobs import PROMPT
out, model, effort = sys.argv[1], sys.argv[2], sys.argv[3]; side = int(sys.argv[4]) if len(sys.argv) > 4 else 640
effort = None if effort == 'none' else effort; extra = json.loads(os.environ.get('C1_EXTRA', '{}'))
man = json.load(open(K + '/c0/C0_MANIFEST.json')); tag = model.split('/')[-1]; n = 0
with open(out, 'a') as f:
    for sc, m in man.items():
        if m['frames_present'] != 32: print('skip incomplete', sc); continue
        kinds = m['names']; content = [{'text': PROMPT.format(n=32, kinds=json.dumps(kinds), k0=kinds[0])}]
        for i, p in enumerate(m['frames']): content += [{'text': 'Frame %d' % (i + 1)}, {'image': p, 'max_side': side}]
        f.write(json.dumps({'id': '%s_%s_f32_s%d' % (sc.replace('/', '__'), tag, side), 'model': model, 'effort': effort, 'max_tokens': 32768, 'extra': extra,
                            'content': content, 'meta': {'scene': sc, 'n': 32, 'side': side, 'kinds': kinds}}) + '\n'); n += 1
print('wrote', n, 'tasks to', out)
PYEOF
cat > $K/kit/c1_jobs.py <<'PYEOF'
"""nvkey1: build fat presence-and-point labelling tasks for K1 calibration captures (one call = every class of a capture x all frames).
usage: c1_jobs.py OUT.jsonl MODEL EFFORT NFRAMES(32|64) [alias,alias,...|all] [max_side]
Frames: /scratch/jjyeung/k1_frames/<sha[:2]>/<sha>.png; truth stays in work/c1 and is never sent."""
import json, os, sys
K = '/scratch/jjyeung/orch_n30/nvkey1/work'
FR = '/scratch/jjyeung/k1_frames'
PROMPT = ('These are {n} frames sampled in time order from one video of an indoor room. Each image follows its label "Frame k" (k = 1 to {n}).\n'
          'Object kinds: {kinds}.\n'
          'For every frame and every object kind, decide whether at least one object of that kind is visible in that frame, fully or partly '
          '(partly visible or partly occluded objects count; reflections and pictures of objects do not). '
          'If it is visible, give one point on a visible part of it (if several are visible, pick the most visible one) as [x, y] in 0-1000 coordinates '
          'of that frame: x = 0 at the left edge and 1000 at the right edge, y = 0 at the top edge and 1000 at the bottom edge. If it is not visible, give null.\n'
          'Reply with one JSON object and nothing else, with one entry for every frame from 1 to {n} and every object kind: '
          '{{"1": {{"{k0}": [x, y] or null, ...}}, "2": {{...}}, ..., "{n}": {{...}}}}')
def main():
    if len(sys.argv) < 5: return
    out, model, effort, n = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    extra = json.loads(os.environ.get('C1_EXTRA', '{}')); effort = None if effort == 'none' else effort
    sel = sys.argv[5] if len(sys.argv) > 5 else 'all'; side = int(sys.argv[6]) if len(sys.argv) > 6 else 640
    man = json.load(open(K + '/c1/C1_MANIFEST.json'))
    aliases = list(man) if sel == 'all' else sel.split(',')
    tag = model.split('/')[-1]
    with open(out, 'a') as f:
        for a in aliases:
            m = man[a]; shas = m['anchors'] if n == 32 else m['dense']
            assert len(shas) == n, (a, len(shas))
            kinds = m['classes']
            content = [{'text': PROMPT.format(n=n, kinds=json.dumps(kinds), k0=kinds[0])}]
            for i, s in enumerate(shas):
                p = '%s/%s/%s.png' % (FR, s[:2], s); assert os.path.isfile(p), p
                content += [{'text': 'Frame %d' % (i + 1)}, {'image': p, 'max_side': side}]
            f.write(json.dumps({'id': '%s_%s_f%d_s%d' % (a, tag, n, side), 'model': model, 'effort': effort, 'max_tokens': 32768, 'extra': extra, 'content': content,
                                'meta': {'alias': a, 'n': n, 'side': side, 'kinds': kinds, 'slots': m['anchor_slots'] if n == 64 else list(range(32))}}) + '\n')
    print('wrote', len(aliases), 'tasks to', out)
if __name__ == '__main__': main()
PYEOF
cat > $K/kit/score_c1.py <<'PYEOF'
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
PYEOF
cat > $K/c0_gt.json <<'JEOF'
[["arkitscenes/41069053", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/41069053.npz"], ["arkitscenes/41069054", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/41069054.npz"], ["arkitscenes/41098140", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/41098140.npz"], ["arkitscenes/41098149", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/41098149.npz"], ["arkitscenes/41126645", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/41126645.npz"], ["arkitscenes/41159771", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/41159771.npz"], ["arkitscenes/41159772", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/41159772.npz"], ["arkitscenes/41159782", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/41159782.npz"], ["arkitscenes/41254810", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/41254810.npz"], ["arkitscenes/41291639", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/41291639.npz"], ["arkitscenes/41291643", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/41291643.npz"], ["arkitscenes/42446097", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/42446097.npz"], ["arkitscenes/42446117", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/42446117.npz"], ["arkitscenes/42897921", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/42897921.npz"], ["arkitscenes/42897936", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/42897936.npz"], ["arkitscenes/42897942", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/42897942.npz"], ["arkitscenes/42899532", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/42899532.npz"], ["arkitscenes/42899535", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/42899535.npz"], ["arkitscenes/42899829", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/42899829.npz"], ["arkitscenes/43649603", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/43649603.npz"], ["arkitscenes/43828324", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/43828324.npz"], ["arkitscenes/43828368", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/43828368.npz"], ["arkitscenes/44358634", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/44358634.npz"], ["arkitscenes/45261332", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/45261332.npz"], ["arkitscenes/45663051", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/45663051.npz"], ["arkitscenes/47330997", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/47330997.npz"], ["arkitscenes/47331002", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/47331002.npz"], ["arkitscenes/47332556", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/47332556.npz"], ["arkitscenes/47332598", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/47332598.npz"], ["arkitscenes/47332599", "/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/47332599.npz"], ["scannet/scene0166_00", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0166_00.npz"], ["scannet/scene0166_02", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0166_02.npz"], ["scannet/scene0250_01", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0250_01.npz"], ["scannet/scene0261_02", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0261_02.npz"], ["scannet/scene0320_01", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0320_01.npz"], ["scannet/scene0380_01", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0380_01.npz"], ["scannet/scene0515_00", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0515_00.npz"], ["scannet/scene0515_01", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0515_01.npz"], ["scannet/scene0515_02", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0515_02.npz"], ["scannet/scene0642_01", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0642_01.npz"], ["scannet/scene0666_01", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannet__scene0666_01.npz"], ["scannetppv2/0c7962bd64", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__0c7962bd64.npz"], ["scannetppv2/17c5e6a336", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__17c5e6a336.npz"], ["scannetppv2/246fe09e98", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__246fe09e98.npz"], ["scannetppv2/307e3262f1", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__307e3262f1.npz"], ["scannetppv2/37c9538a2b", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__37c9538a2b.npz"], ["scannetppv2/38fcf02d0b", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__38fcf02d0b.npz"], ["scannetppv2/3ce6d36ab5", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__3ce6d36ab5.npz"], ["scannetppv2/6a217fbcb0", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__6a217fbcb0.npz"], ["scannetppv2/7e7cd69a59", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__7e7cd69a59.npz"], ["scannetppv2/80ffca8a48", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__80ffca8a48.npz"], ["scannetppv2/99a2503d63", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__99a2503d63.npz"], ["scannetppv2/aaa9c251de", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__aaa9c251de.npz"], ["scannetppv2/ad562ce09b", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__ad562ce09b.npz"], ["scannetppv2/ca3b651c23", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__ca3b651c23.npz"], ["scannetppv2/d6bb698875", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__d6bb698875.npz"], ["scannetppv2/e35232b92f", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__e35232b92f.npz"], ["scannetppv2/e667e09fe6", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__e667e09fe6.npz"], ["scannetppv2/e7ccd75e5d", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__e7ccd75e5d.npz"], ["scannetppv2/eb8ef9b4cc", "/scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__eb8ef9b4cc.npz"]]
JEOF
date -u +%T; echo 8 > $K/ctl/RATE
cd $K && $P -B kit/c0_build.py 2>&1 | tail -5
wc -l $K/out/10_bake32.jsonl; $P -B kit/score_c1.py $K/out/10_bake32.jsonl 2>&1 | tail -12
cat $K/meter/METER.json
