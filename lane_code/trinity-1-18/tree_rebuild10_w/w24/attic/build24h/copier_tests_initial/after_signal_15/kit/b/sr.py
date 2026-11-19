"""Signal only worker descendants of the batch workload, then await its exit."""
import os
from pathlib import Path
import signal
import sys
import time


def children(pid):
    try:
        return [int(v) for v in Path('/proc',str(pid),'task',str(pid),'children').read_text().split()]
    except (OSError,ValueError):
        return []


def descendants(pid):
    result=[];pending=[pid]
    while pending:
        parent=pending.pop()
        for child in children(parent):
            result.append(child);pending.append(child)
    return result


def alive(pid):
    try:
        return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[0] != 'Z'
    except OSError:
        return False


def forward(pid):
    sent=[]
    for child in descendants(pid):
        try:
            args=Path('/proc',str(child),'cmdline').read_bytes().split(b'\0')
            env=Path('/proc',str(child),'environ').read_bytes().split(b'\0')
            # Elastic's agent has no worker RANK and must never receive SIGUSR1.
            if any(v.endswith(b'/b/u.py') for v in args) and any(v.startswith(b'RANK=') for v in env) and any(v.startswith(b'LOCAL_RANK=') for v in env):
                os.kill(child,signal.SIGUSR1);sent.append(child)
        except (OSError,ProcessLookupError):
            continue
    return sent


def main():
    pid=int(sys.argv[1]);bound=int(sys.argv[2]);deadline=time.monotonic()+bound
    if len(sys.argv)>3:
        forward(pid)
    while alive(pid):
        if time.monotonic()>=deadline:
            print('R1_COPY_WORK_WAIT_TIMEOUT',flush=True)
            return 124
        time.sleep(.1)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
