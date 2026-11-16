"""K1 presence probe, CPU prep: captures, GT per-frame category visibility, scored categories, held-out items.
Reads only: K1 manifest (arkit_timing), K1 GT rasters (sha-checked), K1 frames. Writes out/prep/."""
import hashlib, json, random, sys
from collections import defaultdict
from pathlib import Path
import numpy as np

MANIFEST = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json')
OUT = Path('/scratch/jjyeung/orch_n30/b11_presence/out/prep')
FLOOR = 39          # raster pixels at half resolution = 154 px at 640x480 (GT_CEILING ladder floor)
MAX_CATS = 14       # scored categories per capture
STOP = {'wall', 'floor', 'ceiling', 'object', 'remove', 'doorframe', 'door frame', 'window frame', 'windowsill',
        'window sill', 'split', 'otherprop', 'otherfurniture', 'otherstructure', 'unknown', 'structure', 'beam',
        'pipe', 'column', 'pillar', 'stair', 'stairs', 'rail', 'railing', 'ceiling beam', 'ledge', 'wall cabinet frame'}
APPEAR_Q = 'What will be the first-time appearance order of the following categories in the video: {}?'
COUNT_Q = 'How many {}(s) are in this room?'


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def rng_for(*parts):
    return random.Random(int(hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()[:16], 16))


def first_seen(vis, valid):
    """1-based first anchor with visibility; 33 = never visible. None if an invalid frame precedes it."""
    for k in range(32):
        if not valid[k]:
            return None
        if vis[k]:
            return k + 1
    return 33


def capture_record(c):
    gt = c['gt']
    data = Path(gt['path']).read_bytes()
    assert hashlib.sha256(data).hexdigest() == gt['sha256'], 'GT hash mismatch ' + c['canonical']
    import io
    z = np.load(io.BytesIO(data), allow_pickle=False)
    inst, ids, labels, valid = z['inst'], z['ids'].tolist(), [str(x) for x in z['labels'].tolist()], z['valid'].astype(bool)
    assert inst.shape[0] == 32 and list(z['frame_indices']) == list(c['anchor_indices'])
    si = c['model_row']['student_input']
    assert si['frame_indices'] == list(c['anchor_indices']) and len(si['frames']) == 32
    cats = defaultdict(list)
    for i, lab in zip(ids, labels):
        name = lab.strip().lower()
        if name and name not in STOP:
            cats[name].append(i)
    counts = np.stack([np.bincount((inst[k] + 1).ravel(), minlength=max(ids) + 2) for k in range(32)])  # [32, max_id+2]
    percat = {}
    for name, inst_ids in sorted(cats.items()):
        px = counts[:, [i + 1 for i in inst_ids]]                     # [32, n_inst]
        vis_inst = px >= FLOOR
        any_inst = px >= 1
        vis = vis_inst.any(1)
        percat[name] = dict(instances=len(inst_ids), pixels=px.sum(1).tolist(), visible=vis.astype(int).tolist(),
                            visible_any=any_inst.any(1).astype(int).tolist(),
                            first_seen=first_seen(vis, valid), first_seen_any=first_seen(any_inst.any(1), valid),
                            count_visible=int(vis_inst.any(0).sum()),
                            inst_first=[first_seen(vis_inst[:, j], valid) for j in range(len(inst_ids))])
    return dict(canonical=c['canonical'], room=c['room'], split=c['k1_split'], dataset=c['canonical'].split('/')[0],
                frames=[f['path'] for f in si['frames']], frame_sha256=[f['sha256'] for f in si['frames']],
                frame_indices=si['frame_indices'], fps=si['fps'], total_num_frames=si['total_num_frames'],
                valid=valid.astype(int).tolist(), gt_sha256=gt['sha256'], categories=percat)


