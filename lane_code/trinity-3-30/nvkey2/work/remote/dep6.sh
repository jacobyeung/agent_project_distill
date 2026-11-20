K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1
cat > $K/kit/v2_jobs.py <<'PYEOF'
"""nvkey2 V2 alias table: numbered crops of K1 TRAINING ground-truth instances (the anchor frame with the largest mask share, 20% context around the
instance box, mask outline drawn, no class name), 30 crops per call. Returns per crop five noun phrases, the noun a question writer would use, a
part-of-larger flag and a one-object flag. Instances: every ground-truth instance at 1% of the frame or more in some valid anchor of the clear K1
training captures (exclusion assert), rarest classes first. Crops go to K/v2/crops; the instance index (truth) to K/v2/INSTANCES.json (never sent).
usage: v2_jobs.py OUT.jsonl MODEL EFFORT [PER_CALL=30] [all | N | calN (seeded random calibration sample) | restN (all but that sample)]"""
import json, os, sys, random, hashlib, collections
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import excl
K = os.environ.get('NVK', '/scratch/jjyeung/orch_n30/nvkey1/work'); FR = '/scratch/jjyeung/k1_frames'; CR = K + '/v2/crops'
PROMPT = ('Below are {n} numbered crops from photos of indoor rooms. In each crop one object is outlined in green. Name the outlined object only.\n'
          'For each crop give:\n'
          '- "phrases": five different noun phrases a person might use for the outlined object, most likely first (for example "office chair", "desk chair", '
          '"swivel chair", "chair", "rolling chair");\n'
          '- "question_noun": the single noun phrase a person writing a question about this room would most likely use for it;\n'
          '- "part_of_larger": true if the outline covers only a part of a larger object (for example a drawer of a cabinet or a door of a wardrobe), else false;\n'
          '- "one_object": true if the outline covers exactly one physical object, false if it covers several objects or none.\n'
          'Reply with one JSON object and nothing else: {{"1": {{"phrases": [...], "question_noun": "...", "part_of_larger": false, "one_object": true}}, ..., "{n}": {{...}}}}')
def norm(l):
    l = str(l).lower().replace('_', ' ').strip(); return {'tv monitor': 'tv', 'television': 'tv'}.get(l, l)
def instances():
    p = K + '/v2/INSTANCES.json'
    if os.path.exists(p): return json.load(open(p))
    man = json.load(open(K + '/k1r/geo_k1/stage/K1_MANIFEST.arkit_timing.json')); caps = {c['canonical']: c for c in man['captures']}
    idx = json.load(open(K + '/k1r/k1r_index.json')); out = []
    for cn in sorted(idx):
        if excl.reasons(cn): continue
        c = caps[cn]; assert c.get('k1_split') == 'train' and c.get('split') == 'train'
        z = np.load(K + '/k1r/' + idx[cn]['rel'], allow_pickle=True); inst = z['inst']; n, H, W = inst.shape
        valid = [k for k in range(32) if float(z['depth'][k].max()) > 0]
        for i, lab in zip([int(x) for x in z['ids']], [norm(x) for x in z['labels']]):
            sh = [(float((inst[k] == i).sum()) / (H * W), k) for k in valid]
            if not sh: continue
            s, k = max(sh)
            if s < 0.01: continue
            ys, xs = np.nonzero(inst[k] == i)
            sha = os.path.basename(c['dense_frames'][int(c['anchor_slots'][k])]['path']).split('.')[0]
            out.append(dict(id='i' + hashlib.sha256(('%s %d' % (cn, i)).encode()).hexdigest()[:10], canonical=cn, dataset=cn.split('/')[0], inst=i, label=lab,
                            frame=k, share=round(s, 4), box=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())], H=H, W=W, sha=sha, raster=idx[cn]['rel']))
    freq = collections.Counter(x['label'] for x in out)
    random.Random('v2').shuffle(out); out.sort(key=lambda x: freq[x['label']])
    os.makedirs(K + '/v2', exist_ok=True); json.dump(out, open(p, 'w'))
    print('instances', len(out), 'captures', len(set(x['canonical'] for x in out)), 'labels', len(freq))
    return out
