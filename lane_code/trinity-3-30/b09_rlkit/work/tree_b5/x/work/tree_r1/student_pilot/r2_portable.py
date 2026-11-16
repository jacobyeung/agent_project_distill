"""Resolve immutable metadata pins relative to a verified portable closure."""
from pathlib import Path
from .p3_provenance import pinned


def bound(pin, root=None):
    if root is None:
        return pinned(pin)
    root = Path(root).resolve()
    path = root / pin['path']
    if path.is_symlink() or not path.resolve().is_relative_to(root):
        raise ValueError('Bound record escaped the kit')
    return pinned(dict(path=str(path.resolve()), sha256=pin['sha256']))
