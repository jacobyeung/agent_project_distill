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


def forward(pid, sent):
    newly=[]
    for child in descendants(pid):
        try:
            if child in sent:continue
            status=Path('/proc',str(child),'status').read_text()
            caught=next(line.split()[1] for line in status.splitlines() if line.startswith('SigCgt:'))
            if not int(caught,16) & (1 << (signal.SIGUSR1-1)):continue
            args=Path('/proc',str(child),'cmdline').read_bytes().split(b'\0')
            env=Path('/proc',str(child),'environ').read_bytes().split(b'\0')
            # Elastic's agent has no worker RANK and must never receive SIGUSR1.
            if any(v.endswith(b'/b/rv.py') for v in args):
                os.kill(child,signal.SIGUSR1);newly.append(child)
            elif any(v.endswith(b'/b/u.py') for v in args) and any(v.startswith(b'RANK=') for v in env) and any(v.startswith(b'LOCAL_RANK=') for v in env):
                os.kill(child,signal.SIGUSR1);newly.append(child)
        except (OSError,ProcessLookupError):
            continue
    return newly


def main():
    pid=int(sys.argv[1]);bound=int(sys.argv[2]);deadline=time.monotonic()+bound
    sent=set()
    while alive(pid):
        if len(sys.argv)>3:sent.update(forward(pid,sent))
        if time.monotonic()>=deadline:
            print('R1_COPY_WORK_WAIT_TIMEOUT',flush=True)
            return 124
        time.sleep(.1)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
