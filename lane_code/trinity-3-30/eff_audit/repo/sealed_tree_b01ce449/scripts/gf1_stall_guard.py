"""Run one child group, retain its log, and stop it on log inactivity; never retry."""
import argparse
import os
from pathlib import Path
import signal
import subprocess
import time


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log',required=True);parser.add_argument('--stall-seconds',type=float,default=900)
    parser.add_argument('--startup-seconds',type=float,default=3600)
    parser.add_argument('--poll-seconds',type=float,default=60)
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args();command=args.command
    if command and command[0]=='--':command=command[1:]
    if not command or min(args.stall_seconds,args.startup_seconds,args.poll_seconds)<=0:
        parser.error('A command and positive timeouts are required')
    log=Path(args.log);log.parent.mkdir(parents=True,exist_ok=True)
    started=last=time.monotonic();size=0;child=None
    with log.open('xb',buffering=0) as output:
        child=subprocess.Popen(command,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
        def stop(signum,frame):
            if child.poll() is None:os.killpg(child.pid,signum)
        signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
        while child.poll() is None:
            time.sleep(min(60,args.poll_seconds))
            now=time.monotonic();current=log.stat().st_size
            if current!=size:size=current;last=now
            deadline=args.startup_seconds if now-started<args.startup_seconds else args.stall_seconds
            if now-last>deadline and child.poll() is None:
                output.write(b'\nGF1_STALL: log stopped advancing; terminating this launcher group; no automatic retry.\n')
                os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid,signal.SIGKILL);child.wait()
                return 124
    return child.returncode
if __name__=='__main__':raise SystemExit(main())
