"""nv_orch1 V7 boolean-form queues (ORCH ANSWER 0532Z) for clips [START, START+CAP) of the build_v7b order (O1 rule, one clip per visit first).
Writes OUTDIR/20_v7a.jsonl ((a): 17 ARKit classes + 4 decoys, Astra and Argon) and OUTDIR/22_v7n.jsonl ((b) naming call, Astra; chain -> 23_v7b).
usage: NVK=work/v6f python build_v7_bool.py OUTDIR CAP [START]"""
import gzip, json, random, sys, os
W = '/scratch/jjyeung/orch_n30/nv_orch1/work/'
sys.path.insert(0, W + 'v6f/kit'); import excl
sys.path.insert(0, W + 'kit'); import forms_b as F
outdir, cap = sys.argv[1], int(sys.argv[2]); start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
AST = ('openai/openai/gpt-6.2-astra', 'high'); ARG = ('gcp/google/gemini-4-argon', 'high')
cvraw = open(W + 'v6f/v6/CHECK_VOCAB.json').read(); cv = json.loads(cvraw); r3 = json.load(open(W + 'v6f/v6/R3_SIBLINGS.json'))['sets']
STRUCT = {'wall', 'floor', 'ceiling', 'object', 'objects', 'otherfurniture', 'otherprop', 'otherstructure', 'unknown', 'misc', 'structure', 'doorframe', 'beam', 'pipe', 'column'}
sib = set(F.ARKIT17)
for g in r3:
    if set(g) & set(F.ARKIT17): sib |= set(g)
pool0 = [x for x in cv['open'] if x not in sib and x not in STRUCT and x not in set(cv['datasets']['arkitscenes'])]
clips = [json.loads(l) for p in ('d3_clips_a.jsonl.gz', 'd3_clips_b.jsonl.gz') for l in gzip.open(W + p, 'rt') if l.strip()]
S = excl._sets(); ks = json.load(open(W + 'v6f/excl/K1_SPLIT.json'))
k1caps = {excl.norm(c['canonical']) for c in ks['train'] + ks['heldout']}; k1rooms = {excl.room(c) for c in k1caps}
ok = []
for r in clips:
    c = 'arkitscenes/' + r['video']; v = S['visits'].get(r['video'])
    if len(r['f']) != 32 or excl.reasons(c) or not v or v == 'NA' or c in k1caps or excl.room(c) in k1rooms: continue
    ok.append(r)
ok.sort(key=lambda r: r['v']); random.Random(20261120).shuffle(ok)
first, rest, seen = [], [], set()
for r in ok:
    vv = S['visits'][r['video']]; (rest if vv in seen else first).append(r); seen.add(vv)
ok = first + rest; sel = ok[start:start + cap]
vmap = json.load(open(W + 'v7_map.json')) if os.path.exists(W + 'v7_map.json') else {}
na = nn = 0; os.makedirs(outdir, exist_ok=True)
with gzip.open(os.path.join(outdir, '20_v7a.jsonl.gz'), 'wt') as fa, open(os.path.join(outdir, '22_v7n.jsonl'), 'w') as fn:
    for j, r in enumerate(sel):
        k = 'k%04d' % (start + j); c = 'arkitscenes/' + r['video']; room = excl.room(c); excl.assert_train([c])
        frames = []
        for i, (fi, s) in enumerate(r['f']): frames += [{'text': 'Frame %d' % (i + 1)}, {'image': 'tar:' + s, 'max_side': 640}]
        rng = random.Random('decoy ' + c); pool = list(F.DECOYS); rng.shuffle(pool); assert all(x in cv['open'] for x in pool)
        meta = {'tag': 'train', 'scenes_h': [F.sha(c), F.sha(room)], 'deny_k1': True, 'clip': k, 'src_idx': [fi for fi, _ in r['f']], 'src_sha': [s for _, s in r['f']],
                'check_vocab_sha256': F.sha(cvraw)}
        dec = pool[:4]; kinds = F.ARKIT17 + dec; random.Random('a ' + c).shuffle(kinds)
        for t in F.boolean_tasks(k, frames, kinds, [AST, ARG], dict(meta, decoys=dec), 'a'): fa.write(json.dumps(t) + '\n'); na += 1
        fn.write(json.dumps({'id': k + '_n_p', 'model': AST[0], 'effort': AST[1], 'max_tokens': 4096, 'content': [{'text': F.NAMING}] + frames,
                             'meta': dict(meta, role='naming', prompt_sha256=F.PROMPTS['naming'], note=F.NOTE_B, form=F.FORM,
                                          chain={'job': '23_v7b', 'models': [list(AST), list(ARG)], 'decoy_pool': pool})}) + '\n'); nn += 1
        vmap[k] = {'v': r['v'], 'video': r['video'], 'canonical': c, 'room': room, 'frames': r['f']}
json.dump(vmap, open(W + 'v7_map.json', 'w'))
print('eligible', len(ok), 'clips', len(sel), 'a tasks', na, 'naming tasks', nn, 'prompts', F.PROMPTS)
