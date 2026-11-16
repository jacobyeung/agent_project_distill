"""Interrupt only this build's invalid package test and its controller."""
import os
from pathlib import Path
import signal
L=Path(__file__).resolve().parents[2]
targets=[]
for p in Path('/proc').iterdir():
    if not p.name.isdigit():continue
    try:args=(p/'cmdline').read_bytes().split(b'\0')
    except (FileNotFoundError,PermissionError,ProcessLookupError):continue
    if any(arg in (b'work/build5/package.py',str(L/'work/tmp/package/work/build5/test_runner.py').encode()) for arg in args):
        if int(p.name)!=os.getpid():targets.append(int(p.name))
for pid in targets:
    try:os.kill(pid,signal.SIGINT)
    except ProcessLookupError:pass
print(targets)
