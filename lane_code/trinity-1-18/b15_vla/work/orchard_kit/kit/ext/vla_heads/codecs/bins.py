"""Uniform bins (RT-2 / OpenVLA): each of the K * A normalised values goes to one of `bins` uniform
bins over [-1, 1], time-major (step 0's A values first). Decoding returns bin centres, so
|error| <= 1 / bins. Fixed length K * A, no end token."""
import torch


class UniformBins:
    name = 'bins'

    def __init__(self, chunk, action_dim, bins=256):
        self.chunk, self.action_dim, self.vocab = chunk, action_dim, bins
        self.fixed_length = chunk * action_dim

    def encode(self, actions):
        x = actions.float().clamp(-1, 1)
        return ((x + 1) / 2 * self.vocab).floor().clamp(0, self.vocab - 1).long().reshape(len(x), -1).tolist()

    def decode(self, seqs):
        out = torch.zeros(len(seqs), self.chunk * self.action_dim)
        ok = torch.zeros(len(seqs), dtype=torch.bool)
        for i, s in enumerate(seqs):
            s = list(s)[:self.fixed_length]
            ok[i] = len(s) == self.fixed_length
            s = s + [self.vocab // 2] * (self.fixed_length - len(s))
            out[i] = (torch.tensor(s, dtype=torch.float32) + 0.5) / self.vocab * 2 - 1
        return out.reshape(len(seqs), self.chunk, self.action_dim), ok

    def step_of_token(self):
        """Chunk step that each token position encodes (for masking padded steps)."""
        return torch.arange(self.fixed_length) // self.action_dim

    def error_bound(self):
        return 1.0 / self.vocab
