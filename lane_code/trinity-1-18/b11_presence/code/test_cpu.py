"""CPU first batch through the full forward (fp32): prompt tokenization equality and prefix-reuse equality.
For one held-out K1 capture: arm V on 2 objects x 2 frames, arms I and Y on 2 objects x 1 frame.
Each cached+batched read is compared with a single full-prompt forward without cache."""
import json, sys, time
from pathlib import Path
import torch
sys.path.insert(0, str(Path(__file__).parent))
from scorer import Scorer, LANE

torch.set_num_threads(int(sys.argv[1]) if len(sys.argv) > 1 else 32)
caps = [json.loads(l) for l in open(LANE / 'out/prep/CAPTURES.jsonl')]
cap = sorted([c for c in caps if c['split'] == 'heldout'], key=lambda c: c['canonical'])[0]
t0 = time.monotonic()
s = Scorer('cpu', 'fp32')
print('loaded', round(time.monotonic() - t0), 's', flush=True)
objs = cap['scored'][:2]
res = dict(capture=cap['canonical'], objects=objs, checks=[])
anchors = s.load_frames(cap)


def full_logits(batch):
    with torch.inference_mode():
        out = s.model(**batch, use_cache=False, logits_to_keep=1)
    return out.logits[0, -1].float()


# ---- arm V ----
texts = [(o, k, s.full_text('V', o, k)) for o in objs for k in (1, 17)]
pre = s.split(texts[0][2])[0]
inp, (arrays, meta) = s.video_inputs(cap, anchors, pre)
t1 = time.monotonic()
cache, plen, delta = s.prefix_forward(inp)
res['V_prefix_seconds'] = time.monotonic() - t1
res['V_prefix_tokens'] = plen
tails = [s.tail_ids(s.split(x[2])[1]) for x in texts]
t1 = time.monotonic()
lg = s.tails_forward(cache, plen, delta, tails)
res['V_tails_seconds'] = time.monotonic() - t1
from transformers.video_utils import VideoMetadata
from scorer import video_kwargs
for (o, k, text), l, tl in zip(texts, lg, tails):
    full = s.processor(text=[text], videos=[arrays], video_metadata=[VideoMetadata(**meta)], **video_kwargs(len(arrays)),
                       return_tensors='pt')
    ids_equal = full['input_ids'][0].tolist() == inp['input_ids'][0].tolist() + tl
    t1 = time.monotonic()
    fl = full_logits(full)
    a, b = s.read('V', l), s.read('V', fl)
    res['checks'].append(dict(arm='V', obj=o, frame=k, ids_equal=ids_equal, cached=a, full=b,
                              logit_diff=abs(a['logit'] - b['logit']), full_seconds=time.monotonic() - t1,
                              max_abs_logit_diff=float((l - fl).abs().max())))
    print(res['checks'][-1], flush=True)
# ---- arms I, Y ----
k = 9
texts = [(a, o, s.full_text(a, o)) for a in ('I', 'Y') for o in objs]
pre = s.split(texts[0][2])[0]
cache, plen, delta = s.prefix_forward(s.image_inputs(anchors[k - 1], pre))
tails = [s.tail_ids(s.split(x[2])[1]) for x in texts]
lg = s.tails_forward(cache, plen, delta, tails)
for (a, o, text), l, tl in zip(texts, lg, tails):
    full = s.image_inputs(anchors[k - 1], text)
    ids_equal = full['input_ids'][0].tolist() == s.image_inputs(anchors[k - 1], pre)['input_ids'][0].tolist() + tl
    fl = full_logits(full)
    x, y = s.read(a, l), s.read(a, fl)
    res['checks'].append(dict(arm=a, obj=o, frame=k, ids_equal=ids_equal, cached=x, full=y,
                              logit_diff=abs(x['logit'] - y['logit']), max_abs_logit_diff=float((l - fl).abs().max()),
                              top_token=s.tok.decode([y['top']])))
    print(res['checks'][-1], flush=True)
res['visible_gt'] = {o: cap['categories'][o]['visible'] for o in objs}
res['pass'] = all(c['ids_equal'] and c['logit_diff'] < 0.05 for c in res['checks'])
res['seconds'] = time.monotonic() - t0
(LANE / 'out/tests').mkdir(parents=True, exist_ok=True)
(LANE / 'out/tests/CPU_FIRST_BATCH.json').write_text(json.dumps(res, indent=1) + '\n')
print('PASS' if res['pass'] else 'FAIL', json.dumps({k: v for k, v in res.items() if k != 'checks'}))
