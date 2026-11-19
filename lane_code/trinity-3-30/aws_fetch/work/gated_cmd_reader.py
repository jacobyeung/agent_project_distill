"""Gated reader: stop self before payload; on CONT run argv[1:] as a child and copy its stdout to ours (no exec)."""
import os, signal, subprocess, sys
os.kill(os.getpid(), signal.SIGSTOP)
p = subprocess.Popen(sys.argv[1:], stdout=subprocess.PIPE, bufsize=0)
out = sys.stdout.buffer
while True:
    b = p.stdout.read(65536)
    if not b:
        break
    out.write(b); out.flush()
sys.exit(p.wait())
