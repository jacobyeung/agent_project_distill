"""Gated tar reader: stop before payload IO, then stream a ustar/pax archive of a file list to stdout.

usage: gated_tar_reader.py LIST ROOT   (LIST: one path relative to ROOT per line)
Never execs, launches children or retries; the governor's node agent continues it.
"""
import os, signal, sys, tarfile
os.kill(os.getpid(), signal.SIGSTOP)
lst, root = sys.argv[1], sys.argv[2]
with tarfile.open(fileobj=sys.stdout.buffer, mode='w|', format=tarfile.PAX_FORMAT, bufsize=65536) as tf:
    for rel in (l.strip() for l in open(lst)):
        if rel:
            tf.add(os.path.join(root, rel), arcname=rel, recursive=False)
