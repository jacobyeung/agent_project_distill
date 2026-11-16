"""Path forcing and the per-draw sampling choice.

The native decoder (`carrier_c1_decode.generate` -> `Row.step`) asks a choice object
for every non-response token: `choose(records, logits)`. Scripted reads pass a
`scripted_calls.ReferenceChoice`; this kit passes a `SamplingChoice`, which
  1. emits the forced first span of the draw's path (head call or direct opening),
  2. then samples with temperature / top-p from a torch.Generator seeded per draw,
  3. emits EOS when the sampled-token budget is spent (recorded as a budget hit).
Tool responses never pass through `choose`: the decoder forces them itself, so
forced response tokens can be separated from the model's own tokens afterwards.
Forced first-span tokens count toward chain length but carry no policy-gradient term.
"""
import math
from contextlib import contextmanager

import torch

PATHS = ('free', 'head', 'direct')


def draw_path(draw, draws, forced_share=0.5, has_head=True, has_direct=True):
    """Deterministic path of a draw. With forced_share 0.5 and 8 draws: 4 free, 2 head, 2 direct.

    Forced draws alternate head/direct; a type without a head (or direct) form samples
    that slot free instead of forcing a form it never trained.
    """
    n_forced = int(round(draws * forced_share))
    if draw < draws - n_forced:
        return 'free'
    k = draw - (draws - n_forced)
    want = 'head' if k % 2 == 0 else 'direct'
    if want == 'head' and not has_head:
        return 'free'
    if want == 'direct' and not has_direct:
        return 'free'
    return want


def forced_text(forcing, prompt, path):
    """Text of the forced first span (after the prompt's own `<think>\\n`), or '' for free."""
    if path == 'free':
        return ''
    spec = (prompt.get('forcing') or {}).get(path)
    if spec is None:
        spec = (forcing.get(prompt['type']) or {}).get(path)
    if spec is None:
        raise KeyError(f'no {path} forcing for type {prompt["type"]}')
    fields = dict(prompt.get('fields') or {})
    objects = prompt.get('objects') or []
    for i, name in enumerate(objects):
        fields.setdefault(f'obj{i}', name)
    text = spec.format(**fields)
    if not text:
        raise ValueError('a forced path needs a non-empty first span')
    return text


def encode_exact(tokenizer, text):
    ids = tokenizer.encode(text, add_special_tokens=False)
    if not ids or tokenizer.decode(ids, skip_special_tokens=False) != text:
        raise ValueError(f'tokenizer cannot preserve the forced span bytes: {text!r}')
    return list(ids)


class SamplingChoice:
    """Token choice for one draw: forced prefix, then seeded temperature/top-p sampling."""
    is_rlkit_choice = True

    def __init__(self, prefix_ids, *, seed, temperature=0.7, top_p=0.95, max_sampled_tokens=4096,
                 eos_id, device='cpu'):
        if not temperature > 0:
            raise ValueError('temperature must be positive (greedy reads use the reader, not this kit)')
        if not 0 < top_p <= 1:
            raise ValueError('top_p must lie in (0, 1]')
        self.prefix = list(prefix_ids)
        self.temperature, self.top_p = float(temperature), float(top_p)
        self.max_sampled = int(max_sampled_tokens)
        self.eos_id = int(eos_id)
        self.seed = int(seed)
        self.generator = torch.Generator(device=device)
        self.generator.manual_seed(self.seed)
        self.chosen = []      # token ids in choose order
        self.kinds = []       # 'f' forced prefix, 's' sampled, 'b' budget EOS
        self.logp_tempered = []  # log prob under the tempered, untruncated distribution
        self.logp_raw = []       # log prob at temperature 1
        self.budget_hit = False

    def choose(self, records, logits):
        logits = logits.float()
        if logits.ndim == 2:
            logits = logits[0]
        raw = torch.log_softmax(logits, -1)
        tempered = torch.log_softmax(logits / self.temperature, -1)
        n_prefix = sum(k == 'f' for k in self.kinds)
        if n_prefix < len(self.prefix):
            token, kind = self.prefix[n_prefix], 'f'
        elif sum(k == 's' for k in self.kinds) >= self.max_sampled:
            token, kind = self.eos_id, 'b'
            self.budget_hit = True
        else:
            token, kind = self._sample(tempered), 's'
        self.chosen.append(int(token))
        self.kinds.append(kind)
        lt, lr = float(tempered[token]), float(raw[token])
        self.logp_tempered.append(lt if math.isfinite(lt) else -1e30)
        self.logp_raw.append(lr if math.isfinite(lr) else -1e30)
        return int(token)

    def _sample(self, logprobs):
        probs = logprobs.exp()
        if self.top_p < 1:
            sorted_p, order = probs.sort(descending=True)
            keep = sorted_p.cumsum(0) - sorted_p < self.top_p  # always keeps the top token
            sorted_p = torch.where(keep, sorted_p, torch.zeros_like(sorted_p))
            probs = torch.zeros_like(probs).scatter(0, order, sorted_p)
        probs = probs / probs.sum()
        return int(torch.multinomial(probs.cpu(), 1, generator=self.generator).item())

    def check_complete(self, result):
        n_prefix = sum(k == 'f' for k in self.kinds)
        if n_prefix < len(self.prefix):
            raise ValueError('decoding stopped inside the forced first span')
        return dict(mode='rlkit_sample', seed=self.seed, forced_prefix_tokens=n_prefix,
                    sampled_tokens=sum(k == 's' for k in self.kinds), budget_hit=self.budget_hit,
                    temperature=self.temperature, top_p=self.top_p)


def align(record, choice):
    """Per-position source of every generated id: 'f' forced prefix, 's' sampled, 'b' budget EOS,
    'r' tool response forced by the decoder. Also checks the decoder's ids against the choice log.
    """
    ids = record['tokens']
    kinds = [None] * len(ids)
    for call in record.get('calls', []):
        start, n = call['at_token'], call['forced_tokens']
        for i in range(start, min(start + n, len(ids))):
            kinds[i] = 'r'
    own = [i for i, k in enumerate(kinds) if k is None]
    if len(own) != len(choice.chosen) or any(ids[i] != t for i, t in zip(own, choice.chosen)):
        raise ValueError('decoded ids disagree with the choice log; response spans misaligned')
    lt = [None] * len(ids)
    lr = [None] * len(ids)
    for j, i in enumerate(own):
        kinds[i] = choice.kinds[j]
        lt[i], lr[i] = choice.logp_tempered[j], choice.logp_raw[j]
    return kinds, lt, lr


@contextmanager
def sampling_hooks():
    """Let the tree's public `generate` accept SamplingChoice objects as reference traces.

    Only the token-choice object changes; every other decode step (prefill, carriers,
    head and tower responses, trace sessions, batching, tower failures) is the tree's.
    The patch is process-local, reversible and touches no file.
    """
    from student_pilot import scripted_calls as sc
    original_validate, original_choice = sc.validate_reference, sc.ReferenceChoice

    def validate(ref):
        if getattr(ref, 'is_rlkit_choice', False):
            return []
        return original_validate(ref)

    def make_choice(ref, tokenizer):
        if getattr(ref, 'is_rlkit_choice', False):
            return ref
        return original_choice(ref, tokenizer)

    sc.validate_reference, sc.ReferenceChoice = validate, make_choice
    try:
        yield
    finally:
        sc.validate_reference, sc.ReferenceChoice = original_validate, original_choice
