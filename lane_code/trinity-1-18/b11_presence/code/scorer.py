"""Presence scorer: the step-544 model's own per-frame presence decision on K1 captures.

Arms (all read one next-token decision; no generation):
  V  trained format: 32-frame video (duplicate layout, reader kwargs), "Point to the {obj} in frame {k}. ... null"
     + ANSWER_FORMAT_INSTRUCTION, empty think, forced '{"point_2d":'; presence = logit(' [') - logit(' null').
  I  single image, same pointing wording for "this image", empty think, forced '{"point_2d":'; same read-out.
  Y  single image, "Is the {obj} visible in this image? Answer yes or no.", empty think; presence = log P(yes-group) - log P(no-group).
Prefix reuse: the visual prefix (up to <|vision_end|>) runs once; every query tail runs against a copy of its cache,
right-padded, read at its last real token. test_cpu.py checks this against single full-prompt forwards.
Journal: out/journals/<arm>/<capture>.jsonl, written whole per capture (resume = skip existing files).
"""
import argparse, copy, hashlib, json, os, sys, time
from pathlib import Path
import numpy as np

LANE = Path('/scratch/jjyeung/orch_n30/b11_presence')
READER = Path('/scratch/jjyeung/orch_n30/trin_read/root/sj/apb59bef09f3/p/reader/evaluator')
MODEL = LANE / 'work/model_m544'
EMPTY_THINK = '<think>\n\n</think>\n\n'
FORCE = '{"point_2d":'
TOK_PRESENT, TOK_ABSENT = 498, 819          # ' [' and ' null' (checked in load())
V_QUESTION = ('Point to the {obj} in frame {k}. Output the point as JSON {{"point_2d": [x, y]}} with integer '
              'coordinates on a 0-1000 grid of that frame. If there is no {obj} in frame {k}, output {{"point_2d": null}}.')
I_QUESTION = ('Point to the {obj} in this image. Output the point as JSON {{"point_2d": [x, y]}} with integer '
              'coordinates on a 0-1000 grid of this image. If there is no {obj} in this image, output {{"point_2d": null}}.')
Y_QUESTION = 'Is the {obj} visible in this image? Answer yes or no.'


def answer_instruction():
    sys.path.insert(0, str(READER))
    from trainer.trace_contract import ANSWER_FORMAT_INSTRUCTION
    return ANSWER_FORMAT_INSTRUCTION


def video_kwargs(count):   # = reader media.kwargs
    return dict(size={'shortest_edge': count * 128 * 128, 'longest_edge': count * 384 * 384}, do_sample_frames=False)


def token_groups(tok, labels):
    groups = []
    for label in labels:
        ids = set()
        for s in {label, label.capitalize(), label.upper()}:
            for pre in ('', ' '):
                e = tok.encode(pre + s, add_special_tokens=False)
                if len(e) == 1 and tok.decode(e).strip().casefold() == label:
                    ids.add(e[0])
        groups.append(sorted(ids))
    return groups


