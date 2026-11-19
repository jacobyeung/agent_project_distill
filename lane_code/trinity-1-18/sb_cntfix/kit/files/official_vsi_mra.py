"""Pinned verbatim function from N evalpath/official.py; see MRA_SOURCE.json."""
import math
from typing import Optional

def official_mra(
    pred: Optional[float],
    target: Optional[float],
    start: float = 0.5,
    end: float = 0.95,
    interval: float = 0.05,
) -> float:
    if pred is None or target is None or not math.isfinite(pred) or not math.isfinite(target):
        return 0.0
    if target == 0.0:
        return 1.0 if pred == 0.0 else 0.0
    num_pts = int((end - start) / interval + 2)
    conf_intervs = [start + i * (end - start) / (num_pts - 1) for i in range(num_pts)]
    rel_err = abs(pred - target) / abs(target)
    hits = [1.0 if rel_err <= (1.0 - c) else 0.0 for c in conf_intervs]
    return sum(hits) / len(hits)
