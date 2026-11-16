"""Action chunking at episode ends, temporal ensembling and open-loop chunk execution."""
import torch


def make_chunks(actions, chunk):
    """One episode [T, A] -> (chunks [T, K, A], mask [T, K]): chunk t holds actions t..t+K-1. Steps past
    the episode end repeat the last action and are masked out (mask False)."""
    x = torch.as_tensor(actions)
    t = x.shape[0]
    idx = torch.arange(t)[:, None] + torch.arange(chunk)[None]
    mask = idx < t
    return x[idx.clamp(max=t - 1)], mask


class TemporalEnsembler:
    """ACT-style temporal ensembling for closed-loop evaluation.

    Call `update(chunk [K, A] or [B, K, A])` once per control step with the newest predicted chunk;
    it returns the action to execute now: a weighted mean of every stored chunk's prediction for
    the current step, weights exp(-m * i) with i = 0 for the oldest prediction (ACT, m = 0.01).
    `reset()` at each episode start.
    """

    def __init__(self, chunk, m=0.01):
        self.chunk, self.m = chunk, m
        self.reset()

    def reset(self):
        self.history = []  # (step issued, chunk)
        self.step = 0

    def update(self, chunk):
        chunk = torch.as_tensor(chunk)
        if chunk.shape[-2] != self.chunk:
            raise ValueError(f'chunk must have {self.chunk} steps')
        self.history = [(s, c) for s, c in self.history if self.step - s < self.chunk]
        self.history.append((self.step, chunk))
        preds = torch.stack([c[..., self.step - s, :] for s, c in self.history]).double()
        w = torch.exp(-self.m * torch.arange(len(preds), dtype=torch.float64))
        w = (w / w.sum()).reshape(-1, *([1] * (preds.ndim - 1)))
        self.step += 1
        return (preds * w).sum(0).to(chunk.dtype)


class ChunkExecutor:
    """Open-loop chunk execution: query the policy every `replan` steps and play its actions."""

    def __init__(self, replan):
        self.replan = replan
        self.reset()

    def reset(self):
        self.queue, self.step = None, 0

    def needs_query(self):
        return self.queue is None or self.step % self.replan == 0

    def update(self, chunk=None):
        if chunk is not None:
            self.queue, self.offset = torch.as_tensor(chunk), self.step
        if self.queue is None:
            raise ValueError('update(chunk) first')
        action = self.queue[..., self.step - self.offset, :]
        self.step += 1
        return action
