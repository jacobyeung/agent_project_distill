"""Labelling pilot, part 1 (calibration): closed questions with raster truth for K1 TRAINING captures, and their contact sheets.
Runs on trinity-1-18 (nice 10, one process, one thread). Reads the K1 manifest (capture list with k1_split), the rebuilt ground-truth
rasters and the RGB anchors under /scratch/jjyeung/k1_frames. A held-out capture, and any capture whose room holds a held-out capture,
is never opened: only its manifest entry (name, room, split) is read.
usage: python k1_build.py OUT_DIR SHEET_DIR_ON_LABELLER_NODE [captures per dataset=8]
Truth rules (the row builder's rule, record B12_COUNT_APPEARANCE_ROWS_20261116.md): a class is visible in a frame when its raster pixel
share is >= 0.002; it is absent when it has 0 pixels (frames in between are never asked). First-seen = the first sampled frame where the
class is visible. Count = instances of the class that are visible in at least one sampled frame.
Writes OUT/sheets/<alias>_s1..4.jpg, OUT/jobs_k1.json (questions without truth), OUT/key_k1.json (truth), and prints a summary."""
import json, os, sys, hashlib, random, collections
import numpy as np
from PIL import Image, ImageDraw, ImageFont
W = '/scratch/jjyeung/orch_n30'
MAN = W + '/geo_k1/stage/K1_MANIFEST.arkit_timing.json'
RAST = [W + '/gt_build/out/dose_pool/out/t1_gt/gt', W + '/gt_build/out/dose_pool/out/arkit_gt/gt', W + '/gt_build2/out/dose_pool/out/arkit_gt/gt']
OUT = sys.argv[1]; SHEETS_AT = sys.argv[2].rstrip('/'); PER = int(sys.argv[3]) if len(sys.argv) > 3 else 8
VIS = 0.002; NCLS = 8; TW, TH = 496, 372
ALLOW = set('''chair table sofa couch bed tv monitor door window cabinet shelf bookshelf desk lamp sink toilet bathtub refrigerator fridge stove oven
microwave washer dishwasher fireplace stool pillow backpack keyboard laptop mirror whiteboard blackboard radiator heater printer plant
picture curtain blinds towel suitcase clock telephone nightstand dresser wardrobe bench armchair counter piano guitar bicycle ladder fan
closet bag box bottle cup shower'''.split()) | set(['trash can', 'trash bin', 'office chair', 'coffee table', 'computer tower', 'ceiling light',
    'washing machine', 'coat hanger', 'computer mouse', 'kitchen cabinet', 'dining table', 'shower curtain', 'file cabinet', 'paper towel dispenser'])
def norm(l):
    l = str(l).lower().replace('_', ' ').strip()
    return {'tv monitor': 'tv', 'television': 'tv'}.get(l, l)
def head(l):
    h = l.split()[-1]
    return h[:-1] if h.endswith('s') and not h.endswith('ss') else h
os.makedirs(OUT + '/sheets', exist_ok=True)
man = json.load(open(MAN)); caps = man['captures']
held_rooms = set(c['room'] for c in caps if c.get('k1_split') != 'train' or c.get('split') != 'train')
cand = collections.defaultdict(list); skipped = collections.Counter()
for c in caps:
    if c.get('k1_split') != 'train' or c.get('split') != 'train': continue
    if c['room'] in held_rooms: skipped['train capture in a held-out room'] += 1; continue
    name = os.path.basename(c['gt']['path']); path = None
    for d in RAST:
        if os.path.isfile(d + '/' + name): path = d + '/' + name
    if not path: skipped['no rebuilt raster'] += 1; continue
    cand[c['canonical'].split('/')[0]].append((c, path))
