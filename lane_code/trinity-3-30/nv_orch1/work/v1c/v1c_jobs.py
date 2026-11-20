"""nvkey2 V1 form (c): judge pointing claims with a ring on the 640-px frame plus a 256-px close-up crop (ring drawn) of every point claim; 24 claims per call.
Rows: pilot = the 1,208 pointing-store rows with local frames (all dev-S1: tag dev-analysis); nearmiss = 300 claims built from K1 TRAINING rasters with known
truth (100 true points, 50 points just off the object, 50 wrong names, 50 true absent, 50 false absent; objects at 1% of the frame or more): tag train.
Verdicts: point rows on | off | wrong_name | absent | unsure; absent rows absent | visible | unsure. Crops are pre-rendered to K/v1/crops (never truth).
usage: v1c_jobs.py OUT.jsonl SET(pilot|nearmiss) MODEL EFFORT [CHUNK=24]"""
import json, os, sys, random, hashlib, collections
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import excl
K = os.environ.get('NVK', '/scratch/jjyeung/orch_n30/nvkey1/work'); FR = '/scratch/jjyeung/k1_frames'; CR = K + '/v1/crops'
PROMPT = ('You are auditing the labels of a pointing dataset. Each row below shows one video frame of an indoor room and one claim about it.\n'
          '- A point row shows the frame with a red ring, then a close-up crop of the same frame around the ring (the ring is drawn there too). '
          'Its claim: the centre of the ring lies on a visible part of an object of the named kind.\n'
          '- An absent row shows the frame only. Its claim: no object of the named kind is visible anywhere in the frame.\n'
          'Judge every claim from its own images. Give one verdict per row:\n'
          'point rows: "on" (the ring centre lies on a visible part of an object of the named kind), "off" (an object of the named kind is visible in the frame, '
          'but the ring centre is not on it), "wrong_name" (the ring centre is on an object that most people would not call by the named kind or a close synonym, '
          'and no object of that kind is under the ring), "absent" (no object of the named kind is visible anywhere in the frame), or "unsure";\n'
          'absent rows: "absent" (the claim holds), "visible" (an object of the named kind is visible in the frame), or "unsure".\n'
          'Reply with one JSON object and nothing else: {{"<row id>": "<verdict>", ...}} with all {n} row ids.')
ALLOW = set('''chair table sofa couch bed tv monitor door window cabinet shelf bookshelf desk lamp sink toilet bathtub refrigerator fridge stove oven
microwave washer dishwasher fireplace stool pillow backpack keyboard laptop mirror whiteboard blackboard radiator heater printer plant
picture curtain blinds towel suitcase clock telephone nightstand dresser wardrobe bench armchair counter piano guitar bicycle ladder fan
closet bag box bottle cup shower'''.split()) | set(['trash can', 'trash bin', 'office chair', 'coffee table', 'computer tower', 'ceiling light',
    'washing machine', 'coat hanger', 'computer mouse', 'kitchen cabinet', 'dining table', 'shower curtain', 'file cabinet', 'paper towel dispenser'])
def norm(l):
    l = str(l).lower().replace('_', ' ').strip(); return {'tv monitor': 'tv', 'television': 'tv'}.get(l, l)
def head(l):
    h = l.split()[-1]; return h[:-1] if h.endswith('s') and not h.endswith('ss') else h
def crop(path, uv, rid):
    os.makedirs(CR, exist_ok=True); out = '%s/%s.png' % (CR, rid)
    if os.path.exists(out): return out
    im = Image.open(path).convert('RGB'); W, H = im.size; x, y = uv[0] / 1000.0 * W, uv[1] / 1000.0 * H; s = 0.4 * min(W, H)
    x0 = min(max(0.0, x - s / 2), W - s); y0 = min(max(0.0, y - s / 2), H - s)
    c = im.crop((int(x0), int(y0), int(x0 + s), int(y0 + s))).resize((256, 256), Image.LANCZOS)
    px, py = (x - int(x0)) * 256.0 / s, (y - int(y0)) * 256.0 / s; d = ImageDraw.Draw(c); r = 12
    for rr, col in ((r + 2, (0, 0, 0)), (r, (255, 0, 0)), (r - 2, (0, 0, 0))): d.ellipse([px - rr, py - rr, px + rr, py + rr], outline=col, width=2)
    c.save(out); return out
