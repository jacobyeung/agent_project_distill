"""T2 reader: stop before any payload IO, then write one tar stream of the listed /data2 files to stdout.
No exec, no children, no retry. usage: t2_reader.py LIST (paths relative to /)"""
import os, signal, sys, tarfile
names = [l.strip() for l in open(sys.argv[1]) if l.strip()]
os.kill(os.getpid(), signal.SIGSTOP)
with tarfile.open(fileobj=sys.stdout.buffer, mode='w|', format=tarfile.PAX_FORMAT) as t:
    for n in names:
        t.add('/' + n, arcname=n, recursive=False)
