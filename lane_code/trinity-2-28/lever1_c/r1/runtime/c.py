"""Prepare bounded durable scheduler output before submission."""
import fcntl
import os
from pathlib import Path
import stat
import subprocess

CAP=524288


def submit(root, argv, **kwargs):
    root=Path(root)
    if kwargs.get('input')!=(root.parent/'BATCH.sh').read_bytes():raise ValueError('E84')
    with (root/'28').open('ab') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for name in ('19','24','21'):
            fd=os.open(root/name,os.O_WRONLY|os.O_CREAT|os.O_APPEND|os.O_NOFOLLOW|os.O_NONBLOCK,0o600)
            try:
                info=os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_size>=CAP:raise ValueError('E76')
                os.fsync(fd)
            finally:os.close(fd)
        return subprocess.run(argv,**kwargs)