def nearmiss_rows():
    man = json.load(open(K + '/k1r/geo_k1/stage/K1_MANIFEST.arkit_timing.json')); caps = {c['canonical']: c for c in man['captures']}
    idx = json.load(open(K + '/k1r/k1r_index.json')); c1 = {v['canonical'] for v in json.load(open(K + '/c1/C1_MANIFEST.json')).values()}
    pool = sorted(cn for cn in idx if cn not in c1 and not excl.reasons(cn)); rng = random.Random('v1c nearmiss'); rng.shuffle(pool)
    want = collections.OrderedDict([('true_point', 100), ('off', 50), ('wrong_name', 50), ('true_absent', 50), ('false_absent', 50)]); got = collections.Counter(); rows = []
    for cn in pool:
        if all(got[k] >= v for k, v in want.items()): break
        c = caps[cn]; z = np.load(K + '/k1r/' + idx[cn]['rel'], allow_pickle=True); inst = z['inst']; n, H, W = inst.shape
        valid = [k for k in range(32) if float(z['depth'][k].max()) > 0]; ids = [int(x) for x in z['ids']]; labels = [norm(x) for x in z['labels']]
        heads = collections.Counter(head(l) for l in set(labels)); cls = [l for l in sorted(set(labels)) if l in ALLOW and heads[head(l)] == 1]
        if len(cls) < 2: continue
        masks = {l: np.isin(inst, [i for i, x in zip(ids, labels) if x == l]) for l in cls}; share = {l: masks[l].reshape(32, -1).mean(1) for l in cls}
        sha = lambda k: os.path.basename(c['dense_frames'][int(c['anchor_slots'][k])]['path']).split('.')[0]
        uv = lambda yx: [round((yx[1] + 0.5) / W * 1000), round((yx[0] + 0.5) / H * 1000)]
        per = 0
        for _ in range(40):
            if per >= 14: break
            kind = rng.choice([k for k in want if got[k] < want[k]] or ['none'])
            if kind == 'none': break
            l = rng.choice(cls); big = [k for k in valid if share[l][k] >= 0.01]; zero = [k for k in valid if share[l][k] == 0]
            if kind in ('true_point', 'off', 'wrong_name', 'false_absent') and not big: continue
            if kind == 'true_absent' and (not zero or not big): continue
            k = rng.choice(zero if kind == 'true_absent' else big); m = masks[l][k]; row = dict(canonical=cn, frame=k, sha=sha(k), share=float(share[l][k]), type=kind)
            if kind in ('true_point', 'wrong_name'):
                er = m.copy()
                for _e in range(3): er = er & np.roll(er, 1, 0) & np.roll(er, -1, 0) & np.roll(er, 1, 1) & np.roll(er, -1, 1)
                pts = np.argwhere(er)
                if not len(pts): continue
                p = pts[rng.randrange(len(pts))]; row['uv'] = uv(p)
                if kind == 'wrong_name':
                    others = [o for o in cls if o != l and not masks[o][k][p[0], p[1]] and head(o) != head(l)]
                    if not others: continue
                    row['label'] = rng.choice(others); row['true_label'] = l; row['label_visible_in_frame'] = bool(share[row['label']][k] > 0)
                else: row['label'] = l
                row['kind'] = 'point'
            elif kind == 'off':
                any_l = m; dil = m.copy()
                for _e in range(10): dil = dil | np.roll(dil, 1, 0) | np.roll(dil, -1, 0) | np.roll(dil, 1, 1) | np.roll(dil, -1, 1)
                ring = dil & ~m
                for _e in range(3): ring = ring & ~(np.roll(m, _e + 1, 0) | np.roll(m, -_e - 1, 0) | np.roll(m, _e + 1, 1) | np.roll(m, -_e - 1, 1))
                pts = np.argwhere(ring)
                if not len(pts): continue
                p = pts[rng.randrange(len(pts))]; row.update(uv=uv(p), label=l, kind='point')
            else: row.update(label=l, kind='absent')
            row['id'] = 'n' + hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()[:10]
            row['path'] = '%s/%s/%s.png' % (FR, row['sha'][:2], row['sha']); assert os.path.isfile(row['path'])
            rows.append(row); got[kind] += 1; per += 1
    os.makedirs(K + '/v1', exist_ok=True); json.dump(rows, open(K + '/v1/NEARMISS_TRUTH.json', 'w'))
    print('nearmiss rows', len(rows), dict(got), 'captures', len(set(r['canonical'] for r in rows)))
    return rows
