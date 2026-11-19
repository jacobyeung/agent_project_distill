"""Hash-pinned, GT-free per-clip scale from ttower's scales64 rule."""
import hashlib
from pathlib import Path

RULE_SHA256 = '460231adeda2b7ce4b8065f22df1556e0a00b31ca3e489d571a2d4c8b9b49d4e'
ESTIMATOR_SHA256 = 'cb8509d8c1c2625b8554770111df18e1077f2094beda45dce01ec7c375685830'


def estimate_scale(depth, confidence, own_depth):
    root = Path(__file__).parent
    for name, expected in (('tower_scale_rule.json', RULE_SHA256),
                           ('tower_scale_rule.py', ESTIMATOR_SHA256)):
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen tower scale hash differs: ' + name)
    from .tower_scale_rule import estimate
    return estimate(depth, confidence, own_depth)
