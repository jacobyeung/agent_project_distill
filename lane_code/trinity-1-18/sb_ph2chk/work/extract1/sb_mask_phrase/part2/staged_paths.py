"""Resolve frozen absolute input names within the staged payload, without fallback."""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]


def local(path):
    path = Path(path)
    if os.environ.get('PART2_STAGED') == '1' and not path.is_relative_to(ROOT):
        return ROOT/'payload/files'/str(path).lstrip('/')
    return path
