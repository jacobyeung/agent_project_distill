"""nv_orch1 V7 queue builder, form v2 (nvkey2's V6 templates via forms_v2.py). Clip rule and order as build_v7.py (O1, O11): exactly 32 frames,
excl.py v3 pass (room-keyed), ARKit visit_id present, not a K1 capture or K1 room; one clip per visit first (seed 20261120), then the rest.
Named kinds: none (blind inventory; O5 default accepted by ORCH 0444Z). Check kinds: 15 open nouns from the frozen CHECK_VOCAB (ebac12b2) outside the
ARKit vocabulary (as V6's open rule), seeded per clip (O6 default accepted). Opaque ids k<NNNN> on Orchard; map work/v7_map.json on Trinity only.
usage: NVK=work/v6f python build_v7b.py OUT.jsonl CAP PRIMARY_ROUTE PRIMARY_EFFORT VERIFIER_ROUTE VERIFIER_EFFORT [START]"""
import gzip, json, hashlib, random, sys, os
W = '/scratch/jjyeung/orch_n30/nv_orch1/work/'
sys.path.insert(0, W + 'v6f/kit'); import excl
sys.path.insert(0, W + 'kit'); import forms_v2 as F
out, cap, pr, pe, vr, ve = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]; start = int(sys.argv[7]) if len(sys.argv) > 7 else 0
cvraw = open(W + 'v6f/v6/CHECK_VOCAB.json').read(); cv = json.loads(cvraw); r3raw = open(W + 'v6f/v6/R3_SIBLINGS.json').read()
STRUCT = {'wall', 'floor', 'ceiling', 'object', 'objects', 'otherfurniture', 'otherprop', 'otherstructure', 'unknown', 'misc', 'structure', 'doorframe', 'beam', 'pipe', 'column'}
openv0 = [x for x in cv['open'] if x not in set(cv['datasets']['arkitscenes']) and x not in STRUCT]
rows = [json.loads(l) for p in ('d3_clips_a.jsonl.gz', 'd3_clips_b.jsonl.gz') for l in gzip.open(W + p, 'rt') if l.strip()]
S = excl._sets(); ks = json.load(open(W + 'v6f/excl/K1_SPLIT.json'))
k1caps = {excl.norm(c['canonical']) for c in ks['train'] + ks['heldout']}; k1rooms = {excl.room(c) for c in k1caps}
ok = []
for r in rows:
    c = 'arkitscenes/' + r['video']; v = S['visits'].get(r['video'])
    if len(r['f']) != 32 or excl.reasons(c) or not v or v == 'NA': continue
    if c in k1caps or excl.room(c) in k1rooms: continue
    ok.append(r)
ok.sort(key=lambda r: r['v']); random.Random(20261120).shuffle(ok)
first, rest, seen = [], [], set()
for r in ok:
    vv = S['visits'][r['video']]; (rest if vv in seen else first).append(r); seen.add(vv)
ok = first + rest; sel = ok[start:start + cap]
vmap = json.load(open(W + 'v7_map.json')) if os.path.exists(W + 'v7_map.json') else {}
n = 0
with open(out, 'w') as f:
    for j, r in enumerate(sel):
        k = 'k%04d' % (start + j); c = 'arkitscenes/' + r['video']; room = excl.room(c); excl.assert_train([c])
        rng = random.Random('check ' + c); openv = list(openv0); rng.shuffle(openv); check = openv[:15]
        content = [{'text': F.PRIMARY.format(named=json.dumps([]), check=json.dumps(check))}]
        for i, (fi, s) in enumerate(r['f']): content += [{'text': 'Frame %d' % (i + 1)}, {'image': 'tar:' + s, 'max_side': 640}]
        f.write(json.dumps({'id': k + '_p', 'model': pr, 'effort': None if pe == 'none' else pe, 'max_tokens': 32768, 'content': content,
                            'meta': {'tag': 'train', 'scenes_h': [F.sha(c), F.sha(room)], 'deny_k1': True, 'form': F.FORM, 'role': 'primary', 'named': [], 'check': check,
                                     'check_type': {x: 'open' for x in check}, 'frames': [{'sha256': s, 'source_index': fi} for fi, s in r['f']],
                                     'prompt_sha256': F.PROMPTS['primary'], 'r3_sha256': F.sha(r3raw), 'check_vocab_sha256': F.sha(cvraw),
                                     'chain': {'job': '21_v7v', 'model': vr, 'effort': None if ve == 'none' else ve}}}) + '\n')
        vmap[k] = {'v': r['v'], 'video': r['video'], 'canonical': c, 'room': room, 'frames': r['f']}; n += 1
json.dump(vmap, open(W + 'v7_map.json', 'w'))
print('eligible', len(ok), 'visits', len(first), 'wrote', n, out, 'prompts', F.PROMPTS, 'r3', F.sha(r3raw)[:8], 'cv', F.sha(cvraw)[:8], 'excl', excl.receipt()['excl_py_sha256'][:8])
