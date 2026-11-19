"""Bounded, nonrecursive kernel-cache inventory; no file-content reads."""
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kit_profile'))
from privacy import opaque, write_json


def snapshot():
    output = {}
    for key in ('CUDA_CACHE_PATH', 'TRITON_CACHE_DIR', 'TORCHINDUCTOR_CACHE_DIR'):
        value = os.environ.get(key)
        if not value:
            raise ValueError('Set ' + key + ' to a production-equivalent scratch cache')
        path = Path(value)
        entries = []
        if path.exists():
            with os.scandir(path) as scan:
                for item in scan:
                    if len(entries) == 4096:
                        break
                    stat = item.stat(follow_symlinks=False)
                    entries.append((opaque(item.name),stat.st_size,stat.st_mtime_ns,item.is_dir(follow_symlinks=False)))
        output[key] = dict(path_sha256=opaque(value), exists=path.exists(),
                           entries=sorted(entries), truncated=len(entries)==4096, recursive=False)
    return output


if __name__ == '__main__':
    write_json(Path(sys.argv[1]), snapshot())