class Scorer:
    def __init__(self, device='cuda', dtype='bf16', model=MODEL):
        import torch
        from transformers import AutoProcessor, AutoModelForImageTextToText
        self.torch = torch
        self.processor = AutoProcessor.from_pretrained(str(model), local_files_only=True)
        self.tok = self.processor.tokenizer
        assert self.tok.decode([TOK_PRESENT]) == ' [' and self.tok.decode([TOK_ABSENT]) == ' null'
        self.yes_no = token_groups(self.tok, ['yes', 'no'])
        dt = dict(bf16=torch.bfloat16, fp32=torch.float32)[dtype]
        self.model = AutoModelForImageTextToText.from_pretrained(str(model), local_files_only=True, dtype=dt).to(device).eval()
        self.device, self.dtype = device, dtype
        self.instr = answer_instruction()
        self.pad = self.tok.pad_token_id if self.tok.pad_token_id is not None else self.tok.eos_token_id

    # ---------- prompt text ----------
    def chat(self, kind, text):
        msgs = [{'role': 'user', 'content': [{'type': kind}, {'type': 'text', 'text': text}]}]
        v = self.processor.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        assert v.endswith(EMPTY_THINK), 'empty-think prefix changed'
        return v

    def full_text(self, arm, obj, k=None):
        if arm == 'V':
            return self.chat('video', V_QUESTION.format(obj=obj, k=k) + '\n\n' + self.instr) + FORCE
        if arm == 'I':
            return self.chat('image', I_QUESTION.format(obj=obj)) + FORCE
        return self.chat('image', Y_QUESTION.format(obj=obj))

    @staticmethod
    def split(text):
        i = text.index('<|vision_end|>') + len('<|vision_end|>')
        return text[:i], text[i:]

    # ---------- media ----------
    @staticmethod
    def load_frames(cap):
        from PIL import Image
        arrs = []
        for p, s in zip(cap['frames'], cap['frame_sha256']):
            raw = Path(p).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == s, 'frame sha mismatch ' + p
            import io
            with Image.open(io.BytesIO(raw)) as im:
                arrs.append(np.array(im.convert('RGB')))
        return np.stack(arrs)

    def video_inputs(self, cap, anchors, prefix_text):
        from transformers.video_utils import VideoMetadata
        arrays = np.repeat(anchors, 2, axis=0)
        idx = [i for i in cap['frame_indices'] for _ in range(2)]
        meta = dict(fps=cap['fps'], frames_indices=idx, total_num_frames=cap['total_num_frames'],
                    height=int(arrays.shape[1]), width=int(arrays.shape[2]))
        return self.processor(text=[prefix_text], videos=[arrays], video_metadata=[VideoMetadata(**meta)],
                              **video_kwargs(len(arrays)), return_tensors='pt'), (arrays, meta)

    def image_inputs(self, image, prefix_text):
        from PIL import Image
        return self.processor(text=[prefix_text], images=[Image.fromarray(image)], return_tensors='pt')

    # ---------- forward ----------
    def prefix_forward(self, batch):
        torch = self.torch
        batch = {k: v.to(self.device) for k, v in batch.items()}
        with torch.inference_mode():
            out = self.model(**batch, use_cache=True, logits_to_keep=1)
        delta = self.model.model.rope_deltas.reshape(-1)[0].item()
        return out.past_key_values, batch['input_ids'].shape[1], int(delta)

    def expand(self, cache, b):
        c = copy.copy(cache)
        c.layers = []
        for layer in cache.layers:
            nl = copy.copy(layer)
            for a in ('keys', 'values', 'conv_states', 'recurrent_states'):
                t = getattr(layer, a, None)
                if isinstance(t, self.torch.Tensor):
                    setattr(nl, a, t.expand(b, *t.shape[1:]).contiguous())
            c.layers.append(nl)
        return c

    def tails_forward(self, cache, plen, delta, tails):
        """tails: list of token-id lists. Returns float32 logits [len(tails), vocab] at each last real token."""
        torch = self.torch
        b, t = len(tails), max(len(x) for x in tails)
        ids = torch.full((b, t), self.pad, dtype=torch.long)
        am = torch.zeros((b, plen + t), dtype=torch.long)
        am[:, :plen] = 1
        for i, x in enumerate(tails):
            ids[i, :len(x)] = torch.tensor(x)
            am[i, plen:plen + len(x)] = 1
        pos = (torch.arange(plen, plen + t) + delta).view(1, 1, t).expand(3, b, t).contiguous()
        with torch.inference_mode():
            out = self.model(input_ids=ids.to(self.device), attention_mask=am.to(self.device),
                             position_ids=pos.to(self.device), past_key_values=self.expand(cache, b), use_cache=True)
        last = torch.tensor([len(x) - 1 for x in tails], device=out.logits.device)
        return out.logits[torch.arange(b, device=last.device), last].float().cpu()

    def read(self, arm, logits):
        lp = logits.log_softmax(-1)
        top = int(lp.argmax())
        if arm in ('V', 'I'):
            a, n = lp[TOK_PRESENT].item(), lp[TOK_ABSENT].item()
        else:
            a = lp[self.yes_no[0]].logsumexp(0).item(); n = lp[self.yes_no[1]].logsumexp(0).item()
        return dict(logit=a - n, lp_present=a, lp_absent=n, top=top)

    def tail_ids(self, text):
        return self.tok.encode(text, add_special_tokens=False)

    # ---------- per capture ----------
    def score_capture(self, cap, arms, batch=64, frames=None):
        anchors = self.load_frames(cap)
        cats = cap['scored']
        frames = list(range(1, 33)) if frames is None else frames
        rows, timing = [], {}
        if 'V' in arms:
            t0 = time.monotonic()
            texts = [(o, k, self.full_text('V', o, k)) for o in cats for k in frames]
            pre = self.split(texts[0][2])[0]
            assert all(self.split(x[2])[0] == pre for x in texts)
            inp, _ = self.video_inputs(cap, anchors, pre)
            cache, plen, delta = self.prefix_forward(inp)
            tails = [self.tail_ids(self.split(x[2])[1]) for x in texts]
            for s in range(0, len(texts), batch):
                lg = self.tails_forward(cache, plen, delta, tails[s:s + batch])
                for (o, k, _), l in zip(texts[s:s + batch], lg):
                    rows.append(dict(arm='V', capture=cap['canonical'], obj=o, frame=k, **self.read('V', l)))
            del cache
            timing['V'] = dict(seconds=time.monotonic() - t0, queries=len(texts), prefix_tokens=plen)
        img_arms = [a for a in ('I', 'Y') if a in arms]
        if img_arms:
            t0 = time.monotonic(); n = 0
            for k in frames:
                texts = [(a, o, self.full_text(a, o)) for a in img_arms for o in cats]
                pre = self.split(texts[0][2])[0]
                assert all(self.split(x[2])[0] == pre for x in texts)
                cache, plen, delta = self.prefix_forward(self.image_inputs(anchors[k - 1], pre))
                tails = [self.tail_ids(self.split(x[2])[1]) for x in texts]
                for s in range(0, len(texts), batch):
                    lg = self.tails_forward(cache, plen, delta, tails[s:s + batch])
                    for (a, o, _), l in zip(texts[s:s + batch], lg):
                        rows.append(dict(arm=a, capture=cap['canonical'], obj=o, frame=k, **self.read(a, l)))
                n += len(texts)
                del cache
            timing['IY'] = dict(seconds=time.monotonic() - t0, queries=n, arms=img_arms)
        return rows, timing


