"""One allocation clock for work and all return channels."""
from contextlib import contextmanager
import signal
import subprocess
import time

WORK_RESERVE=240
RECEIPT_RESERVE=90
FINAL_RESERVE=10


def remaining(end, cap, clock=time.time):
    value=min(float(cap),end-clock())
    if value<=0:raise TimeoutError('E31')
    return value


@contextmanager
def window(end, results=None, clock=time.time):
    """Cap each transfer and interrupt local preparation at the same deadline."""
    original_run=subprocess.run
    old_pool=results.pool_operation if results is not None else None
    def run(*a,**kw):
        kw['timeout']=remaining(end,kw.get('timeout',1e9),clock)
        return original_run(*a,**kw)
    def pool(*a,**kw):
        kw['timeout']=remaining(end,kw.get('timeout',60),clock)
        return old_pool(*a,**kw)
    def expired(*args):raise TimeoutError('E32')
    handler=signal.getsignal(signal.SIGALRM)
    prior=signal.getitimer(signal.ITIMER_REAL)
    signal.signal(signal.SIGALRM,expired)
    subprocess.run=run
    if results is not None:results.pool_operation=pool
    try:
        signal.setitimer(signal.ITIMER_REAL,remaining(end,1e9,clock))
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,handler)
        if prior[0]:signal.setitimer(signal.ITIMER_REAL,*prior)
        subprocess.run=original_run
        if results is not None:results.pool_operation=old_pool


def finish(root,cfg,out,token,results,end,upload,write,failed,clock=time.time):
    """Return a bounded capture, then normal receipts, then a small fallback."""
    try:
        with window(end-RECEIPT_RESERVE,results,clock):upload(root,cfg,out,token,results)
    except Exception:
        write(out/'metadata/CAPTURE.json',dict(verified=False,error='E33'))
    if not (out/'metadata/PARITY.json').exists():
        write(out/'metadata/PARITY.json',dict(trusted=False,items=0,expected=60,failure='E34'))
    try:
        with window(end-FINAL_RESERVE,results,clock):
            returned=results.publish(out,cfg['pool'],token,cfg['plan_sha256'],1 if failed else 0)
            write(root/'RETURN.json',returned)
            if not returned.get('returned'):raise TimeoutError('E39')
    except Exception:
        write(out/'RETURN_RECEIPT.json',dict(returned=False,error='E35'))
        # Publish a small failure receipt even if normal packaging exhausted its window.
        local=root/'z';local.mkdir(exist_ok=True)
        write(local/'RETURN_RECEIPT.json',dict(returned=False,error='E35'))
        write(local/'JOB.log',dict(error='E35'))
        try:
            with window(end-2,results,clock):
                results.pool_operation('receipt',cfg['pool'],token,local,timeout=8)
        except Exception:pass
