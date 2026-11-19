"""Token/weight probe for pointing rows through the tree's own helpers (proxy tokenizer; real Qwen3.5 files MISSING).

Run: bash work/run.sh probe   (writes work/probe.json)
The tree's training_text builds prompt/suffix; pointing_token_weights and segment_tags assign weights/tags.
Proxy tokenizer: one token per Qwen2-family pre-tokenizer match, special tokens atomic. Real BPE can only
split a pre-token further (rare words/labels), so non-special counts are lower bounds; the three
think-block tokens ("\n", "</think>", "\n\n") are single tokens in Qwen-family vocabularies.
"""
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import regex
import torch

PACK = Path('/scratch/jjyeung/orch_n30/fb_pack')
TREE = PACK/'ro/orch_n30/tree_rebuild10_w/w24/work/tree_r1'
SOURCE = PACK/'in/pointing/rows_c09bb5ca.sqlite'
LOCATE = PACK/'point/out/rows_pointing_locate.sqlite'
CONFIGS = [TREE/'configs/E2E-1C.json', TREE/'configs/E2E-1G.json']
sys.path.insert(0, str(TREE))

from student_pilot.batches import training_text  # noqa: E402
from student_pilot.carrier_c1_data import pointing_token_weights, segment_tags, STREAM_SEGMENTS, READOUT_TARGET  # noqa: E402

PATTERN = regex.compile(r"""(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+""")
SPECIAL = {'<|endoftext|>': 248044, '<|im_start|>': 248045, '<|im_end|>': 248046, '<think>': 248068,
           '</think>': 248069, '<|vision_start|>': 248053, '<|vision_end|>': 248054, '<|video_pad|>': 248057}
SPLIT = regex.compile('(' + '|'.join(regex.escape(s) for s in SPECIAL) + ')')


class ProxyTokenizer:
    eos_token, eos_token_id, pad_token_id = '<|im_end|>', 248046, 248044

    def __init__(self):
        self.vocab, self.inverse = dict(SPECIAL), {v: k for k, v in SPECIAL.items()}

    def encode(self, text, add_special_tokens=False):
        ids = []
        for part in SPLIT.split(text):
            if part in SPECIAL:
                ids.append(SPECIAL[part])
                continue
            for piece in PATTERN.findall(part):
                if piece not in self.vocab:
                    self.vocab[piece] = len(self.vocab)
                    self.inverse[self.vocab[piece]] = piece
                ids.append(self.vocab[piece])
        return ids

    def decode(self, ids, skip_special_tokens=False):
        return ''.join('' if skip_special_tokens and int(i) in SPECIAL.values() else self.inverse[int(i)] for i in ids)


class ProxyProcessor:
    """Qwen3-family template as the tree's own boundary code expects it (batches.py:111-125,
    vqa_direct.py:181-182, pointing_markers.py:164-166): default generation prefix ends '<think>\\n';
    enable_thinking=False ends with the empty think block; the final assistant turn renders
    '<think>\\n' + reasoning.strip('\\n') + '\\n</think>\\n\\n' + content.lstrip('\\n')."""
    _student_pilot_student = 'qwen35'

    def __init__(self):
        self.tokenizer = ProxyTokenizer()

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True, enable_thinking=None):
        text = messages[0]['content'][1]['text']
        prompt = '<|im_start|>user\n<|vision_start|><|video_pad|><|vision_end|>' + text + '<|im_end|>\n<|im_start|>assistant\n'
        if len(messages) == 2:
            content = messages[1]['content']
            reasoning = content.split('</think>')[0].rstrip('\n').split('<think>')[-1].lstrip('\n') if '</think>' in content else ''
            answer = content.split('</think>')[-1].lstrip('\n')
            return prompt + '<think>\n' + reasoning.strip('\n') + '\n</think>\n\n' + answer + self.tokenizer.eos_token + '\n'
        return prompt + ('<think>\n\n</think>\n\n' if enable_thinking is False else '<think>\n')


def encode(processor, question, target):
    tok = processor.tokenizer
    prompt, suffix = training_text(processor, question, [], target)
    plain, suffix_ids = tok.encode(prompt), tok.encode(suffix)
    merged = tok.encode(prompt + suffix) != plain + suffix_ids
    labels = torch.tensor([[-100] * len(plain) + suffix_ids])
    return prompt, suffix, plain, suffix_ids, merged, labels


def analyse(processor, row, weights_cfg, zero_think=False):
    tok = processor.tokenizer
    prompt, suffix, plain, suffix_ids, merged, labels = encode(processor, row['student_input']['question'], row['target'])
    shifted = labels[:, 1:]
    w = pointing_token_weights(shifted, lambda i: tok.decode([i]), **weights_cfg).reshape(-1)
    tags = segment_tags(shifted, 'pointing', lambda i: tok.decode([i])).reshape(-1)
    pos = (shifted.reshape(-1) != -100).nonzero().flatten().tolist()
    pieces = [tok.decode([int(shifted[0, i])]) for i in pos]
    json_start = next(k for k, p in enumerate(pieces) if p.startswith('{'))
    think = pos[:json_start]
    if zero_think:
        w[think] = 0.
        w[pos] *= weights_cfg['row_mean'] * len(pos) / float(w[pos].sum())
    total = float(w[pos].sum())
    decision = max(pos, key=lambda i: float(w[i]))
    return dict(prompt_tail=prompt[-24:], suffix=suffix, merged_boundary=merged, n_supervised=len(pos),
                n_think=len(think), think_weight_share=float(w[think].sum()) / total,
                think_weight_sum_over_n=float(w[think].sum()) / len(pos), row_coefficient=total / len(pos),
                decision_piece=tok.decode([int(shifted[0, decision])]), decision_weight=float(w[decision]),
                json_token_weight=float(w[pos[json_start]]),
                tokens=[dict(piece=p, weight=round(float(w[i]), 4), tag=STREAM_SEGMENTS[int(tags[i])] if tags[i] >= 0 else None)
                        for p, i in zip(pieces, pos)])


