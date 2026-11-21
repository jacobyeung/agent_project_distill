"""Drain output to fixed-cap opaque files, including scheduler output."""
import fcntl
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
import resource

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


def collector(root):
    # This process runs inside the allocation. FIFO peers must share a kernel;
    # a reader on the submission host cannot consume a compute node's FIFO.
    root=Path(root)
    resource.setrlimit(resource.RLIMIT_FSIZE,(524288,resource.getrlimit(resource.RLIMIT_FSIZE)[1]))
    sink=Sink(root/'24',root/'25')
    fd=os.open(root/'19',os.O_RDONLY)
    try:
        while True:
            block=os.read(fd,8192)
            if not block:break
            sink.write(block)
    finally:sink.close();os.close(fd)


def submit(root, argv, **kwargs):
    if '--test-only' in argv:return subprocess.run(argv,**kwargs)
    root=Path(root)
    with (root/'28').open('ab') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        fifo=root/'19'
        try:os.mkfifo(fifo,0o600)
        except FileExistsError:
            if not stat.S_ISFIFO(fifo.stat().st_mode):raise ValueError('E76')
        result=subprocess.run(argv,**kwargs)
        job=result.stdout.strip().split(b';')[0]
        if result.returncode or not job.isdigit():return result
        job=job.decode()
        while True:
            state=subprocess.run(['squeue','-h','-j',job,'-o','%T'],capture_output=True,env=kwargs.get('env'))
            if state.returncode:raise RuntimeError('E77')
            value=state.stdout.strip()
            if value in (b'RUNNING',b'COMPLETING'):break
            if value not in (b'PENDING',b'CONFIGURING'):raise RuntimeError('E78')
            # This waits for the one accepted allocation; it never resubmits.
            time.sleep(60)
        step=['srun','--jobid='+job,'--overlap','--exact','--nodes=1','--ntasks=1',
              '--cpus-per-task=1','--gres=none','--mem=0','--export=NONE','--chdir=/tmp',
              '/usr/bin/python3','-I','-s','-B',str(root/'27.py'),'fifo',str(root)]
        # srun carries its own control output to the submitter. Only the
        # compute-local reader consumes scheduler bytes and writes a/24.
        collected=subprocess.run(step,capture_output=True,env=kwargs.get('env'))
        if collected.returncode:
            result.stderr+=b'E79\n'+collected.stderr[:4096].hex().encode()+b'\n'
        return result


if __name__=='__main__':
    if sys.argv[1]=='fifo':collector(sys.argv[2])
    else:stream(sys.argv[1],sys.argv[2])
