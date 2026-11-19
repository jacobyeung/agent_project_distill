"""One stop-file contract across wrappers and optimizer step boundaries."""
import os
from pathlib import Path


def requested(signal_requested, cfg, step):
    limit = cfg.get('stop_after_step')
    if limit is not None and (type(limit) is not int or limit <= 0):
        raise ValueError('stop_after_step must be a positive integer')
    paths = {os.environ[k] for k in ('K3', 'R1_STOP_FILE') if os.environ.get(k)}
    return bool(signal_requested or any(Path(p).is_file() for p in paths)
                or (limit is not None and step >= limit))
