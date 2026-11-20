"""nv_orch1: tasks for the Orchard probe (32 anchors of one capture, both families) and the 64-frame dev-S1 census (ORDER 0356Z).
Same prompt as nvkey1's C0 (kit/c1_jobs.PROMPT, n=64), same names per capture as C0_MANIFEST, 64 tower frames from the reads' DENSE_MANIFEST
(the 32 C0 anchors are nested at anchor_slots). Names are split into calls of at most 6 so 64-frame outputs stay under ~18K tokens.
Opaque ids on Orchard (c<NN>); the capture map stays on Trinity (work/c64_map.json). Analysis only: dev-S1, nothing becomes a training row."""
import json, sys, hashlib
sys.path.insert(0, '/scratch/jjyeung/orch_n30/nvkey1/work/kit')
from c1_jobs import PROMPT
W = '/scratch/jjyeung/orch_n30/nv_orch1/work/'
man = json.load(open(W + 'k228/scratch/jjyeung/orch_n30/nvkey1/work/c0/C0_MANIFEST.json'))
dense = json.load(open(W + 'rd/b/work/meta/x/sj/orch_cd/evalx/work/milestone/raw_g3t_20261114/admission/DENSE_MANIFEST.json'))['captures']
idx = {tuple(d['frames'][s]['sha256'] for s in d['anchor_slots']): k for k, d in dense.items()}
MODELS = {'a': ('gcp/google/gemini-4-argon', 'high'), 's': ('openai/openai/gpt-6.2-astra', 'high')}
cmap = {}; probe = []; census = []; phash = {}
for ci, (sc, m) in enumerate(man.items()):
    anch = tuple(f.split('/')[-1].split('.')[0] for f in m['frames']); nat = idx[anch]; d = dense[nat]
    shas = [f['sha256'] for f in d['frames']]; slots = d['anchor_slots']; assert [shas[s] for s in slots] == list(anch)
    cid = 'c%02d' % ci; cmap[cid] = dict(scene=sc, native=nat, names=m['names'], slots=slots, shas=shas, anchors=list(anch), n_tower=len(shas))
    if len(shas) != 64: continue  # 29 ARKit captures carry only their 32 anchors on Orchard
    names = m['names']; chunks = [names[i:i + 6] for i in range(0, len(names), 6)]
    for mk, (route, eff) in MODELS.items():
        for qi, kinds in enumerate(chunks):
            text = PROMPT.format(n=64, kinds=json.dumps(kinds), k0=kinds[0]); phash['%s_q%d' % (cid, qi)] = hashlib.sha256(text.encode()).hexdigest()
            content = [{'text': text}]
            for i, s in enumerate(shas): content += [{'text': 'Frame %d' % (i + 1)}, {'image': 'tar:' + s, 'max_side': 640}]
            census.append({'id': '%s_q%d_%s_f64' % (cid, qi, mk), 'model': route, 'effort': eff, 'max_tokens': 32768, 'content': content,
                           'meta': {'c': cid, 'q': qi, 'n': 64, 'side': 640, 'kinds': kinds, 'slots': slots, 'tag': 'dev-analysis'}})
        if ci == 0:
            text = PROMPT.format(n=32, kinds=json.dumps(names), k0=names[0]); content = [{'text': text}]
            for i, s in enumerate(anch): content += [{'text': 'Frame %d' % (i + 1)}, {'image': 'tar:' + s, 'max_side': 640}]
            probe.append({'id': '%s_%s_f32_probe' % (cid, mk), 'model': route, 'effort': eff, 'max_tokens': 32768, 'content': content,
                          'meta': {'c': cid, 'n': 32, 'side': 640, 'kinds': names, 'tag': 'dev-analysis'}})
json.dump(dict(cmap=cmap, prompt_sha256=phash), open(W + 'c64_map.json', 'w'))
for fn, rows in (('q/01_probe.jsonl', probe), ('q/10_c64.jsonl', census)):
    with open(W + fn, 'w') as f:
        for r in rows: f.write(json.dumps(r) + '\n')
print('probe', len(probe), 'census', len(census), 'by model', {k: sum(1 for r in census if r['id'].endswith('_%s_f64' % k)) for k in MODELS})
allsh = sorted(set(s for c in cmap.values() for s in c['shas'] + c['anchors']))
print('captures with 64 tower frames', sum(1 for c in cmap.values() if c['n_tower'] == 64), 'of', len(cmap)); open(W + 'q/SHAS.txt', 'w').write('\n'.join(allsh) + '\n'); print('distinct frames', len(allsh))