def pilot_rows():
    import c2_jobs
    rows, _ = c2_jobs.load_rows(None); out = []
    for r in rows:
        can = r['canonical'] or '%s/%s' % (r['dataset'], r['scene'])
        out.append(dict(id='r%d' % r['i'], canonical=can, path=r['path'], uv=r['uv'], label=r['label'], kind='absent' if r['kind'] == 'gt_absent' else 'point', scene=r['scene']))
    return out
def main():
    out, which, model, effort = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]; chunk = int(sys.argv[5]) if len(sys.argv) > 5 else 24
    effort = None if effort == 'none' else effort; extra = json.loads(os.environ.get('C1_EXTRA', '{}')); mtag = model.split('/')[-1]
    if which == 'nearmiss':
        p = K + '/v1/NEARMISS_TRUTH.json'; rows = json.load(open(p)) if os.path.exists(p) else nearmiss_rows(); tag = 'calibration'
        excl.assert_train(sorted(set(r['canonical'] for r in rows)), label=False)
    else:
        rows = pilot_rows(); tag = 'dev-analysis'
        assert all(excl.reasons(r['canonical']) for r in rows), 'a pilot row outside the protected sets: build it as a train job'
    by = collections.defaultdict(list)
    for r in rows: by[r['canonical']].append(r)
    rng = random.Random('v1c ' + which); n = 0
    with open(out, 'a') as f:
        groups = []
        for cn in sorted(by):
            rs = by[cn][:]; rng.shuffle(rs); groups += [rs[j:j + chunk] for j in range(0, len(rs), chunk)]
        if which == 'nearmiss':
            flat = [r for g in groups for r in g]; groups = [flat[j:j + chunk] for j in range(0, len(flat), chunk)]
        for gi, part in enumerate(groups):
            text = PROMPT.format(n=len(part)); content = [{'text': text}]
            for r in part:
                if r['kind'] == 'absent':
                    content += [{'text': 'Row %s (absent row): kind = "%s"' % (r['id'], r['label'])}, {'image': r['path'], 'max_side': 640}]
                else:
                    content += [{'text': 'Row %s (point row): kind = "%s"' % (r['id'], r['label'])}, {'image': r['path'], 'max_side': 640, 'mark': r['uv']},
                                {'text': 'Row %s close-up' % r['id']}, {'image': crop(r['path'], r['uv'], r['id']), 'max_side': 256}]
            f.write(json.dumps({'id': 'v1c_%s_%03d_%s' % (which, gi, mtag), 'model': model, 'effort': effort, 'max_tokens': 16384, 'extra': extra, 'content': content,
                                'meta': {'tag': tag, 'scenes': sorted(set(r['canonical'] for r in part)), 'set': which, 'rows': [r['id'] for r in part],
                                         'prompt_sha256': hashlib.sha256(PROMPT.encode()).hexdigest()}}) + '\n'); n += 1
    print(which, mtag, 'rows', len(rows), 'tasks', n)
if __name__ == '__main__': main()
