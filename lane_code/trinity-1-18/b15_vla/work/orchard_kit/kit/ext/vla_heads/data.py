"""A resumable sampler: a fresh seeded permutation every epoch and an exact position for resume.

Save `sampler.state_dict()` in `save_checkpoint(..., extra={'sampler': ...})` and restore it with
`load_state_dict`; the next index after a resume equals the next index of an uninterrupted run.
"""
import torch


class EpochSampler:
    def __init__(self, n, seed=0, rank=0, world_size=1):
        if n < world_size:
            raise ValueError('Fewer items than ranks')
        self.n, self.seed, self.rank, self.world = n, seed, rank, world_size
        self.epoch, self.pos = 0, 0

    def _order(self):
        g = torch.Generator().manual_seed(self.seed * 1_000_003 + self.epoch)
        order = torch.randperm(self.n, generator=g)
        per = self.n // self.world
        return order[self.rank * per:(self.rank + 1) * per]

    def next_indices(self, batch):
        """The next `batch` indices of this rank, rolling into a new permutation at epoch ends."""
        out = []
        while len(out) < batch:
            order = self._order()
            take = order[self.pos:self.pos + batch - len(out)].tolist()
            out += take
            self.pos += len(take)
            if self.pos >= len(order):
                self.epoch, self.pos = self.epoch + 1, 0
        return out

    def state_dict(self):
        return dict(n=self.n, seed=self.seed, rank=self.rank, world=self.world, epoch=self.epoch, pos=self.pos)

    def load_state_dict(self, state):
        if (state['n'], state['seed'], state['rank'], state['world']) != (self.n, self.seed, self.rank, self.world):
            raise ValueError('Sampler identity differs from the checkpoint')
        self.epoch, self.pos = state['epoch'], state['pos']
