"""Governed file reader: stop before any payload IO, then stream FILE to fd 1 (the pipe into ratelimit.py). usage: file_reader.py FILE"""
import os, signal, shutil, sys
os.kill(os.getpid(), signal.SIGSTOP)
with open(sys.argv[1], 'rb') as f, os.fdopen(1, 'wb', closefd=False) as o:
    shutil.copyfileobj(f, o, 1 << 20)
