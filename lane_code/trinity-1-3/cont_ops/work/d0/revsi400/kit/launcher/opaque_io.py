"""Preserve diagnostics as hex without exposing their text in job logs."""
import os
import sys
import threading
from contextlib import contextmanager


def encode(source, destination):
    while True:
        chunk=source.read(4096)
        if not chunk:break
        destination.write(chunk.hex().encode()+b'\n')
        destination.flush()


def install():
    """Capture native writes and inherited child descriptors as well as Python output."""
    sys.stdout.flush();sys.stderr.flush()
    workers=[]
    for descriptor in (1,2):
        restore_fd=os.dup(descriptor)
        saved=os.dup(descriptor)
        reader,writer=os.pipe()
        os.dup2(writer,descriptor);os.close(writer)
        source=os.fdopen(reader,'rb',buffering=0)
        output=os.fdopen(saved,'wb',buffering=0)
        def pump(source=source,output=output):
            with source,output:encode(source,output)
        worker=threading.Thread(target=pump,daemon=True);worker.start();workers.append((descriptor,restore_fd,worker))
    return workers


@contextmanager
def redirect():
    workers=install()
    try:yield
    finally:
        sys.stdout.flush();sys.stderr.flush()
        for descriptor,restore_fd,worker in workers:
            os.dup2(restore_fd,descriptor);os.close(restore_fd)
        for descriptor,restore_fd,worker in workers:worker.join(timeout=5)
