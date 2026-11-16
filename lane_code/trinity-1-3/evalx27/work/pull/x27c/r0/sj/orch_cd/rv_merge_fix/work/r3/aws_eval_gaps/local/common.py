import hashlib
import io
import json
from pathlib import Path
import re
import tarfile

ROOT=Path(__file__).resolve().parents[1]
AWS='/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'
LEDGER='/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/aws_reserve/AWS_JOB_LEDGER.jsonl'


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def save(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,sort_keys=True,indent=1,allow_nan=False)+'\n')


def pin(value):
    path,sep,h=value.rpartition('@')
    if not sep or not path.startswith('/') or not re.fullmatch('[0-9a-f]{64}',h):
        raise ValueError('Require absolute-path@sha256')
    return dict(path=path,sha256=h)


def archive(path,blobs):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with tarfile.open(path,'w',format=tarfile.PAX_FORMAT) as tf:
        for name,raw in sorted(blobs.items()):
            member=tarfile.TarInfo(name)
            member.size,member.mode,member.mtime=len(raw),0o444,0
            tf.addfile(member,io.BytesIO(raw))