def rows(path):
    c = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
    try:
        for i, raw in c.execute('SELECT i,row FROM rows ORDER BY i'):
            yield i, json.loads(raw)
    finally:
        c.close()


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def summarise(values):
    values = sorted(values)
    return dict(n=len(values), mean=sum(values) / len(values), min=values[0], max=values[-1],
                median=values[len(values) // 2])


def main():
    cfgs = {p.name: json.loads(p.read_text()) for p in CONFIGS}
    pw = cfgs['E2E-1C.json']['pointing_weights']
    assert all(c['pointing_weights'] == pw for c in cfgs.values())
    uniform = dict(decision=1.0, row_mean=1.0)
    processor = ProxyProcessor()
    out = dict(inputs={str(p): sha(p) for p in [SOURCE, LOCATE, *CONFIGS, Path(__file__),
                                                 TREE/'student_pilot/batches.py', TREE/'student_pilot/carrier_c1_data.py']},
               tokenizer='MISSING real Qwen3.5 files on local /scratch; proxy = Qwen2-family pre-token regex, specials atomic',
               pointing_weights=pw)
    examples, stats = {}, {k: {'visible': [], 'null': []} for k in
                           ('base_think_share', 'base_think_share_uniform', 'base_n', 'base_think_over_n',
                            'locate_think_share', 'locate_n', 'locate_decision_weight', 'c_json_weight_ratio')}
    merged, prefixes, starts = Counter(), Counter(), Counter()
    longest = (0, None)
    for (i, base), (j, loc) in zip(rows(SOURCE), rows(LOCATE)):
        assert i == j and base['qid'] == loc['qid'] and base['target'].startswith(READOUT_TARGET)
        kind = 'null' if base['pointing']['kind'] == 'gt_absent' else 'visible'
        a = analyse(processor, base, pw)
        u = analyse(processor, base, uniform)
        c = analyse(processor, base, pw, zero_think=True)
        b = analyse(processor, loc, pw)
        merged[('base', a['merged_boundary'])] += 1
        merged[('locate', b['merged_boundary'])] += 1
        prefixes[a['prompt_tail'][-9:]] += 1
        starts[repr(''.join(t['piece'] for t in a['tokens'][:a['n_think']]))] += 1
        stats['base_think_share'][kind].append(a['think_weight_share'])
        stats['base_think_share_uniform'][kind].append(u['think_weight_share'])
        stats['base_n'][kind].append(a['n_supervised'])
        stats['base_think_over_n'][kind].append(a['think_weight_sum_over_n'])
        stats['locate_think_share'][kind].append(b['think_weight_share'])
        stats['locate_n'][kind].append(b['n_supervised'])
        stats['locate_decision_weight'][kind].append(b['decision_weight'])
        stats['c_json_weight_ratio'][kind].append(c['json_token_weight'] / a['json_token_weight'])
        gen = b['n_supervised']
        if gen > longest[0]:
            longest = (gen, i)
        if i in (0, 3):
            examples[f'{i}:{kind}'] = dict(base=a, uniform=u, zero_think=c, locate=b)
    out['examples'] = examples
    out['merged_boundary_counts'] = {f'{k[0]}:{k[1]}': v for k, v in merged.items()}
    out['prompt_tail_counts'] = dict(prefixes)
    out['supervised_think_text_counts'] = dict(starts)
    out['stats'] = {k: {kind: summarise(v) for kind, v in d.items()} for k, d in stats.items()}
    out['longest_locate_supervised'] = dict(tokens=longest[0], row=longest[1])
    tok = processor.tokenizer
    eval_prefix = tok.encode('<|im_start|>assistant\n<think>\n\n</think>\n\n')
    train_prefix = tok.encode('<|im_start|>assistant\n<think>\n') + tok.encode('\n</think>\n\n')
    out['eval_vs_train_context'] = dict(eval=[tok.decode([t]) for t in eval_prefix], train=[tok.decode([t]) for t in train_prefix])
    counts = {k: {kind: len(v) for kind, v in d.items()} for k, d in stats.items()}['base_n']
    out['row_counts'] = counts
    Path(__file__).with_name('probe.json').write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps({k: out[k] for k in ('merged_boundary_counts', 'prompt_tail_counts', 'supervised_think_text_counts',
                                          'longest_locate_supervised', 'eval_vs_train_context', 'row_counts')}, indent=1))
    print(json.dumps(out['stats'], indent=1))


if __name__ == '__main__':
    main()