print('training captures with a raster, outside held-out rooms:', dict((k, len(v)) for k, v in cand.items()), '| skipped', dict(skipped))
try: font = ImageFont.load_default(size=30)
except TypeError: font = ImageFont.load_default()
def sheets(alias, paths):
    for s in range(4):
        sheet = Image.new('RGB', (4 * TW, 2 * TH), (0, 0, 0)); d = ImageDraw.Draw(sheet)
        for j in range(8):
            k = s * 8 + j; img = Image.open(paths[k]).convert('RGB'); w, h = img.size; sc = min(TW / float(w), TH / float(h))
            im = img.resize((max(1, int(w * sc)), max(1, int(h * sc))), Image.LANCZOS); x, y = (j % 4) * TW, (j // 4) * TH
            sheet.paste(im, (x + (TW - im.size[0]) // 2, y + (TH - im.size[1]) // 2))
            d.rectangle([x, y, x + 150, y + 38], fill=(0, 0, 0)); d.text((x + 6, y + 2), 'frame %d' % (k + 1), fill=(255, 255, 0), font=font)
            d.rectangle([x, y, x + TW - 1, y + TH - 1], outline=(255, 255, 255))
        sheet.save('%s/sheets/%s_s%d.jpg' % (OUT, alias, s + 1), 'JPEG', quality=78)
    return w, h
def build(c, path, rng):
    z = np.load(path, allow_pickle=True); inst = z['inst']; n, H, Wd = inst.shape
    if n != 32 or len(c['anchor_indices']) != 32: return None, 'not 32 frames'
    if 'frame_indices' in z.files and [int(x) for x in z['frame_indices']] != [int(x) for x in c['anchor_indices']]: return None, 'raster grid differs from the anchors'
    fr = [c['dense_frames'][s] for s in c['anchor_slots']]
    if [int(f['index']) for f in fr] != [int(x) for x in c['anchor_indices']]: return None, 'dense frame index differs from the anchors'
    if not all(os.path.isfile(f['path']) for f in fr): return None, 'anchor frame file missing'
    missing = [float(z['depth'][k].max()) <= 0 for k in range(32)]
    ids = [int(x) for x in z['ids']]; labels = [norm(x) for x in z['labels']]
    share = collections.defaultdict(lambda: np.zeros(32))          # instance id -> pixel share per frame
    for k in range(32):
        u, cnt = np.unique(inst[k], return_counts=True)
        for a, b in zip(u, cnt):
            if a >= 0: share[int(a)][k] = b / float(H * Wd)
    heads = collections.Counter(head(l) for l in set(labels))
    cls = {}
    for l in sorted(set(labels)):
        if l not in ALLOW or heads[head(l)] > 1: continue
        ii = [i for i, x in zip(ids, labels) if x == l]; sc = sum(share[i] for i in ii)
        V = [k for k in range(32) if sc[k] >= VIS and not missing[k]]; A = [k for k in range(32) if sc[k] == 0 and not missing[k]]
        if not V: continue
        vis_inst = [i for i in ii if max(share[i][k] for k in range(32) if not missing[k]) >= VIS]
        first = min(V)
        cls[l] = dict(V=V, A=A, sc=sc, count=len(vis_inst), annotated=len(ii), first=first,
                      clean=all(sc[j] == 0 and not missing[j] for j in range(first)), inst_max=[round(float(max(share[i])), 4) for i in ii])
    if len(cls) < 5: return None, 'under 5 eligible classes'
    order = sorted(cls); rng.shuffle(order)
    order.sort(key=lambda l: (0 if cls[l]['count'] >= 2 else 1, 0 if cls[l]['A'] else 1))
    chosen = order[:NCLS]; Q = []; K = {}
    def add(kind, text, fmt, **kw):
        qid = '%s%02d' % (kind[0], 1 + sum(1 for q in Q if q['qid'][0] == kind[0])); Q.append(dict(qid=qid, text=text, format=fmt)); K[qid] = dict(kind=kind, **kw)
    for j, l in enumerate(chosen):
        x = cls[l]; art = 'an' if l[0] in 'aeiou' else 'a'; npos = 2 if j % 2 == 0 else 1
        pos = rng.sample(x['V'], min(npos, len(x['V']))); neg = rng.sample(x['A'], min(3 - len(pos), len(x['A'])))
        if len(pos) + len(neg) < 3: pos += rng.sample([k for k in x['V'] if k not in pos], min(3 - len(pos) - len(neg), len(x['V']) - len(pos)))
        for k in sorted(pos + neg):
            add('visible', 'Is at least one %s visible, fully or partly, in frame %d?' % (l, k + 1), 'yes or no', label=l, frame=k + 1,
                gt='yes' if k in pos else 'no', share=round(float(x['sc'][k]), 4))
    for l in chosen:
        x = cls[l]; art = 'an' if l[0] in 'aeiou' else 'a'
        add('first', 'In which frame, 1 to 32, is %s %s visible for the first time?' % (art, l), 'integer from 1 to 32', label=l, gt=x['first'] + 1, clean=bool(x['clean']),
            share=round(float(x['sc'][x['first']]), 4))
    for l in chosen:
        x = cls[l]
        add('count', 'How many separate objects of the kind "%s" appear across the whole clip? Count each physical object once, even when several frames show it.' % l,
            'integer', label=l, gt=x['count'], annotated=x['annotated'], inst_max=x['inst_max'])
    return (fr, Q, K, missing), None
jobs = collections.OrderedDict(); key = collections.OrderedDict(); rng = random.Random(20261119); tot = collections.Counter(); why = collections.Counter()
for ds in sorted(cand):
    lst = sorted(cand[ds], key=lambda t: t[0]['canonical']); rng.shuffle(lst); done = 0; rooms = set()
    for c, path in lst:
        if done >= PER: break
        if c['room'] in rooms: continue
        r, err = build(c, path, rng)
        if err: why[ds + ': ' + err] += 1; continue
        fr, Q, K, missing = r; alias = 'k' + hashlib.sha256(('pilot k1 ' + c['canonical']).encode()).hexdigest()[:11]
        size = sheets(alias, [f['path'] for f in fr]); rooms.add(c['room']); done += 1
        jobs[alias] = dict(sheets=['%s/%s_s%d.jpg' % (SHEETS_AT, alias, s) for s in (1, 2, 3, 4)], questions=Q)
        for qid, k in K.items(): key[alias + '/' + qid] = dict(k, dataset=ds, capture=c['canonical'], room=c['room'])
        kinds = collections.Counter(k['kind'] for k in K.values()); yes = sum(1 for k in K.values() if k['kind'] == 'visible' and k['gt'] == 'yes')
        for kk, v in kinds.items(): tot[kk] += v
        tot['visible yes'] += yes
        print('ok %s %-11s %-28s frame %dx%d raster %s questions %s yes %d missing frames %d counts %s' % (alias, ds, c['canonical'], size[0], size[1],
              os.path.basename(path)[:24], dict(kinds), yes, sum(missing), [k['gt'] for k in K.values() if k['kind'] == 'count']))
json.dump(jobs, open(OUT + '/jobs_k1.json', 'w'), indent=0); json.dump(key, open(OUT + '/key_k1.json', 'w'), indent=0)
print('captures', len(jobs), 'questions', dict(tot), '| captures passed over', dict(why))
print('sheet bytes', sum(os.path.getsize(OUT + '/sheets/' + f) for f in os.listdir(OUT + '/sheets')))
