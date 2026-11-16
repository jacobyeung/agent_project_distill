"""Training dropout and the evaluation-only conditions of schema 5.5. All act on provider outputs, never on its inputs.

- Dropout: chunk (episode, t) is withheld iff int(sha256(f"{seed}:{episode}:{t}").hexdigest()[:8], 16) / 16**8 < 0.2,
  seed 17. A withheld chunk zeroes both vectors, sets where_mask False and prints `withheld` for every entity (the
  phrases stay). The trainer applies it; the cache stores the unwithheld output.
- withheld: every chunk withheld (the phrase-only condition).
- shuffled: the record of chunk k in episode (task, init i) is replaced, in both channels, by the record logged at chunk
  k of the U1 primary evaluation of (task, init (i + 1) mod 50), or by that episode's last record when it ended earlier.
- scale_k (0.8, 1.25): cols 6-14 and the printed cam, reach and size multiplied by k; uv stays.
- gt_where: the same provider code with GT inputs (build.build_provider('gt_where', ...)), flag proprio_handeye.
"""
import copy
import hashlib

import numpy as np

from .pline import format_line
from .types import WhereOutput

SEED = 17
RATE = 0.2


def draw(episode, t, seed=SEED):
    return int(hashlib.sha256(f'{seed}:{episode}:{t}'.encode()).hexdigest()[:8], 16) / 16 ** 8


def is_withheld(episode, t, seed=SEED, rate=RATE):
    return draw(episode, t, seed) < rate


def _copy(output):
    return WhereOutput.from_dict(copy.deepcopy(output.to_dict()))


def withhold(output):
    out = _copy(output)
    for e in out.entities:
        e.withheld = True
    out.line = format_line(out.entities)
    out.meta['condition'] = 'withheld'
    return out


def training_view(output, episode, t, seed=SEED, rate=RATE):
    return withhold(output) if is_withheld(episode, t, seed, rate) else output


def scale_k(output, k):
    out = _copy(output)
    for e in out.entities:
        if e.metric:
            e.X_wrist, e.reach_base, e.size = ([float(k) * v for v in getattr(e, f)]
                                               for f in ('X_wrist', 'reach_base', 'size'))
    out.line = format_line(out.entities)
    out.meta['condition'] = f'scale_{k}'
    return out


def shuffled(log, task, init, k, n_init=50):
    """log: {(task, init): [WhereOutput per chunk]} from the U1 primary evaluation. The donor's record at chunk k."""
    donor = log[(task, (init + 1) % n_init)]
    out = _copy(donor[min(k, len(donor) - 1)])
    out.meta['condition'] = 'shuffled'
    out.meta['donor'] = [task, (init + 1) % n_init, min(k, len(donor) - 1)]
    return out


def batch(outputs, withheld=None):
    """Stack outputs into the head's `where` [B, 2, 18] float32 and `where_mask` [B, 2] bool (schema 1, 3)."""
    where = np.stack([o.vector() for o in outputs])
    mask = np.stack([o.mask() for o in outputs])
    if withheld is not None:
        w = np.asarray(withheld, dtype=bool)
        where[w], mask[w] = 0.0, False
    return where, mask
