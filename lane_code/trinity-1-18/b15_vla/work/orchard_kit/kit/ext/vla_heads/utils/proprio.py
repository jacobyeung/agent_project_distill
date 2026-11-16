"""Proprioception encoding (normalise with utils.norm.Normalizer first)."""
from torch import nn


class ProprioEncoder(nn.Module):
    """Normalised proprio [B, P] -> one token [B, 1, out_dim] (used when proprio_inject = lm)."""

    def __init__(self, proprio_dim, out_dim, hidden=256):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(proprio_dim, hidden), nn.GELU(), nn.Linear(hidden, out_dim))

    def forward(self, proprio):
        return self.net(proprio.to(self.net[0].weight.dtype))[:, None]
