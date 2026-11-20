"""Reserve cumulative package metadata writes before forwarding each write."""
import builtins
import fcntl
import io
import os

LIMIT=2_000_000
TOKEN='TOKEN_VALUE'
PREFIX='/project/community/jjyeung/'+TOKEN+'/'
_original=builtins.open


def charge(size):
    # Fixed-width accounting includes its own writes; failed writes stay charged.
    with _original(os.open(PREFIX+'a/18',os.O_RDWR|os.O_CREAT,0o600), 'r+b', buffering=0) as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        lock.seek(0); raw=lock.read(32);used=int(raw or b'0')
        cost=size+32
        if used+cost>LIMIT:raise OSError('E70')
        lock.seek(0);lock.write(('%032d'%(used+cost)).encode());os.fsync(lock.fileno())


class Writer:
    def __init__(self,stream):self.stream=stream
    def write(self,data):
        charge(len(data.encode(self.stream.encoding or 'utf-8')) if isinstance(data,str) else len(data))
        return self.stream.write(data)
    def writelines(self,lines):
        for line in lines:self.write(line)
    def __getattr__(self,name):return getattr(self.stream,name)
    def __enter__(self):return self
    def __exit__(self,*args):return self.stream.__exit__(*args)


def install():
    if getattr(builtins.open,'_a18',False):return
    io_open=io.open
    def wrap(original):
        def opened(file,mode='r',*args,**kwargs):
            path=os.path.abspath(os.fspath(file)) if not isinstance(file,int) else ''
            watched=path.startswith(PREFIX) and not path.startswith(PREFIX+'a/f/') and any(x in mode for x in 'wax+')
            if watched:charge(0)
            stream=original(file,mode,*args,**kwargs)
            return Writer(stream) if watched else stream
        opened._a18=True
        return opened
    builtins.open=wrap(_original);io.open=wrap(io_open)
