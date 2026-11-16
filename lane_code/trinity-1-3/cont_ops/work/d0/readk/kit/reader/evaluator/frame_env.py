"""Stage the authenticated trainer environment once in the job-local directory."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from evalpath.items import sha256

ARCHIVE='/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/bdad3598/k/venv_rwtrain_torch211_cu129.tar'
SHA256='ffc81db4b3b1c3d1e42ac91159d504dc57b36eebfc75f537d15a426bbe6a8a22'


def unpack(archive,expected,dest):
    """Hash during a single archive read; execute nothing until the hash matches."""
    dest=Path(dest);dest.mkdir()
    proc=subprocess.Popen(['tar','-xf','-','-C',str(dest),'--no-same-owner'],stdin=subprocess.PIPE)
    h=hashlib.sha256()
    try:
        with Path(archive).open('rb') as stream:
            for block in iter(lambda:stream.read(16<<20),b''):
                h.update(block);proc.stdin.write(block)
    finally:
        proc.stdin.close()
        status=proc.wait()
    if status or h.hexdigest()!=expected:raise ValueError('Frame environment pin/extraction differs')
    venv=dest/'rwtrain_torch211_cu129'
    if not (venv/'lib/python3.12/site-packages').is_dir():raise ValueError('Require trainer Python 3.12 environment')
    if not (venv/'bin/python3').is_file():raise ValueError('Missing trainer interpreter')
    target=('#!'+str(venv/'bin/python3')).encode()
    pattern=re.compile(rb'#!/project/community/jjyeung/[^/\s]+/venvs/rwtrain_torch211_cu129/bin/python[0-9.]*')
    for path in (venv/'bin').iterdir():
        if path.is_symlink() or not path.is_file():continue
        with path.open('rb') as stream:first=stream.readline(4096)
        if pattern.fullmatch(first.rstrip()):
            raw=path.read_bytes();_,sep,rest=raw.partition(b'\n')
            mode=path.stat().st_mode
            path.chmod(mode|0o200)
            path.write_bytes(target+sep+rest)
            path.chmod(mode)
    return venv/'bin/python3'


def prepare_frames(config,work):
    work=Path(work)
    local=os.environ.get('EVALX_FRAME_PY')
    interpreter=Path(local) if local else unpack(ARCHIVE,SHA256,work/'e')
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
             OPENBLAS_NUM_THREADS='1',PYTHONNOUSERSITE='1')
    env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
    with (work/'2.log').open('ab') as log:
        subprocess.run([str(interpreter),'-B',str(Path(__file__).with_name('frame_stage.py')),
                        str(config),str(work/'f')],env=env,stdout=log,stderr=log,check=True)
    index=json.loads((work/'f/0.json').read_text())
    cfg=json.loads(Path(config).read_text())
    if index['binding']!=cfg['binding'] or index['source_sha256']!=cfg['source_sha256']:
        raise ValueError('Frame stage binding differs')
    return sha256(work/'f/0.json')
