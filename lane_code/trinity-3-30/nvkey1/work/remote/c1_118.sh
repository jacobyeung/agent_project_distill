set +x
echo "== host $(hostname -s) $(date -u +%FT%TZ)"; df -h /scratch | tail -1; uptime
L=/scratch/jjyeung/orch_n30/nvkey1; mkdir -p $L/kit $L/c1
cat > $L/kit/c1_build.py <<'PYEOF'
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
PYEOF
PY=/scratch/jjyeung/envs/p1cpu/bin/python; [ -x $PY ] || PY=/scratch/jjyeung/envs/planner_local_v1/bin/python
cd $L && OMP_NUM_THREADS=2 nice -n 10 $PY -B kit/c1_build.py $L/c1 '{"k68b61bbae2e": "arkitscenes/47332192", "kc88e2007abb": "arkitscenes/47331711", "kc2430767aa3": "arkitscenes/47331479", "ka9594e8caae": "arkitscenes/42898745", "kaa310d36055": "arkitscenes/43649382", "kdaaa778983e": "arkitscenes/42899906", "kce989573ccf": "arkitscenes/42897622", "k4c04c58033d": "arkitscenes/44796392", "k521fea161b1": "scannet/scene0452_02", "k01d89b248dc": "scannet/scene0614_02", "k2461c13d2ad": "scannet/scene0204_00", "k2abb9b9bbdf": "scannet/scene0388_00", "k37904b5d65e": "scannet/scene0370_01", "k694f86f6515": "scannet/scene0478_01", "kf54aa2cf5b1": "scannet/scene0505_04", "k912a5fb9af0": "scannet/scene0232_02", "k2eb7fff7537": "scannetpp/302a7f6b67", "k03c5a6666c8": "scannetpp/d82aaa88dc", "kc57e8edfa5c": "scannetpp/ad2d07fd11", "kba4b66ca031": "scannetpp/2c7c10379b", "k3072061a4d5": "scannetpp/79eb3fbc63", "k234381f08ec": "scannetpp/72f527a47c", "k7891d5fc2d3": "scannetpp/abb6639ceb", "k3003f05d0ab": "scannetpp/c178491bc5"}' 2>&1 | tail -30
du -sh $L/c1
echo "== devS1 GT"; for d in /scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt /scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt; do echo "-- $d"; ls $d 2>&1 | head -3; ls $d 2>/dev/null | wc -l; du -sh $d 2>/dev/null; done
f=$(ls /scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/*.npz 2>/dev/null | head -1); [ -n "$f" ] && $PY -c "
import numpy as np, sys; z=np.load(sys.argv[1], allow_pickle=True); print({k: (z[k].shape, z[k].dtype) for k in z.files})" $f
echo "== send c1 to 2-28"
tar cf - -C $L c1 | timeout 300 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'mkdir -p /scratch/jjyeung/orch_n30/nvkey1/work && tar xf - -C /scratch/jjyeung/orch_n30/nvkey1/work && du -sh /scratch/jjyeung/orch_n30/nvkey1/work/c1 && ls /scratch/jjyeung/orch_n30/nvkey1/work/c1 | wc -l'
echo "== done"
