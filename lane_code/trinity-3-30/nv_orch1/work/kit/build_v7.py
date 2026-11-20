"""nv_orch1 V7 queue builder (Trinity side). ORCH ANSWER 0426Z + consumer spec O1/O9/O11: every d3 clip of the k6 MAP with exactly 32 frames that
passes nvkey2's excl.py room-keyed (R1), has an ARKit visit_id (fail closed) and is neither a K1 capture nor in a K1 room (covers V1's calibration
captures and the PE-K1 reserve); order: one clip per visit first (seeded), then the rest (seeded; N's per-clip row counts are not on hand); first CAP. Opaque ids k<NNNN> on Orchard; map in work/v7_map.json (Trinity only).
usage: NVK=work/excl2 python build_v7.py OUT.jsonl CAP PRIMARY_ROUTE PRIMARY_EFFORT VERIFIER_ROUTE VERIFIER_EFFORT [START]"""
import gzip, json, hashlib, random, sys, os
W = '/scratch/jjyeung/orch_n30/nv_orch1/work/'
sys.path.insert(0, W + 'excl2/kit'); import excl
sys.path.insert(0, W + 'kit'); import forms
out, cap, pr, pe, vr, ve = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]; start = int(sys.argv[7]) if len(sys.argv) > 7 else 0
NOUNS = ['bathtub', 'piano', 'treadmill', 'fireplace', 'aquarium', 'bunk bed', 'grandfather clock', 'pool table', 'rowing machine', 'washing machine', 'dishwasher',
         'refrigerator', 'oven', 'sink', 'toilet', 'bed', 'sofa', 'television', 'bookshelf', 'desk', 'chair', 'stool', 'lamp', 'mirror', 'plant', 'rug', 'curtain',
         'radiator', 'fan', 'printer', 'microwave', 'kettle', 'guitar', 'bicycle', 'suitcase', 'crib', 'ironing board', 'vacuum cleaner', 'trash can', 'whiteboard']
rows = [json.loads(l) for p in ('d3_clips_a.jsonl.gz', 'd3_clips_b.jsonl.gz') for l in gzip.open(W + p, 'rt') if l.strip()]
S = excl._sets(); ks = json.load(open(W + 'excl2/excl/K1_SPLIT.json'))
k1caps = {excl.norm(c['canonical']) for c in ks['train'] + ks['heldout']}; k1rooms = {excl.room(c) for c in k1caps}
ok = []
for r in rows:
    c = 'arkitscenes/' + r['video']; v = S['visits'].get(r['video'])
    if len(r['f']) != 32 or excl.reasons(c) or not v or v == 'NA': continue
    if c in k1caps or excl.room(c) in k1rooms: continue
    ok.append(r)
ok.sort(key=lambda r: r['v']); rnd = random.Random(20261120); rnd.shuffle(ok)
first, rest, seen = [], [], set()
for r in ok:
    vv = S['visits'][r['video']]
    (rest if vv in seen else first).append(r); seen.add(vv)
ok = first + rest
sel = ok[start:start + cap]; vmap = json.load(open(W + 'v7_map.json')) if os.path.exists(W + 'v7_map.json') else {}
n = 0
with open(out, 'w') as f:
    for j, r in enumerate(sel):
        k = 'k%04d' % (start + j); c = 'arkitscenes/' + r['video']; room = excl.room(c)
        excl.assert_train([c])
        absent = random.Random(k).sample(NOUNS, 15)
        content = [{'text': forms.PRIMARY.format(n=32, absent=json.dumps(absent))}]
        for i, (fi, s) in enumerate(r['f']): content += [{'text': 'Frame %d' % (i + 1)}, {'image': 'tar:' + s, 'max_side': 640}]
        f.write(json.dumps({'id': k + '_p', 'model': pr, 'effort': None if pe == 'none' else pe, 'max_tokens': 32768, 'content': content,
                            'meta': {'tag': 'train', 'scenes_h': [hashlib.sha256(c.encode()).hexdigest(), hashlib.sha256(room.encode()).hexdigest()], 'n': 32, 'role': 'primary',
                                     'src_idx': [fi for fi, _ in r['f']], 'src_sha': [s for _, s in r['f']], 'form': forms.FORM,
                                     'absent': absent, 'prompt_sha256': forms.PROMPTS['primary'], 'chain': {'job': '21_v7v', 'model': vr, 'effort': None if ve == 'none' else ve}}}) + '\n')
        vmap[k] = {'v': r['v'], 'video': r['video'], 'canonical': c, 'room': room, 'frames': r['f']}; n += 1
json.dump(vmap, open(W + 'v7_map.json', 'w'))
print('eligible', len(ok), 'visits', len(first), 'wrote', n, 'tasks', out, 'prompts', forms.PROMPTS)
