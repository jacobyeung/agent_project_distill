"""nvkey1 C1/bake-off calibration truth for K1 TRAINING captures (runs on trinity-1-18; reads the K1 manifest, rebuilt rasters, k1_frames).
For each capture: every eligible annotated class (furniture-scale allow list, no sibling head noun), its pixel share and mask in each of the 32 anchor
frames, the anchor frame shas and the dense frame shas (with anchor slots). Writes OUT/<alias>.npz and OUT/C1_MANIFEST.json. Held-out rooms never opened."""
import json, os, sys, hashlib, collections
import numpy as np
W = '/scratch/jjyeung/orch_n30'
MAN = W + '/geo_k1/stage/K1_MANIFEST.arkit_timing.json'
RAST = [W + '/gt_build/out/dose_pool/out/t1_gt/gt', W + '/gt_build/out/dose_pool/out/arkit_gt/gt', W + '/gt_build2/out/dose_pool/out/arkit_gt/gt']
OUT = sys.argv[1]; CAPS = json.loads(sys.argv[2]); MAXC = 12; VIS = 0.002
ALLOW = set('''chair table sofa couch bed tv monitor door window cabinet shelf bookshelf desk lamp sink toilet bathtub refrigerator fridge stove oven
microwave washer dishwasher fireplace stool pillow backpack keyboard laptop mirror whiteboard blackboard radiator heater printer plant
picture curtain blinds towel suitcase clock telephone nightstand dresser wardrobe bench armchair counter piano guitar bicycle ladder fan
closet bag box bottle cup shower'''.split()) | set(['trash can', 'trash bin', 'office chair', 'coffee table', 'computer tower', 'ceiling light',
    'washing machine', 'coat hanger', 'computer mouse', 'kitchen cabinet', 'dining table', 'shower curtain', 'file cabinet', 'paper towel dispenser'])
def norm(l):
    l = str(l).lower().replace('_', ' ').strip(); return {'tv monitor': 'tv', 'television': 'tv'}.get(l, l)
def head(l):
    h = l.split()[-1]; return h[:-1] if h.endswith('s') and not h.endswith('ss') else h
os.makedirs(OUT, exist_ok=True)
man = json.load(open(MAN)); caps = {c['canonical']: c for c in man['captures']}
held_rooms = set(c['room'] for c in man['captures'] if c.get('k1_split') != 'train' or c.get('split') != 'train')
summary = collections.OrderedDict()
for alias, canon in CAPS.items():
    c = caps[canon]
    assert c.get('k1_split') == 'train' and c.get('split') == 'train' and c['room'] not in held_rooms, canon
    name = os.path.basename(c['gt']['path']); path = [d + '/' + name for d in RAST if os.path.isfile(d + '/' + name)][0]
    z = np.load(path, allow_pickle=True); inst = z['inst']; n, H, Wd = inst.shape
    assert n == 32 and [int(x) for x in z['frame_indices']] == [int(x) for x in c['anchor_indices']] if 'frame_indices' in z.files else n == 32
    dense = c['dense_frames']; slots = [int(s) for s in c['anchor_slots']]
    assert [int(dense[s]['index']) for s in slots] == [int(x) for x in c['anchor_indices']]
    sha = lambda p: os.path.basename(p).split('.')[0]
    missing = np.array([float(z['depth'][k].max()) <= 0 for k in range(32)])
    ids = [int(x) for x in z['ids']]; labels = [norm(x) for x in z['labels']]
    heads = collections.Counter(head(l) for l in set(labels))
    cls = []
    for l in sorted(set(labels)):
        if l not in ALLOW or heads[head(l)] > 1: continue
        ii = [i for i, x in zip(ids, labels) if x == l]
        m = np.isin(inst, ii); sc = m.reshape(32, -1).mean(1)
        if not any(sc[k] >= VIS and not missing[k] for k in range(32)): continue
        cls.append((l, m, sc, len(ii)))
    cls.sort(key=lambda t: -float((t[2] >= VIS).sum())); cls = cls[:MAXC]
    np.savez_compressed(OUT + '/' + alias + '.npz', classes=np.array([t[0] for t in cls]), share=np.stack([t[2] for t in cls]).astype(np.float32),
                        mask=np.packbits(np.stack([t[1] for t in cls]), axis=-1), shape=np.array([H, Wd]), missing=missing,
                        annotated=np.array([t[3] for t in cls]))
    summary[alias] = dict(canonical=canon, room=c['room'], dataset=canon.split('/')[0], raster=os.path.basename(path), H=H, W=Wd,
                          anchors=[sha(dense[s]['path']) for s in slots], dense=[sha(f['path']) for f in dense], anchor_slots=slots,
                          dense_indices=[int(f['index']) for f in dense], classes=[t[0] for t in cls], missing=int(missing.sum()))
    print('ok', alias, canon, 'dense', len(dense), 'classes', len(cls), 'raster', H, Wd, 'missing', int(missing.sum()))
json.dump(summary, open(OUT + '/C1_MANIFEST.json', 'w'), indent=0)
print('captures', len(summary), 'classes', sum(len(v['classes']) for v in summary.values()))
