"""Hand spot check of 20 kit object-frames: raw RLE + GT npz, own resampling, no kit/sb_kbox4 mask code."""
import hashlib, json, random
import numpy as np

KIT = '/scratch/jjyeung/orch_n30/sb_maskfail/out/MASKFAIL.json'
pin = json.load(open('/scratch/jjyeung/orch_n30/sb_kbox4/pinned_train.json'))
caps = {c['canonical']: c for c in pin['captures']}
recs = json.load(open(KIT))['records']
seen, uniq = set(), []
for r in recs:
    k = (r['capture'], r['object'], r['frame'])
    if r['valid'] and r['visible'] and k not in seen:
        seen.add(k); uniq.append(r)
rng = random.Random(20261119)
pick = []
for ds in ['arkitscenes', 'scannet', 'scannetpp']:
    pool = [r for r in uniq if r['dataset'] == ds]
    served = [r for r in pool if r['served_area'] > 0]
    pick += rng.sample(served, 5) + rng.sample([r for r in pool if r['served_area'] == 0], 1)
pick += rng.sample([r for r in uniq if r['dataset'] == 'scannetpp' and r['served_area'] > 0 and r['share'] < .01], 2)


def digest(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, allow_nan=False).encode()).hexdigest()


def decode(rle):
    h, w = rle['size']; counts = np.asarray(rle['counts'], np.int64)
    return np.repeat(np.arange(len(counts)) % 2 == 1, counts).reshape((h, w), order='F')


def nearest(m, shape):
    """Centre-aligned nearest-neighbour resample."""
    h, w = m.shape; H, W = shape
    ys = np.minimum(((np.arange(H) + .5) * h / H).astype(int), h - 1)
    xs = np.minimum(((np.arange(W) + .5) * w / W).astype(int), w - 1)
    return m[ys][:, xs]


def iou(a, b):
    u = np.count_nonzero(a | b)
    return np.count_nonzero(a & b) / u if u else None


out = []
for r in pick:
    c = caps[r['capture']]; key = digest(c['canonical'])[:16]
    cache = json.load(open(f'/scratch/jjyeung/k1/run_convert_2/{key}/candidates.json'))
    z = np.load(c['gt']['path'], allow_pickle=False)
    inst = z['inst'] if 'inst' in z.files else z['instances']
    tgt_native = inst[r['frame'] - 1] == r['instance']
    canvas = (240, 320)
    tgt_canvas = nearest(tgt_native, canvas)
    rec = cache['frames'][str(r['frame'] - 1)]['phrases'].get(r['object'])
    pool = []
    if rec is not None:
        ent = [p for p in rec.get('instances', []) if p.get('source_prompt', r['object']) == r['object']]
        pres = float(ent[0].get('source_presence', rec['presence'])) if ent else float(rec['presence'])
        ent = [p for p in sorted(ent, key=lambda p: -float(p['score'])) if float(p['score']) * pres >= .05][:30]
        pool = [decode(p['mask']) for p in ent]
    k = r['selected_proposal_index']
    served_native = pool[k] if k is not None else None
    sc = nearest(served_native, canvas) if served_native is not None else np.zeros(canvas, bool)
    sn = nearest(served_native, tgt_native.shape) if served_native is not None else np.zeros(tgt_native.shape, bool)
    hand_canvas = iou(sc, tgt_canvas) or 0.
    hand_native = iou(sn, tgt_native) or 0.
    pool_best = max([iou(nearest(p, canvas), tgt_canvas) or 0. for p in pool], default=0.)
    out.append(dict(capture=r['capture'], object=r['object'], frame=r['frame'], instance=r['instance'],
                    gt_shape=list(tgt_native.shape), sam_shape=list(served_native.shape) if served_native is not None else None,
                    kit_iou=round(r['iou'], 4), hand_iou_canvas=round(hand_canvas, 4), hand_iou_gtnative=round(hand_native, 4),
                    kit_share=round(r['share'], 5), hand_share=round(float(tgt_native.mean()), 5),
                    kit_pool_best=round(r['deployed_best_iou'], 4), hand_pool_best=round(pool_best, 4),
                    kit_kind=r['failure_kind'], served_area_canvas=int(sc.sum()), kit_served_area=r['served_area']))
json.dump(out, open('/scratch/jjyeung/orch_n30/sb_mfrev/SPOTCHECK_20.json', 'w'), indent=1)
for o in out:
    print(o['capture'], o['object'], o['frame'], o['gt_shape'], o['sam_shape'], 'iou kit/hand/native', o['kit_iou'], o['hand_iou_canvas'],
          o['hand_iou_gtnative'], 'share', o['kit_share'], o['hand_share'], 'pool', o['kit_pool_best'], o['hand_pool_best'], o['kit_kind'],
          o['kit_served_area'], o['served_area_canvas'])
d1 = [abs(o['kit_iou'] - o['hand_iou_canvas']) for o in out]; d2 = [abs(o['kit_iou'] - o['hand_iou_gtnative']) for o in out]
print('n', len(out), 'max|kit-hand canvas|', max(d1), 'max|kit-hand native|', max(d2), 'share max diff', max(abs(o['kit_share'] - o['hand_share']) for o in out))
