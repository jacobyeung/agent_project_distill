K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1
cat > $K/kit/v6_jobs.py <<'PYEOF'
"""nvkey2 V6 open-vocabulary inventory, form v2 (consumer spec O2, O5, O6, O10), on K1 TRAINING captures at the 32 anchors.
Primary (one family): named kinds (at most 8 ground-truth classes chosen by sha order), 15 check kinds (frozen list, never chosen by the labeller), and a
blind inventory of up to 40 other instances. States per anchor: L (5% of the frame or more), M (1-5%), S (visible under 1%, cut off, mostly hidden or
unsure), A (not visible); points only on L and M frames. Verifier (second family, chained): the same frames with the named kinds and the primary's
inventory names with counts (no points, no states), plus the check kinds for states only; it returns its own states and points, rejects and missed objects.
usage: v6_jobs.py lists                                     (freeze K/v6/R3_SIBLINGS.json and K/v6/CHECK_VOCAB.json; prints their sha256)
       v6_jobs.py primary OUT.jsonl MODEL EFFORT SELECTION   (SELECTION = first30 | rest | file.json of canonicals)
       v6_jobs.py chain PRIMARY_OUT.jsonl VERIFIER_QUEUE.jsonl MODEL EFFORT   (appends one verifier task per new primary result)"""
import json, os, sys, random, hashlib, collections, sqlite3, re
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import excl
K = os.environ.get('NVK', '/scratch/jjyeung/orch_n30/nvkey1/work'); FR = '/scratch/jjyeung/k1_frames'; V6 = K + '/v6'; FORM = 'v6-form-v2'
STORE = '/scratch/jjyeung/orch_n30/fb_pack/point/out/rows_pointing_locate.sqlite'
R3 = [['desk', 'table'], ['door', 'window'], ['cooktop', 'oven', 'stove'], ['cabinet', 'storage cabinet'], ['monitor', 'computer monitor', 'tv'],
      ['chair', 'seat', 'stool', 'office chair', 'armchair'], ['bookshelf', 'shelf', 'bookcase'], ['sofa', 'couch', 'armchair']]
STRUCT = {'wall', 'floor', 'ceiling', 'object', 'objects', 'otherfurniture', 'otherprop', 'otherstructure', 'unknown', 'misc', 'structure', 'doorframe', 'beam', 'pipe', 'column'}
ALLOW = set('''chair table sofa couch bed tv monitor door window cabinet shelf bookshelf desk lamp sink toilet bathtub refrigerator fridge stove oven
microwave washer dishwasher fireplace stool pillow backpack keyboard laptop mirror whiteboard blackboard radiator heater printer plant
picture curtain blinds towel suitcase clock telephone nightstand dresser wardrobe bench armchair counter piano guitar bicycle ladder fan
closet bag box bottle cup shower'''.split()) | set(['trash can', 'trash bin', 'office chair', 'coffee table', 'computer tower', 'ceiling light',
    'washing machine', 'coat hanger', 'computer mouse', 'kitchen cabinet', 'dining table', 'shower curtain', 'file cabinet', 'paper towel dispenser'])
STATES = ('Size states: for an object in a frame write L if it is visible and covers 5% of the frame or more, M if it is visible and covers 1% to 5%, '
          'S if it is visible but covers under 1%, is cut off at the frame edge, is mostly hidden, or you are unsure, and A if it is not visible in that frame. '
          'A "states" value is a string of exactly 32 characters from L, M, S, A, one per frame in order (frame 1 first).\n'
          'Points are [x, y] in 0-1000 coordinates of that frame: x = 0 at the left edge and 1000 at the right edge, y = 0 at the top edge and 1000 at the bottom edge. '
          'Give points only for frames whose state is L or M.\n')
