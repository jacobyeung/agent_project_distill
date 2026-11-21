"""Drain output to fixed-cap opaque files, including scheduler output."""
import contextlib
import fcntl
import os
from pathlib import Path
import select
import stat
import subprocess
import sys
import threading

CAP=131072


class Sink:
    def __init__(self, path, marker):
        self.fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
        self.marker=marker
    def write(self, block):
        data=block.hex().encode()+b'\n'
        fcntl.flock(self.fd,fcntl.LOCK_EX)
        try:
            left=max(0,CAP-os.fstat(self.fd).st_size)
            if left:
                os.write(self.fd,data[:left]);os.fsync(self.fd)
            if len(data)>left:
                try:fd=os.open(self.marker,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                except FileExistsError:pass
                else:
                    os.write(fd,b'1\n');os.fsync(fd);os.close(fd)
        finally:fcntl.flock(self.fd,fcntl.LOCK_UN)
    def close(self):os.close(self.fd)


def stream(path, marker):
    sink=Sink(path,marker)
    try:
        while True:
            block=os.read(0,8192)
            if not block:break
            sink.write(block)
    finally:sink.close()


@contextlib.contextmanager
def scheduler(root):
    root=Path(root)
    with (root/'28').open('ab') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        fifo=root/'19'
        try:os.mkfifo(fifo,0o600)
        except FileExistsError:
            if not stat.S_ISFIFO(fifo.stat().st_mode):raise ValueError('E76')
        # Hold both ends until sbatch --wait returns, including all queue time.
        fd=os.open(fifo,os.O_RDWR|os.O_NONBLOCK)
        sink=Sink(root/'24',root/'25');done=threading.Event();errors=[]
        def drain():
            try:
                while True:
                    if select.select([fd],[],[],.05)[0]:
                        block=os.read(fd,8192)
                        if block:sink.write(block)
                    elif done.is_set():break
            except BaseException as error:errors.append(error)
        thread=threading.Thread(target=drain);thread.start()
        try:yield
        finally:
            done.set();thread.join();sink.close();os.close(fd)
            if errors:raise errors[0]


def submit(root, argv, **kwargs):
    if '--test-only' in argv:return subprocess.run(argv,**kwargs)
    with scheduler(root):
        return subprocess.run(argv+['--wait'],**kwargs)


if __name__=='__main__':stream(sys.argv[1],sys.argv[2])
