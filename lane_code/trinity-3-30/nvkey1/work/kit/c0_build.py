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