HEAD = 'These are 32 frames sampled in time order from one video of an indoor room. Each image follows its label "Frame k" (k = 1 to 32).\n'
PRIMARY = (HEAD + STATES +
           'Task 1, named kinds: {named}. For each kind give "states" (the state of the most visible object of that kind in each frame) and "points" '
           '(for every L or M frame, one point on a visible part of that object).\n'
           'Task 2, check kinds: {check}. Some of these may be in the room and some may not. For each give "states" only.\n'
           'Task 3, inventory: list up to 40 other distinct physical objects visible in these frames (furniture, appliances, fixtures, and objects at least the size '
           'of a book) that are not of the named kinds. An object seen in several frames is one instance; two objects of the same kind are two instances. For each give '
           '"name" (a singular count noun), "aliases" (two other names), "look_alike" (a kind of object it could be mistaken for), "one_object" (true if it is one '
           'physical object), "part_of_larger" (true if it is part of a larger object), "group" (true if it is several objects named as one), "states" and "points" '
           '(on up to 12 of its L or M frames, spread over the video).\n'
           'Reply with one JSON object and nothing else: {{"named": {{"<kind>": {{"states": "...", "points": {{"<frame>": [x, y], ...}}}}, ...}}, '
           '"check": {{"<kind>": {{"states": "..."}}, ...}}, "inventory": [{{"name": "...", "aliases": ["...", "..."], "look_alike": "...", "one_object": true, '
           '"part_of_larger": false, "group": false, "states": "...", "points": {{"<frame>": [x, y], ...}}}}, ...]}}')
VERIFIER = (HEAD + STATES +
            'Another annotator listed these kinds of objects in this video, with how many distinct objects of each kind it saw: {listed}.\n'
            'For each listed kind give "states" (the state of the most visible object of that kind in each frame) and "points" (for every L or M frame, one point '
            'on a visible part of that object). Then give "rejects": the listed kinds you do not see anywhere in the video, and "missed": other distinct physical '
            'objects (furniture, appliances, fixtures, objects at least the size of a book) that are not of any listed kind, each with "name", "aliases", "states" '
            'and "points" (on up to 12 of its L or M frames).\n'
            'Check kinds, states only (no points): {check}.\n'
            'Reply with one JSON object and nothing else: {{"kinds": {{"<kind>": {{"states": "...", "points": {{"<frame>": [x, y], ...}}}}, ...}}, '
            '"check": {{"<kind>": {{"states": "..."}}, ...}}, "rejects": ["..."], "missed": [{{"name": "...", "aliases": ["...", "..."], "states": "...", '
            '"points": {{"<frame>": [x, y], ...}}}}, ...]}}')
def norm(l):
    l = str(l).lower().replace('_', ' ').strip(); return {'tv monitor': 'tv', 'television': 'tv'}.get(l, l)
def head(l):
    h = l.split()[-1] if l.split() else l; return h[:-1] if h.endswith('s') and not h.endswith('ss') else h
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def lists():
    os.makedirs(V6, exist_ok=True)
    vocab = json.load(open(K + '/excl/TEACHER_K1.raw'))['vocab_by_ds']
    ds = {d: sorted(set(norm(x) for x in v) - STRUCT) for d, v in vocab.items()}
    out = {'R3_SIBLINGS.json': {'form': FORM, 'sets': R3}, 'CHECK_VOCAB.json': {'form': FORM, 'source': 'TEACHER_K1.raw vocab_by_ds (4d4736cf), training vocabularies only', 'datasets': ds,
           'open': sorted(set(x for v in ds.values() for x in v))}}
    for name, v in out.items():
        p = '%s/%s' % (V6, name)
        if not os.path.exists(p): open(p, 'w').write(json.dumps(v, indent=0, sort_keys=True))
        print(name, sha(open(p).read()))
def siblings(l):
    s = {l, head(l)}
    for g in json.load(open(V6 + '/R3_SIBLINGS.json'))['sets']:
        if l in g or head(l) in g: s.update(g); s.update(head(x) for x in g)
    return s
def capture_truth(cn, caps, idx):
    c = caps[cn]; assert c.get('k1_split') == 'train' and c.get('split') == 'train', cn; excl.assert_train([cn])
    z = np.load(K + '/k1r/' + idx[cn]['rel'], allow_pickle=True); inst = z['inst']; n, H, W = inst.shape
    valid = [k for k in range(32) if float(z['depth'][k].max()) > 0]; ids = [int(x) for x in z['ids']]; labels = [norm(x) for x in z['labels']]
    big = sorted(set(l for i, l in zip(ids, labels) if l not in STRUCT and any(float((inst[k] == i).sum()) / (H * W) >= 0.01 for k in valid)))
    heads = collections.Counter(head(l) for l in set(labels))
    pool = [l for l in big if l in ALLOW and heads[head(l)] == 1]
    return c, pool, set(labels), big