def crop(x):
    os.makedirs(CR, exist_ok=True); out = '%s/%s.png' % (CR, x['id'])
    if os.path.exists(out): return out
    im = Image.open('%s/%s/%s.png' % (FR, x['sha'][:2], x['sha'])).convert('RGB'); Wf, Hf = im.size; sx, sy = Wf / float(x['W']), Hf / float(x['H'])
    z = np.load(K + '/k1r/' + x['raster'], allow_pickle=True); m = (z['inst'][x['frame']] == x['inst'])
    x0, y0, x1, y1 = x['box']; bw, bh = x1 - x0 + 1, y1 - y0 + 1; cx0 = max(0, x0 - 0.2 * bw); cy0 = max(0, y0 - 0.2 * bh); cx1 = min(x['W'], x1 + 1 + 0.2 * bw); cy1 = min(x['H'], y1 + 1 + 0.2 * bh)
    edge = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    big = im.copy(); d = ImageDraw.Draw(big)
    for yy, xx in np.argwhere(edge):
        d.rectangle([xx * sx - 1, yy * sy - 1, (xx + 1) * sx, (yy + 1) * sy], fill=(0, 255, 0))
    c = big.crop((int(cx0 * sx), int(cy0 * sy), int(cx1 * sx), int(cy1 * sy))); s = 256.0 / max(c.size)
    if s < 1: c = c.resize((max(1, int(c.size[0] * s)), max(1, int(c.size[1] * s))), Image.LANCZOS)
    c.save(out); return out
def main():
    out, model, effort = sys.argv[1], sys.argv[2], sys.argv[3]; per = int(sys.argv[4]) if len(sys.argv) > 4 else 30
    lim = sys.argv[5] if len(sys.argv) > 5 else 'all'; effort = None if effort == 'none' else effort; extra = json.loads(os.environ.get('C1_EXTRA', '{}')); mtag = model.split('/')[-1]
    xs = instances()
    if lim.startswith('cal'): xs = random.Random('v2 cal').sample(xs, int(lim[3:]))
    elif lim.startswith('rest'):
        cal = {x['id'] for x in random.Random('v2 cal').sample(xs, int(lim[4:]))}; xs = [x for x in xs if x['id'] not in cal]
    elif lim != 'all': xs = xs[:int(lim)]
    excl.assert_train(sorted(set(x['canonical'] for x in xs))); n = 0
    with open(out, 'a') as f:
        for j in range(0, len(xs), per):
            part = xs[j:j + per]; text = PROMPT.format(n=len(part)); content = [{'text': text}]
            for q, x in enumerate(part): content += [{'text': 'Crop %d' % (q + 1)}, {'image': crop(x), 'max_side': 256}]
            f.write(json.dumps({'id': 'v2_%04d_%s' % (j // per, mtag), 'model': model, 'effort': effort, 'max_tokens': 16384, 'extra': extra, 'content': content,
                                'meta': {'tag': 'train', 'scenes': sorted(set(x['canonical'] for x in part)), 'items': [x['id'] for x in part],
                                         'prompt_sha256': hashlib.sha256(PROMPT.encode()).hexdigest()}}) + '\n'); n += 1
    print('v2', mtag, 'instances', len(xs), 'tasks', n)
if __name__ == '__main__': main()
PYEOF
P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%T; cat meter/METER.json; wc -l out/5*.jsonl analysis_only/out/5*.jsonl 2>/dev/null | tail -6; tail -2 runner.log
cd $K/kit && timeout 900 $P -B v2_jobs.py $K/queue/.55.tmp gcp/google/gemini-4-argon high 30 cal300 && C1_EXTRA='{"thinking": {"type": "enabled", "budget_tokens": 4000}}' timeout 300 $P -B v2_jobs.py $K/queue/.55.tmp azure/anthropic/claude-opus-5-5 none 30 cal300 && mv $K/queue/.55.tmp $K/queue/55_v2cal.jsonl
cd $K && wc -l queue/55_v2cal.jsonl; ls v2/crops | wc -l; du -sh v2/crops
$P -B -c "
import json, collections
x=json.load(open('v2/INSTANCES.json')); print('instances', len(x), collections.Counter(i['dataset'] for i in x), collections.Counter(i['label'] for i in x).most_common(8))
import random; cal=random.Random('v2 cal').sample(x, 300); print('cal labels', len(set(i['label'] for i in cal)))"
