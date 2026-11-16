"""Small file/path interface for the pinned optional family bridge."""
import hashlib
import json
from pathlib import Path

SJ = Path('/scratch/jjyeung')
AP = Path('/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap')


def load(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n')