def build_primary(out, model, effort, selection):
    man = json.load(open(K + '/k1r/geo_k1/stage/K1_MANIFEST.arkit_timing.json')); caps = {c['canonical']: c for c in man['captures']}
    idx = json.load(open(K + '/k1r/k1r_index.json')); c1 = {v['canonical'] for v in json.load(open(K + '/c1/C1_MANIFEST.json')).values()}
    cv = json.load(open(V6 + '/CHECK_VOCAB.json'))
    clear = sorted(cn for cn in idx if cn not in c1 and not excl.reasons(cn))
    if selection in ('first30', 'rest'):
        con = sqlite3.connect('file:%s?mode=ro' % STORE, uri=True); prooms = set()
        for (s,) in con.execute('select row from rows'):
            d = json.loads(s); can = (d.get('provenance') or {}).get('canonical_scene')
            if can and '/' in can:
                try: prooms.add(excl.room(can))
                except Exception: pass
        order = sorted(clear, key=lambda x: sha('v6 ' + x)); pr = [cn for cn in order if excl.room(cn) in prooms]; first = []
        for dsn in ('arkitscenes', 'scannet', 'scannetpp'):
            first += ([cn for cn in pr if cn.startswith(dsn + '/')] + [cn for cn in order if cn.startswith(dsn + '/') and cn not in pr])[:10]
        first = [cn for cn in pr if cn in first] + [cn for cn in first if cn not in pr]
        if not os.path.exists(V6 + '/FIRST30.json'): json.dump({'form': FORM, 'rule': '10 per dataset by sha256("v6 " + capture) order, rooms holding pointing rows first; clear of excl.py and of the V1 calibration captures', 'captures': first}, open(V6 + '/FIRST30.json', 'w'), indent=0)
        first = json.load(open(V6 + '/FIRST30.json'))['captures']
        chosen = first if selection == 'first30' else [cn for cn in clear if cn not in set(first)]
    else: chosen = json.load(open(selection))
    effort = None if effort == 'none' else effort; extra = json.loads(os.environ.get('C1_EXTRA', '{}')); mtag = model.split('/')[-1]; n = 0
    with open(out, 'a') as f:
        for cn in chosen:
            c, pool, labels, big = capture_truth(cn, caps, idx)
            named = sorted(pool, key=lambda l: sha(cn + ' ' + l))[:8]
            sib = set().union(*[siblings(l) for l in labels]) if labels else set()
            rng = random.Random('check ' + cn); dsv = cv['datasets'].get(cn.split('/')[0], [])
            absent_ann = [x for x in dsv if x not in labels and x not in sib and head(x) not in sib]; rng.shuffle(absent_ann)
            omitted = [l for l in big if l not in named and not (siblings(l) & set(named))]; rng.shuffle(omitted)
            openv = [x for x in cv['open'] if x not in dsv and x not in sib and head(x) not in sib and x not in STRUCT]; rng.shuffle(openv)
            check = absent_ann[:5] + omitted[:3]; check += [x for x in openv if x not in check][:15 - len(check)]; rng.shuffle(check)
            ctype = {x: ('absent_annotated' if x in absent_ann[:5] else ('present_omitted' if x in omitted[:3] else 'open')) for x in check}
            text = PRIMARY.format(named=json.dumps(named), check=json.dumps(check)); content = [{'text': text}]
            dense = c['dense_frames']; slots = [int(s) for s in c['anchor_slots']]; frames = []
            for k, s in enumerate(slots):
                fs = os.path.basename(dense[s]['path']).split('.')[0]; p = '%s/%s/%s.png' % (FR, fs[:2], fs); assert os.path.isfile(p), p
                content += [{'text': 'Frame %d' % (k + 1)}, {'image': p, 'max_side': 640}]; frames.append({'sha256': fs, 'source_index': int(dense[s]['index'])})
            f.write(json.dumps({'id': 'v6p_%s_%s' % (sha(cn)[:12], mtag), 'model': model, 'effort': effort, 'max_tokens': 32768, 'extra': extra, 'content': content,
                                'meta': {'tag': 'train', 'scenes': [cn], 'form': FORM, 'role': 'primary', 'canonical': cn, 'named': named, 'check': check, 'check_type': ctype,
                                         'frames': frames, 'prompt_sha256': sha(PRIMARY), 'r3_sha256': sha(open(V6 + '/R3_SIBLINGS.json').read()),
                                         'check_vocab_sha256': sha(open(V6 + '/CHECK_VOCAB.json').read())}}) + '\n'); n += 1
    print('v6 primary', mtag, 'captures', len(chosen), 'tasks', n, 'clear pool', len(clear))
