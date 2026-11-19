"""Bars-first checks for scoring and launch (RULING 1135Z item 4).
The registered freeze keeps its original bytes; BARS_AMENDMENT.json records the
empty-mask and population semantics without changing any numerical bar.
This module uses only the standard library and never writes a file.
"""
import hashlib
from pathlib import Path
import sys

FROZEN_SHA256 = 'edff8724b27328f6874b4adb0dd93727cc70fdfd4ddf2fb301cf572a46ceaaf4'


def check(bars_dir, output_dirs=(), *, capture_scores=False):
    """Refuse before any output or scoring work. Return the verified input pin.

    PER_ITEM score exports are forbidden in every output directory. Pricing also
    refuses existing per-capture .json.gz files in its destination. Summary input
    prices and resumable tracker masks are inputs, not summary output files.
    """
    frozen = Path(bars_dir)/'BARS_FROZEN.json'
    try:
        actual = hashlib.sha256(frozen.read_bytes()).hexdigest()
    except OSError as exc:
        raise SystemExit(f'BARS_FIRST: missing or unreadable {frozen}: {exc}') from exc
    if actual != FROZEN_SHA256:
        raise SystemExit(f'BARS_FIRST: sha256 mismatch for {frozen}: {actual}; expected {FROZEN_SHA256}')
    for directory in output_dirs:
        directory = Path(directory)
        if not directory.exists():
            continue
        for p in sorted(directory.iterdir()):
            name = p.name.lower()
            per_item = name.startswith(('per_item', 'per-item')) and ('.json' in name or '.csv' in name or '.parquet' in name)
            if per_item or (capture_scores and name.endswith('.json.gz')):
                raise SystemExit(f'BARS_FIRST: per-item score file already exists: {p}; use a fresh output directory')
    return {str(frozen): actual}


if __name__ == '__main__':
    check(sys.argv[1], sys.argv[2:])
