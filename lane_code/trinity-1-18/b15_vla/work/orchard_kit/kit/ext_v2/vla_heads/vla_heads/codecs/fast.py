"""DCT action tokens: `DCTCodec` (quantised DCT, fixed length) and `FastCodec` (FAST: DCT + BPE).

DCT: an orthonormal DCT-II along time per action dimension, the first `keep` coefficients, scaled by
`scale`, rounded and clipped to [-clip, clip]; integers are laid out frequency-major (every
dimension's lowest frequency first). Round trip with keep = K and no clipping: max-abs error
<= sqrt(K) * 0.5 / scale.

FAST calls the reference implementation directly: `fast_reference.py` is physical-intelligence/fast
`processing_action_tokenizer.py` at revision ec4d7aa7 (FAST_REFERENCE), vendored byte for byte and
checked against REFERENCE_SHA256 at import. `FastCodec.fit` runs `UniversalActionProcessor.fit` on
the training subset's normalised chunks only (scale `tok_dct_scale`, vocabulary `tok_vocab`), encode
and decode call the processor, so the token stream is the reference's. `save(path)` writes the
fitted BPE with its min_token as JSON; `load` rebuilds the same processor. A token sequence whose
coefficients do not reshape to [K, A] decodes to zeros with ok False (the reference prints and
returns zeros there).
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


from ..config import FAST_REFERENCE_SHA256 as REFERENCE_SHA256
FAST_KIND = 'fast_reference_v1'


def _reference():
    path = Path(__file__).with_name('fast_reference.py')
    if hashlib.sha256(path.read_bytes()).hexdigest() != REFERENCE_SHA256:
        raise RuntimeError(f'{path} does not match the pinned FAST reference sha256')
    from . import fast_reference
    return fast_reference.UniversalActionProcessor


class FastCodec:
    name = 'fast'

    def __init__(self, chunk, action_dim, vocab=1024, scale=10.0, path=''):
        from ..config import FAST_REFERENCE
        self.chunk, self.action_dim, self.vocab, self.scale = chunk, action_dim, int(vocab), float(scale)
        self.reference = FAST_REFERENCE
        self.fixed_length = None
        self.processor = None
        self.max_token = None
        self.sha256 = None
        if path:
            self.load(path)

    def fit(self, actions):
        """Fit the reference BPE on normalised chunks [N, K, A] (the training subset only)."""
        import contextlib
        import io
        import numpy as np
        data = [a for a in torch.as_tensor(actions).double().cpu().numpy()]
        with contextlib.redirect_stderr(io.StringIO()):
            proc = _reference().fit(data, scale=self.scale, vocab_size=self.vocab, time_horizon=self.chunk,
                                    action_dim=self.action_dim)
        self.max_token = int(max(np.around(self.integers(a[None])).max() for a in data))
        self._set(proc)
        return self

    def integers(self, actions):
        """FAST's integer stage, [B, K, A] -> [B, K * A] float64: np.around(scale * DCT-II_ortho over time),
        flattened frequency-major (the reference's own formula, before min_token and BPE)."""
        from scipy.fft import dct
        import numpy as np
        x = np.asarray(torch.as_tensor(actions).double().cpu().numpy())
        return np.around(dct(x, axis=1, norm='ortho') * self.scale).reshape(len(x), -1)

    def symbol_integers(self, seq):
        """BPE ids -> the integers they spell (inverse of the integer stage after min_token)."""
        proc = self._need()
        return [ord(c) + int(proc.min_token) for c in proc.bpe_tokenizer.decode([int(t) for t in seq])]

    def _set(self, proc):
        n = proc.bpe_tokenizer.backend_tokenizer.get_vocab_size()
        if n > self.vocab:
            raise ValueError(f'The fitted BPE holds {n} symbols > tok_vocab={self.vocab}')
        self.processor = proc
        self.sha256 = hashlib.sha256((self._state() + '\n').encode()).hexdigest()  # = sha256 of the saved file

    def _state(self):
        p = self.processor
        return json.dumps(dict(kind=FAST_KIND, reference=self.reference, reference_sha256=REFERENCE_SHA256,
                               chunk=self.chunk, action_dim=self.action_dim, scale=self.scale, vocab=self.vocab,
                               min_token=int(p.min_token), max_token=self.max_token,
                               bpe=json.loads(p.bpe_tokenizer.backend_tokenizer.to_str())),
                          sort_keys=True)

    def save(self, path):
        Path(path).write_text(self._state() + '\n')
        return self.sha256

    def load(self, path):
        from tokenizers import Tokenizer
        from transformers import PreTrainedTokenizerFast
        meta = json.loads(Path(path).read_text())
        mine = dict(kind=FAST_KIND, reference_sha256=REFERENCE_SHA256, chunk=self.chunk, action_dim=self.action_dim,
                    scale=self.scale, vocab=self.vocab)
        theirs = {k: meta.get(k) for k in mine}
        if theirs != mine:
            raise ValueError(f'FAST codec file does not match the config: {theirs} vs {mine}')
        tok = PreTrainedTokenizerFast(tokenizer_object=Tokenizer.from_str(json.dumps(meta['bpe'])),
                                      clean_up_tokenization_spaces=False)
        self.max_token = meta.get('max_token')
        self._set(_reference()(tok, scale=self.scale, vocab_size=self.vocab, min_token=meta['min_token'],
                               time_horizon=self.chunk, action_dim=self.action_dim))
        return self

    def _need(self):
        if self.processor is None:
            raise RuntimeError('FastCodec is not fitted: call fit(train_chunks) or pass tok_codec_path')
        return self.processor

    def encode(self, actions):
        proc = self._need()
        return [list(map(int, t)) for t in proc(torch.as_tensor(actions).double().cpu().numpy())]

    def decode(self, seqs):
        """list of id lists -> (actions [B, K, A] float32, ok [B])."""
        import numpy as np
        proc = self._need()
        out = torch.zeros(len(seqs), self.chunk, self.action_dim)
        ok = torch.zeros(len(seqs), dtype=torch.bool)
        n = self.chunk * self.action_dim
        for i, s in enumerate(seqs):
            s = [int(t) for t in s]
            if not s or len(proc.bpe_tokenizer.decode(s)) != n:
                continue
            dec = proc.decode([s], time_horizon=self.chunk, action_dim=self.action_dim)
            out[i] = torch.as_tensor(np.asarray(dec[0]), dtype=torch.float32)
            ok[i] = True
        return out, ok

    def error_bound(self):
        """Inside the fitted coefficient range: max-abs <= sqrt(K) * 0.5 / scale per element."""
        return math.sqrt(self.chunk) * 0.5 / self.scale
