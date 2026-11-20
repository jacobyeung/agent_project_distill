"""nvkey2 V1 batched-form calibration jobs on K1 TRAINING captures (raster truth at the 32 anchors; rasters in K/k1r, frames in /scratch/jjyeung/k1_frames).
Forms: a = guided names (eligible ground-truth classes plus 3 decoys from the dataset's annotated vocabulary that the capture lacks), returning per kind
the visible frames, a point per visible frame, instances with first frames, and a count; b = blind inventory (no names), up to 40 instances with name,
2 aliases, up to 8 clear frames and a point per listed frame. Truth summaries go to K/v1/truth/<alias>.json; masks stay in the rasters (never sent).
usage: v1_jobs.py OUT.jsonl FORM(a|b) MODEL EFFORT NFRAMES(32|64) [CAPS=c1|<n new clear captures>] [max_side=640]"""
import json, os, sys, random, hashlib, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import excl
K = os.environ.get('NVK', '/scratch/jjyeung/orch_n30/nvkey1/work'); FR = '/scratch/jjyeung/k1_frames'; VIS = 0.002; MAXC = 12
ALLOW = set('''chair table sofa couch bed tv monitor door window cabinet shelf bookshelf desk lamp sink toilet bathtub refrigerator fridge stove oven
microwave washer dishwasher fireplace stool pillow backpack keyboard laptop mirror whiteboard blackboard radiator heater printer plant
picture curtain blinds towel suitcase clock telephone nightstand dresser wardrobe bench armchair counter piano guitar bicycle ladder fan
closet bag box bottle cup shower'''.split()) | set(['trash can', 'trash bin', 'office chair', 'coffee table', 'computer tower', 'ceiling light',
    'washing machine', 'coat hanger', 'computer mouse', 'kitchen cabinet', 'dining table', 'shower curtain', 'file cabinet', 'paper towel dispenser'])
PROMPT_A = ('These are {n} frames sampled in time order from one video of an indoor room. Each image follows its label "Frame k" (k = 1 to {n}).\n'
            'Object kinds to look for: {kinds}. Some of these kinds may not be in the room at all.\n'
            'For each kind give:\n'
            '- "frames": every frame number in which at least one object of that kind is visible, fully or partly (partly visible or partly occluded objects count; '
            'reflections and pictures of objects do not);\n'
            '- "points": for each of those frames, one point on a visible part of an object of that kind (if several are visible, the most visible one) as [x, y] '
            'in 0-1000 coordinates of that frame: x = 0 at the left edge and 1000 at the right edge, y = 0 at the top edge and 1000 at the bottom edge;\n'
            '- "instances": the distinct physical objects of that kind seen anywhere in the video, in order of first appearance, each as {{"first_frame": the first '
            'frame number in which that object is visible}}; an object seen again in a later frame is the same instance;\n'
            '- "count": the number of distinct physical objects of that kind in the video (the length of "instances"); 0 if the kind is not in the room.\n'
            'Reply with one JSON object and nothing else, with an entry for every kind listed: '
            '{{"{k0}": {{"frames": [...], "points": {{"<frame>": [x, y], ...}}, "instances": [{{"first_frame": k}}, ...], "count": n}}, ...}}')
PROMPT_B = ('These are {n} frames sampled in time order from one video of an indoor room. Each image follows its label "Frame k" (k = 1 to {n}).\n'
            'Make an inventory of the distinct physical objects visible in these frames: furniture, appliances, fixtures, and other objects at least the size of a book. '
            'List up to 40 objects (instances), larger and clearer ones first. An object seen in several frames is one instance; two objects of the same kind are two instances.\n'
            'For each instance give:\n'
            '- "name": the short noun phrase most people would use for it;\n'
            '- "aliases": two other names a person might use for it;\n'
            '- "frames": up to 8 frame numbers in which it is clearly visible, spread over the video;\n'
            '- "points": for each of those frames, one point on a visible part of that object as [x, y] in 0-1000 coordinates of that frame: x = 0 at the left edge '
            'and 1000 at the right edge, y = 0 at the top edge and 1000 at the bottom edge.\n'
            'Reply with one JSON object and nothing else: {{"instances": [{{"name": "...", "aliases": ["...", "..."], "frames": [...], "points": {{"<frame>": [x, y], ...}}}}, ...]}}')
def norm(l):
    l = str(l).lower().replace('_', ' ').strip(); return {'tv monitor': 'tv', 'television': 'tv'}.get(l, l)
def head(l):
    h = l.split()[-1]; return h[:-1] if h.endswith('s') and not h.endswith('ss') else h
def load_ctx():
    man = json.load(open(K + '/k1r/geo_k1/stage/K1_MANIFEST.arkit_timing.json')); caps = {c['canonical']: c for c in man['captures']}
    idx = json.load(open(K + '/k1r/k1r_index.json')); vocab = json.load(open(K + '/excl/TEACHER_K1.raw'))['vocab_by_ds']
    return caps, idx, vocab
