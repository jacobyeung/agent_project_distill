"""DCT action tokens: `DCTCodec` (quantised DCT, fixed length) and `FastCodec` (FAST: DCT + BPE).

DCT (design record 1.5): an orthonormal DCT-II along time per action dimension, the first `keep`
coefficients, scaled by `scale`, rounded and clipped to [-clip, clip]; integers are laid out
frequency-major (every dimension's lowest frequency first). Round trip with keep = K and no
clipping: max-abs error <= sqrt(K) * 0.5 / scale.

FAST adds byte-pair encoding over that integer stream (HF `tokenizers`, already a transformers
dependency): each integer becomes one character, BPE merges frequent runs up to `vocab` symbols,
and decoding expands symbols back to integers. Fit the BPE on the training subset's normalised
chunks only (`FastCodec.fit`), save it with `save(path)` (JSON + sha256) and load it at evaluation.
A decoded stream with the wrong number of integers is padded with zeros or truncated and flagged
not ok, as FAST's own decoder does.
"""
import hashlib
import json
import math
from pathlib import Path

import torch

BASE_CHAR = 0x4E00  # a contiguous block of single-codepoint characters, one per integer


def dct_matrix(n, dtype=torch.float32):
    """Orthonormal DCT-II matrix M [n, n]: coefficients = M @ signal, signal = M.T @ coefficients."""
    k = torch.arange(n, dtype=torch.float64)[:, None]
    i = torch.arange(n, dtype=torch.float64)[None]
    m = torch.cos(math.pi / n * (i + 0.5) * k) * math.sqrt(2.0 / n)
    m[0] /= math.sqrt(2.0)
    return m.to(dtype)


class DCTCodec:
    name = 'dct'

    def __init__(self, chunk, action_dim, keep=0, scale=10.0, clip=127):
        self.chunk, self.action_dim = chunk, action_dim
        self.keep, self.scale, self.clip = keep or chunk, float(scale), int(clip)
        self.vocab = 2 * self.clip + 1
        self.n_ints = self.keep * action_dim
        self.fixed_length = self.n_ints
        self.m = dct_matrix(chunk, torch.float64)

    def ints(self, actions):
        """[B, K, A] -> integer coefficients [B, keep * A] in [-clip, clip]."""
        c = torch.einsum('fk,bka->bfa', self.m, actions.double().cpu())[:, :self.keep]
        return (c * self.scale).round().clamp(-self.clip, self.clip).long().reshape(len(actions), -1)

    def from_ints(self, ints):
        """list of integer lists -> (actions [B, K, A] float32, ok [B])."""
        out = torch.zeros(len(ints), self.n_ints, dtype=torch.float64)
        ok = torch.zeros(len(ints), dtype=torch.bool)
        for i, s in enumerate(ints):
            s = list(s)[:self.n_ints]
            ok[i] = len(s) == self.n_ints
            out[i, :len(s)] = torch.tensor(s, dtype=torch.float64)
        coeff = (out.reshape(len(ints), self.keep, self.action_dim) / self.scale)
        coeff = torch.cat([coeff, coeff.new_zeros(len(ints), self.chunk - self.keep, self.action_dim)], 1)
        return torch.einsum('fk,bfa->bka', self.m, coeff).float(), ok

    def encode(self, actions):
        return (self.ints(actions) + self.clip).tolist()

    def decode(self, seqs):
        return self.from_ints([[t - self.clip for t in s] for s in seqs])

    def error_bound(self):
        """With keep = K and no clipping: an orthonormal inverse maps a coefficient error of max-abs
        0.5 / scale to max-abs <= sqrt(K) * 0.5 / scale per element."""
        return math.sqrt(self.keep) * 0.5 / self.scale


class FastCodec(DCTCodec):
    name = 'fast'

    def __init__(self, chunk, action_dim, vocab=1024, keep=0, scale=10.0, clip=127, path=''):
        super().__init__(chunk, action_dim, keep, scale, clip)
        self.vocab = int(vocab)
        self.fixed_length = None
        self.bpe = None
        self.sha256 = None
        if vocab < 2 * self.clip + 1:
            raise ValueError('FAST vocab must hold every base integer symbol (2 clip + 1)')
        if path:
            self.load(path)

    @staticmethod
    def _chars(ints):
        return ''.join(chr(BASE_CHAR + int(v)) for v in ints)

    def fit(self, actions, min_frequency=2):
        """Fit the BPE on normalised chunks [N, K, A] (the training subset only)."""
        from tokenizers import Tokenizer, models, trainers
        alphabet = [chr(BASE_CHAR + i) for i in range(2 * self.clip + 1)]
        tok = Tokenizer(models.BPE())
        trainer = trainers.BpeTrainer(vocab_size=self.vocab, initial_alphabet=alphabet, special_tokens=[],
                                      min_frequency=min_frequency, show_progress=False, limit_alphabet=len(alphabet))
        corpus = [self._chars(row) for row in (self.ints(actions) + self.clip).tolist()]
        tok.train_from_iterator(corpus, trainer)
        self._set(tok)
        return self

    def _set(self, tok):
        if tok.get_vocab_size() > self.vocab:
            raise ValueError('BPE vocabulary exceeds the configured FAST vocab')
        self.bpe = tok
        blob = tok.to_str()
        self.sha256 = hashlib.sha256(blob.encode()).hexdigest()
        self._id_to_str = {i: tok.id_to_token(i) for i in range(tok.get_vocab_size())}

    def save(self, path):
        meta = dict(kind='fast_bpe_v1', chunk=self.chunk, action_dim=self.action_dim, keep=self.keep,
                    scale=self.scale, clip=self.clip, vocab=self.vocab, bpe=json.loads(self.bpe.to_str()))
        Path(path).write_text(json.dumps(meta) + '\n')
        return self.sha256

    def load(self, path):
        from tokenizers import Tokenizer
        meta = json.loads(Path(path).read_text())
        mine = dict(chunk=self.chunk, action_dim=self.action_dim, keep=self.keep, scale=self.scale,
                    clip=self.clip, vocab=self.vocab)
        theirs = {k: meta[k] for k in mine}
        if meta.get('kind') != 'fast_bpe_v1' or theirs != mine:
            raise ValueError(f'FAST codec file does not match the config: {theirs} vs {mine}')
        self._set(Tokenizer.from_str(json.dumps(meta['bpe'])))
        return self

    def encode(self, actions):
        if self.bpe is None:
            raise RuntimeError('FastCodec is not fitted: call fit(train_chunks) or pass tok_codec_path')
        rows = self.ints(actions) + self.clip
        return [self.bpe.encode(self._chars(r)).ids for r in rows.tolist()]

    def decode(self, seqs):
        ints = []
        for s in seqs:
            text = ''.join(self._id_to_str.get(int(t), '') for t in s)
            ints.append([ord(c) - BASE_CHAR - self.clip for c in text])
        return self.from_ints(ints)