def slug(c):
    return c.replace('/', '__')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arms', default='V,I,Y')
    ap.add_argument('--out', default=str(LANE / 'out/journals'))
    ap.add_argument('--split', default='all', choices=['all', 'train', 'heldout'])
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--only', default='', help='comma list of canonicals')
    ap.add_argument('--order', default='heldout_first', choices=['heldout_first', 'file'])
    ap.add_argument('--batch', type=int, default=64)
    ap.add_argument('--device', default='cuda')
    ap.add_argument('--dtype', default='bf16')
    ap.add_argument('--stop-file', default=str(LANE / 'work/STOP'))
    a = ap.parse_args()
    arms = a.arms.split(',')
    caps = [json.loads(l) for l in open(LANE / 'out/prep/CAPTURES.jsonl')]
    if a.split != 'all':
        caps = [c for c in caps if c['split'] == a.split]
    if a.only:
        want = set(a.only.split(','))
        caps = [c for c in caps if c['canonical'] in want]
    if a.order == 'heldout_first':
        caps = sorted(caps, key=lambda c: (c['split'] != 'heldout', c['canonical']))
    if a.limit:
        caps = caps[:a.limit]
    out = Path(a.out)
    for arm_set in ['V', 'IY']:
        (out / arm_set).mkdir(parents=True, exist_ok=True)
    s = Scorer(a.device, a.dtype)
    print('LOADED', time.strftime('%H:%M:%SZ', time.gmtime()), flush=True)
    for i, c in enumerate(caps):
        if Path(a.stop_file).exists():
            print('STOP file'); break
        todo = []
        if 'V' in arms and not (out / 'V' / (slug(c['canonical']) + '.jsonl')).exists():
            todo.append('V')
        iy = [x for x in arms if x in ('I', 'Y')]
        if iy and not (out / 'IY' / (slug(c['canonical']) + '.jsonl')).exists():
            todo += iy
        if not todo:
            continue
        rows, timing = s.score_capture(c, todo, batch=a.batch)
        for arm_set, members in (('V', ['V']), ('IY', ['I', 'Y'])):
            part = [r for r in rows if r['arm'] in members]
            if not part:
                continue
            p = out / arm_set / (slug(c['canonical']) + '.jsonl')
            tmp = p.with_suffix('.tmp')
            with open(tmp, 'w') as f:
                for r in part:
                    f.write(json.dumps(r) + '\n')
                f.write(json.dumps(dict(timing=timing, split=c['split'], n=len(part))) + '\n')
            os.replace(tmp, p)
        print(i, c['canonical'], c['split'], json.dumps(timing), time.strftime('%H:%M:%SZ', time.gmtime()), flush=True)


if __name__ == '__main__':
    main()