def truth(canon, caps, idx, vocab, alias):
    c = caps[canon]; assert c.get('k1_split') == 'train' and c.get('split') == 'train', canon; excl.assert_train([canon])
    z = np.load(K + '/k1r/' + idx[canon]['rel'], allow_pickle=True); inst = z['inst']; n, H, W = inst.shape; assert n == 32
    missing = [bool(float(z['depth'][k].max()) <= 0) for k in range(32)]
    ids = [int(x) for x in z['ids']]; labels = [norm(x) for x in z['labels']]; heads = collections.Counter(head(l) for l in set(labels))
    area = float(H * W); cls = []
    for l in sorted(set(labels)):
        if l not in ALLOW or heads[head(l)] > 1: continue
        ii = [i for i, x in zip(ids, labels) if x == l]
        per = {i: [float((inst[k] == i).sum()) / area for k in range(32)] for i in ii}
        share = [float(np.isin(inst[k], ii).sum()) / area for k in range(32)]
        if not any(share[k] >= VIS and not missing[k] for k in range(32)): continue
        vis_inst = {i: [k for k in range(32) if per[i][k] >= VIS and not missing[k]] for i in ii}
        firsts = sorted(v[0] for v in vis_inst.values() if v)
        cls.append(dict(name=l, ids=ii, share=share, count=len(firsts), count_any=sum(1 for i in ii if any(per[i][k] > 0 for k in range(32))),
                        first_frames=firsts, nvis=sum(1 for k in range(32) if share[k] >= VIS and not missing[k])))
    cls.sort(key=lambda t: -t['nvis']); cls = cls[:MAXC]
    ds = canon.split('/')[0]; present = set(labels) | set(head(l) for l in labels)
    pool = sorted(v for v in (norm(x) for x in vocab.get(ds, [])) if v in ALLOW and v not in present and head(v) not in present)
    rng = random.Random('decoy ' + canon); decoys = rng.sample(pool, min(3, len(pool)))
    dense = c['dense_frames']; slots = [int(s) for s in c['anchor_slots']]
    sha = lambda p: os.path.basename(p).split('.')[0]
    t = dict(alias=alias, canonical=canon, dataset=ds, raster=idx[canon]['rel'], raster_sha256=idx[canon]['sha256'], H=H, W=W, missing=missing,
             classes=cls, decoys=decoys, anchors=[sha(dense[s]['path']) for s in slots], dense=[sha(f['path']) for f in dense], anchor_slots=slots)
    os.makedirs(K + '/v1/truth', exist_ok=True); json.dump(t, open(K + '/v1/truth/%s.json' % alias, 'w'))
    return t
def main():
    out, form, model, effort, n = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
    sel = sys.argv[6] if len(sys.argv) > 6 else 'c1'; side = int(sys.argv[7]) if len(sys.argv) > 7 else 640
    effort = None if effort == 'none' else effort; extra = json.loads(os.environ.get('C1_EXTRA', '{}')); tag = model.split('/')[-1]
    caps, idx, vocab = load_ctx(); c1 = json.load(open(K + '/c1/C1_MANIFEST.json'))
    if sel == 'c1': chosen = [(a, v['canonical']) for a, v in sorted(c1.items()) if not excl.reasons(v['canonical'])]
    else:
        used = {v['canonical'] for v in c1.values()}; pool = sorted(cn for cn in idx if cn not in used and not excl.reasons(cn))
        chosen = [('k' + hashlib.sha256(cn.encode()).hexdigest()[:11], cn) for cn in random.Random('v1 new').sample(pool, int(sel))]
    nt = 0
    with open(out, 'a') as f:
        for alias, canon in chosen:
            t = truth(canon, caps, idx, vocab, alias)
            shas = t['anchors'] if n == 32 else t['dense']; assert len(shas) == n, (alias, len(shas))
            if form == 'a':
                kinds = [x['name'] for x in t['classes']] + t['decoys']; random.Random('order %s %s' % (alias, n)).shuffle(kinds)
                text = PROMPT_A.format(n=n, kinds=json.dumps(kinds), k0=kinds[0])
            else:
                kinds = None; text = PROMPT_B.format(n=n)
            content = [{'text': text}]
            for i, s in enumerate(shas):
                p = '%s/%s/%s.png' % (FR, s[:2], s); assert os.path.isfile(p), p
                content += [{'text': 'Frame %d' % (i + 1)}, {'image': p, 'max_side': side}]
            f.write(json.dumps({'id': 'v1%s_%s_%s_f%d' % (form, alias, tag, n), 'model': model, 'effort': effort, 'max_tokens': 32768, 'extra': extra, 'content': content,
                                'meta': {'tag': 'calibration', 'scenes': [canon], 'alias': alias, 'form': form, 'n': n, 'side': side, 'kinds': kinds,
                                         'prompt_sha256': hashlib.sha256(text.encode()).hexdigest(),
                                         'slots': t['anchor_slots'] if n == 64 else list(range(32))}}) + '\n'); nt += 1
    print('form', form, 'model', tag, 'frames', n, 'captures', len(chosen), 'tasks', nt)
if __name__ == '__main__': main()
