"""Digits codec (VLA-0): each normalised value becomes an integer 0..resolution written as text,
values separated by single spaces, time-major. The LM writes the text through its own tokenizer;
codec symbols index `allowed`, the tokenizer ids that writing 0..resolution can produce, so greedy
decoding stays constrained to them. Round trip |error| <= 1 / resolution.

`tokenizer` needs encode(text, add_special_tokens=False) -> ids and decode(ids) -> text (any
transformers tokenizer, or `CharTokenizer` in tests).
"""
import re

import torch


class CharTokenizer:
    """One id per character of a fixed alphabet (tests and examples)."""

    def __init__(self, alphabet='0123456789 -.,', offset=0):
        self.alphabet, self.offset = alphabet, offset

    def encode(self, text, add_special_tokens=False):
        return [self.offset + self.alphabet.index(c) for c in text]

    def decode(self, ids, **kw):
        return ''.join(self.alphabet[i - self.offset] for i in ids)


class DigitsCodec:
    name = 'digits'

    def __init__(self, chunk, action_dim, tokenizer, resolution=1000):
        if tokenizer is None:
            raise ValueError('The digits codec writes text: pass the LM tokenizer')
        self.chunk, self.action_dim, self.resolution = chunk, action_dim, resolution
        self.tokenizer = tokenizer
        self.fixed_length = None
        sample = ' '.join(str(n) for n in range(resolution + 1))
        ids = set(tokenizer.encode(sample, add_special_tokens=False))
        for n in range(resolution + 1):
            ids |= set(tokenizer.encode(str(n), add_special_tokens=False))
        self.allowed = sorted(ids)
        self.index = {t: i for i, t in enumerate(self.allowed)}
        self.vocab = len(self.allowed)

    def text(self, actions):
        # round half to even (torch.round) in float64, as schema 1.1 states
        q = ((torch.as_tensor(actions).double().clamp(-1, 1) + 1) / 2 * self.resolution).round().long().reshape(len(actions), -1)
        return [' '.join(str(v) for v in row) for row in q.tolist()]

    def parse(self, text):
        """text -> (actions [K, A], ok)."""
        n = self.chunk * self.action_dim
        strict = re.fullmatch(r'\d+( \d+)*', text.strip()) is not None
        values = [int(v) for v in re.findall(r'\d+', text)]
        ok = strict and len(values) == n and all(0 <= v <= self.resolution for v in values)
        values = (values + [self.resolution // 2] * n)[:n]
        x = torch.tensor(values, dtype=torch.float32).clamp(0, self.resolution) / self.resolution * 2 - 1
        return x.reshape(self.chunk, self.action_dim), ok

    def encode(self, actions):
        out = []
        for t in self.text(actions):
            ids = self.tokenizer.encode(t, add_special_tokens=False)
            missing = [i for i in ids if i not in self.index]
            if missing:
                raise ValueError(f'The tokenizer wrote ids outside the digits alphabet: {missing[:5]}')
            out.append([self.index[i] for i in ids])
        return out

    def decode(self, seqs):
        rows, oks = [], []
        for s in seqs:
            text = self.tokenizer.decode([self.allowed[int(i)] for i in s])
            x, ok = self.parse(text)
            rows.append(x)
            oks.append(ok)
        return torch.stack(rows), torch.tensor(oks, dtype=torch.bool)

    def error_bound(self):
        return 1.0 / self.resolution