def make_items(r):
    rnd = rng_for('items', r['canonical'])
    cats = r['categories']
    single = sorted(n for n, v in cats.items() if v['instances'] == 1 and v['first_seen'] not in (None, 33))
    items = []
    for t in range(6):
        pick = []
        for _ in range(50):
            pool = list(single); rnd.shuffle(pool)
            pick = []
            for n in pool:
                if cats[n]['first_seen'] not in [cats[p]['first_seen'] for p in pick]:
                    pick.append(n)
                if len(pick) == 4:
                    break
            if len(pick) == 4 and not any(sorted(pick) == i['objects'] for i in items):
                break
            pick = []
        if len(pick) < 4:
            break
        truth = sorted(pick, key=lambda n: cats[n]['first_seen'])
        perms = {tuple(truth)}
        while len(perms) < 4:
            p = pick[:]; rnd.shuffle(p); perms.add(tuple(p))
        opts = sorted(perms); rnd.shuffle(opts)
        letters = 'ABCD'
        ans = letters[opts.index(tuple(truth))]
        items.append(dict(id=f"k1app:{r['canonical']}:{t}", type='obj_appearance_order', capture=r['canonical'],
                          room=r['room'], split=r['split'], objects=sorted(pick),
                          question=APPEAR_Q.format(', '.join(sorted(pick))),
                          options=[f'{letters[i]}. ' + ', '.join(o) for i, o in enumerate(opts)],
                          option_orders=[list(o) for o in opts], answer=ans, truth_order=truth,
                          truth_first_seen={n: cats[n]['first_seen'] for n in pick}))
    multi = sorted(n for n, v in cats.items() if v['instances'] >= 2 and v['count_visible'] >= 2
                   and all(f is not None for f in v['inst_first']))
    rnd.shuffle(multi)
    for t, n in enumerate(multi[:2]):
        items.append(dict(id=f"k1cnt:{r['canonical']}:{t}", type='object_counting', capture=r['canonical'],
                          room=r['room'], split=r['split'], objects=[n], question=COUNT_Q.format(n), options=[],
                          answer=cats[n]['count_visible'], instances_in_room=cats[n]['instances']))
    return items


def scored_categories(r, items):
    rnd = rng_for('cats', r['canonical'])
    need = []
    for it in items:
        for n in it['objects']:
            if n not in need:
                need.append(n)
    cats = r['categories']
    seen = sorted(n for n, v in cats.items() if n not in need and v['first_seen'] not in (None, 33))
    never = sorted(n for n, v in cats.items() if n not in need and v['first_seen'] == 33)
    rnd.shuffle(seen); rnd.shuffle(never)
    out = need + never[:2]
    out += seen[:max(0, MAX_CATS - len(out))]
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    m = json.loads(MANIFEST.read_text())
    caps, items, missing = [], [], []
    for c in m['captures']:
        if not (c.get('gt') and Path(c['gt']['path']).is_file()):
            missing.append(c['canonical']); continue
        r = capture_record(c)
        its = make_items(r)
        r['scored'] = scored_categories(r, its)
        caps.append(r); items.extend(its)
    assert len(caps) == 296, len(caps)
    tr = {c['room'] for c in caps if c['split'] == 'train'}; ho = {c['room'] for c in caps if c['split'] == 'heldout'}
    assert not tr & ho
    with open(OUT / 'CAPTURES.jsonl', 'w') as f:
        for r in caps:
            f.write(json.dumps(r, sort_keys=True) + '\n')
    with open(OUT / 'ITEMS.jsonl', 'w') as f:
        for it in items:
            f.write(json.dumps(it, sort_keys=True) + '\n')
    summ = dict(captures=len(caps), missing=missing, floor_px=FLOOR, max_cats=MAX_CATS,
                train_captures=sum(c['split'] == 'train' for c in caps), heldout_captures=sum(c['split'] == 'heldout' for c in caps),
                scored_pairs=sum(len(c['scored']) for c in caps),
                scored_pairs_heldout=sum(len(c['scored']) for c in caps if c['split'] == 'heldout'),
                items={f'{t}/{s}': sum(1 for i in items if i['type'] == t and i['split'] == s)
                       for t in ('obj_appearance_order', 'object_counting') for s in ('train', 'heldout')},
                manifest_sha256=sha(MANIFEST))
    (OUT / 'PREP_SUMMARY.json').write_text(json.dumps(summ, indent=1) + '\n')
    print(json.dumps(summ))


if __name__ == '__main__':
    main()