def parse(t):
    if not t: return None
    t = t.strip(); t = re.sub(r'^```(json)?', '', t).strip(); t = re.sub(r'```$', '', t).strip()
    for cand in (t, t[t.find('{'):t.rfind('}') + 1]):
        for fix in (lambda x: x, lambda x: re.sub(r',\s*([}\]])', r'\1', x)):
            try: return json.loads(fix(cand))
            except Exception: pass
    return None
def chain(pout, vq, model, effort):
    done = set()
    if os.path.exists(vq):
        for l in open(vq): done.add(json.loads(l)['meta']['primary_id'])
    effort = None if effort == 'none' else effort; extra = json.loads(os.environ.get('C1_EXTRA', '{}')); mtag = model.split('/')[-1]; n = 0
    if not os.path.exists(pout): return 0
    old = open(vq).read() if os.path.exists(vq) else ''; tmp = os.path.join(os.path.dirname(vq), '.' + os.path.basename(vq) + '.tmp')
    with open(tmp, 'w') as f:
        f.write(old)
        for l in open(pout):
            r = json.loads(l)
            if r['id'] in done: continue
            m = r['meta']; d = parse(r['text'])
            inv = [x for x in ((d or {}).get('inventory') or []) if isinstance(x, dict) and x.get('name')] if isinstance(d, dict) else []
            cnt = collections.Counter(norm(x['name']) for x in inv)
            listed = [(k, None) for k in m['named']] + [(k, v) for k, v in sorted(cnt.items()) if k not in m['named']]
            ltxt = ', '.join('%s (%s)' % (k, 'named' if v is None else v) for k, v in listed)
            text = VERIFIER.format(listed=ltxt, check=json.dumps(m['check'])); content = [{'text': text}]
            for k, fr in enumerate(m['frames']):
                p = '%s/%s/%s.png' % (FR, fr['sha256'][:2], fr['sha256']); content += [{'text': 'Frame %d' % (k + 1)}, {'image': p, 'max_side': 640}]
            meta = dict(m, role='verifier', primary_id=r['id'], primary_parsed=d is not None, listed=[k for k, v in listed], counts=dict(cnt), prompt_sha256=sha(VERIFIER))
            f.write(json.dumps({'id': 'v6v_%s_%s' % (sha(m['canonical'])[:12], mtag), 'model': model, 'effort': effort, 'max_tokens': 32768, 'extra': extra,
                                'content': content, 'meta': meta}) + '\n'); n += 1
    if n: os.replace(tmp, vq)
    return n
if __name__ == '__main__':
    a = sys.argv[1]
    if a == 'lists': lists()
    elif a == 'primary': build_primary(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    elif a == 'chain': print('chained', chain(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]))
PYEOF
P=/scratch/jjyeung/envs/p1cpu/bin/python
$P -B kit/v6_jobs.py primary queue/.45.tmp gcp/google/gemini-4-argon high first30 && $P -B - <<'PY'
import json, os
old = [json.loads(l) for l in open('queue/45_v6p30.jsonl')]; new = [json.loads(l) for l in open('queue/.45.tmp')]
ids = {t['id'] for t in old}; assert all(t['id'] in {x['id'] for x in new} for t in old), 'old tasks missing'
out = old + [t for t in new if t['id'] not in ids]
open('queue/.45b.tmp', 'w').write(''.join(json.dumps(t) + '\n' for t in out)); os.replace('queue/.45b.tmp', 'queue/45_v6p30.jsonl')
os.rename('queue/.45.tmp', 'v6/.45_first_build.unused')
import collections; print('v6p tasks', len(out), collections.Counter(t['meta']['canonical'].split('/')[0] for t in out))
PY
sha256sum v6/FIRST30.json; tail -3 runner.log; cat meter/METER.json
